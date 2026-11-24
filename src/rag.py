"""RAG pipeline: otázka -> hybridné vyhľadávanie -> prompt -> LLM.

Hybridné vyhľadávanie = 3 nezávislé poradia chunkov spojené cez Reciprocal Rank Fusion (RRF):
  1. vektorové (kosínusová podobnosť embeddingov, model bge-m3),
  2. BM25 (kľúčové slová, presné názvy výrobkov),
  3. ontologické (chunky, ktoré obsahujú pojmy z otázky alebo ich susedov v ontológii).
RRF skóre chunku = sum 1 / (RRF_K + poradie v zozname).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import numpy as np

from bm25 import BM25
from ingest import TABLE_PDF, LIST_PDF, tables_context
from config import CANDIDATES, EMBED_MODEL, INDEX_DIR, INDEX_ROOT, MIN_SIM, RRF_K, TOP_K
from llm import chat, embed
from ontology import Ontology, load_ontology

MAX_FACTS = 25          # max. počet faktov z ontológie v prompte
W_DIRECT, W_NEIGH = 1.0, 0.3  # váha pojmu priamo z otázky vs. suseda v ontológii
# Váha ontologického poradia v RRF. Meranie (eval/retrieval_eval.py, bge-m3, 13 otázok):
#   0.0 -> hit@4 13/13, MRR 0.96;  0.5 -> 12/13, 0.83;  1.0 -> 11/13, 0.79.
# Na aktuálnych 9 SK dokumentoch ontológia pri radení dokumentov škodí pri bge-m3 (100 % -> 85 %)
# aj pri nomic-embed-text (92 % -> 77 %) – všeobecné pojmy ako Cake posúvajú nesúvisiace chunky.
# (Pomáhala len na starej sade 10 dokumentov s nomic: 85 % -> 100 %.) Ontológia sa preto používa
# na fakty v prompte a na graf, nie na radenie dokumentov.
ONTO_RRF_WEIGHT = 0.0
# otázka na cenu alebo na ponuku ("Čo máte v ponuke?") -> do promptu cenník z ontológie
PRICE_RE = re.compile(r"\b(cen[aeuy]|stoj|stál|stoja|price|€|ponuk|ponúka|predávate|menu|sortiment)", re.I)
ALLERGEN_RE = re.compile(r"alerg", re.I)                                    # otázka na alergény
SEM_FACTS = 8          # koľko faktov z ontológie pridať podľa významovej podobnosti (bge-m3)
SEM_FACT_MIN = 0.45     # min. kosínusová podobnosť faktu s otázkou

SYSTEM_PROMPT = """Si asistent pre doménu cukráreň (cukrárske výrobky, suroviny, personál, objednávky).
Odpovedaj iba na základe poskytnutého kontextu: faktov z ontológie a úryvkov z dokumentov.
Fakty z ontológie opisujú NAŠU cukráreň (jej produkty, ceny, zamestnancov, objednávky).
Pravidlá:
- Ceny uvádzaj IBA z ontológie (zoznam "CENY NAŠEJ CUKRÁRNE"). Ceny z dokumentov nepoužívaj. Ak produkt v tomto zozname nie je, napíš: "Tento produkt v ponuke našej cukrárne nie je."
- Alergény uvádzaj IBA zo stĺpca ALERGÉNY v "TABUĽKA ALERGÉNOV". Suroviny zo stĺpca zloženie (vanilka, kakao, cukor ...) nie sú alergény.
- Nevymýšľaj. Ak odpoveď v kontexte nie je, napíš: "V dostupných dokumentoch to nie je uvedené."
- Ak dokument tému iba spomína (napr. ako otázku alebo názov), ale nepopisuje ju, nepovažuj to za odpoveď.
- Pri zložení výrobku vymenuj iba suroviny, ktoré sú pri ňom výslovne uvedené (hasIngredient alebo v úryvku), nie všeobecné zoznamy surovín.
- Pri tabuľkách (cenníky) čítaj stĺpce pozorne: hmotnosť je v gramoch (g), cena v eurách (€).
- Pri tvrdeniach z dokumentov uveď zdroj v tvare [súbor, s. X]; pri faktoch z ontológie napíš (ontológia).
- Odpovedaj stručne a celý v jazyku, v ktorom je položená otázka. Názvy z ontológie píš po slovensky (napr. "mliečny výrobok", nie "DairyProduct").
- Formát: NAJPRV priama odpoveď (1–4 vety alebo krátky zoznam) so zdrojmi. Potom samostatný riadok "---" a pod ním "Zdôvodnenie:" – 2–4 krátke body, z ktorých faktov a úryvkov si vychádzal."""


@dataclass
class Retrieved:
    text: str
    source: str
    page: int
    score: float                 # RRF skóre
    concepts: list[str]
    cosine: float = 0.0
    bm25: float = 0.0
    ranks: dict = field(default_factory=dict)  # poradie v jednotlivých zoznamoch (vektor/bm25/ontológia)


class RAG:
    def __init__(self):
        self.onto: Ontology = load_ontology()
        self.reload_index()
        self._fact_emb = None  # embeddingy faktov ontológie (vypočítajú sa pri 1. otázke, potom cache)
        self._sem_facts: list[str] = []

    # ------------------------------------------------------------------ fakty ontológie ako vektory
    def _ontology_fact_vectors(self):
        """Všetky fakty ontológie -> embeddingy (rovnaký model ako dokumenty), uložené do cache."""
        import hashlib
        facts = sorted({f for fs in self.onto.facts.values() for f in fs})
        key = hashlib.md5(("\n".join(facts) + self.embed_model).encode("utf-8")).hexdigest()[:12]
        cache = INDEX_ROOT / f"onto_facts_{self.embed_model.replace(':', '_')}_{key}.npy"
        if cache.exists():
            emb = np.load(cache)
        else:
            emb = np.array(embed(facts, model=self.embed_model), dtype=np.float32)
            emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.save(cache, emb)
        self._facts_list, self._fact_emb = facts, emb

    def reload_index(self, index_dir=INDEX_DIR):
        f_chunks, f_emb = index_dir / "chunks.json", index_dir / "embeddings.npy"
        meta_f = index_dir / "meta.json"
        self.meta = json.loads(meta_f.read_text(encoding="utf-8")) if meta_f.exists() else {}
        if f_chunks.exists() and f_emb.exists():
            self.chunks = json.loads(f_chunks.read_text(encoding="utf-8"))
            for c in self.chunks:  # pojmy podľa aktuálnej ontológie (lacné, regex) – bez preindexovania
                c["concepts"] = self.onto.find_concepts(c["text"])
            self.emb = np.load(f_emb)
        else:
            self.chunks, self.emb = [], np.zeros((0, 1), dtype=np.float32)
        self.embed_model = self.meta.get("embed_model", EMBED_MODEL)
        self.bm25 = BM25([c["text"] for c in self.chunks]) if self.chunks else None
        self._fact_emb = None  # iný index môže mať iný embedding model -> fakty prepočítať

    # ------------------------------------------------------------------ vyhľadávanie
    def retrieve(self, question: str, k: int = TOP_K, use_vector=True, use_bm25=True, use_onto=True,
                 onto_weight: float | None = None):
        q_concepts = self.onto.find_concepts(question)
        neigh = self.onto.neighbours(q_concepts, depth=1) - set(q_concepts)
        if not self.chunks:
            return q_concepts, []
        n = len(self.chunks)

        q = np.array(embed([question], model=self.embed_model)[0], dtype=np.float32)
        q /= np.linalg.norm(q) + 1e-9
        cos = self.emb @ q

        # fakty ontológie podobné otázke (BGE-M3) – dopĺňajú fakty nájdené cez kľúčové slová
        if self._fact_emb is None:
            self._ontology_fact_vectors()
        fsim = self._fact_emb @ q
        self._sem_facts = [self._facts_list[i] for i in np.argsort(-fsim)[:SEM_FACTS] if fsim[i] >= SEM_FACT_MIN]
        bm = np.array(self.bm25.scores(question))
        onto = np.array([W_DIRECT * len(set(q_concepts) & set(c["concepts"])) +
                         W_NEIGH * len(neigh & set(c["concepts"])) for c in self.chunks])

        rankings = {}
        if use_vector:
            rankings["vektor"] = np.argsort(-cos)[:CANDIDATES]
        if use_bm25:
            rankings["bm25"] = [i for i in np.argsort(-bm)[:CANDIDATES] if bm[i] > 0]
        w_onto = ONTO_RRF_WEIGHT if onto_weight is None else onto_weight
        if use_onto and q_concepts and w_onto > 0:
            rankings["ontológia"] = [i for i in np.argsort(-onto, kind="stable")[:CANDIDATES] if onto[i] > 0]

        rrf = np.zeros(n)
        ranks: dict[int, dict] = {}
        weights = {"vektor": 1.0, "bm25": 1.0, "ontológia": ONTO_RRF_WEIGHT if onto_weight is None else onto_weight}
        for name, order in rankings.items():
            for r, i in enumerate(order, start=1):
                rrf[i] += weights[name] / (RRF_K + r)
                ranks.setdefault(int(i), {})[name] = r

        # prah podobnosti: zahodiť chunky, ktoré sú vektorovo vzdialené a nemajú zhodu kľúčových slov
        rrf[(cos < MIN_SIM) & (bm == 0)] = 0
        top = [i for i in np.argsort(-rrf)[:k] if rrf[i] > 0]
        hits = [Retrieved(self.chunks[i]["text"], self.chunks[i]["source"], self.chunks[i]["page"],
                          float(rrf[i]), self.chunks[i]["concepts"], float(cos[i]), float(bm[i]),
                          ranks.get(int(i), {})) for i in top]
        return q_concepts, hits

    # ------------------------------------------------------------------ prompt
    def _hubs(self, q_concepts: list[str], min_children: int = 6) -> set[str]:
        """Všeobecné pojmy z otázky (veľa podtried), ak otázka obsahuje aj konkrétny pojem."""
        g = self.onto.graph
        hubs = {c for c in q_concepts if c in g and
                sum(d.get("kind") == "subclass" for _, _, d in g.in_edges(c, data=True)) >= min_children}
        return hubs if set(q_concepts) - hubs else set()

    def _hub_noise(self, q_concepts: list[str]) -> set[str]:
        """Fakty "X is a Surovina" pre všeobecné pojmy s mnohými podtriedami (Ingredient, Product ...).
        Otázka "Aké ingrediencie má tiramisu?" by inak dostala zoznam všetkých surovín a LLM ho
        považovalo za zloženie (napr. pridalo škrob). Vynechajú sa, ak otázka obsahuje aj konkrétny pojem."""
        g, sk = self.onto.graph, self.onto.labels_sk
        disp = lambda n: f"{n} ({sk[n]})" if n in sk else n
        hubs = self._hubs(q_concepts)
        return {f"{disp(s)} is a {disp(o)}." for o in hubs for s, _, d in g.in_edges(o, data=True)
                if d.get("kind") == "subclass" and s not in q_concepts}

    def _price_list(self) -> str:
        """Všetky produkty s cenou (hasPrice) v ontológii – iné produkty naša cukráreň nepredáva."""
        g, sk = self.onto.graph, self.onto.labels_sk
        rows = []
        for n, d in g.nodes(data=True):
            price = d.get("data", {}).get("hasPrice")
            if price is None:
                continue
            cls = [o for _, o, e in g.out_edges(n, data=True) if e.get("kind") == "instance"]
            name = sk.get(cls[0], cls[0]) if cls else d["data"].get("hasName", n)
            rows.append(f"- {name} ({n}): {float(price):.2f} €".replace(".", ","))
        return "CENY NAŠEJ CUKRÁRNE (ontológia) – iba tieto produkty máme v ponuke:\n" + "\n".join(rows)

    def build_messages(self, question: str, q_concepts: list[str], hits: list[Retrieved], history=None):
        # najprv fakty o pojmoch z otázky, potom o susedoch; max. MAX_FACTS riadkov
        # susedov berieme len od konkrétnych pojmov (Tiramisu), nie od všeobecných (Ingredient má desiatky podtried)
        hubs = self._hubs(q_concepts)
        base = [c for c in q_concepts if c not in hubs] or q_concepts
        neigh = sorted(self.onto.neighbours(base, depth=1) - set(q_concepts))
        # indivíduá pojmov z otázky (Tiramisu1: cena, hmotnosť, kto pripravil) hneď za pojmami,
        # inak ich z limitu MAX_FACTS vytlačia fakty o surovinách
        g = self.onto.graph
        own = [n for n in neigh if g.nodes[n].get("kind") == "individual" and
               any(d.get("kind") == "instance" and o in q_concepts for _, o, d in g.out_edges(n, data=True))]
        neigh = own + [n for n in neigh if n not in own]
        facts = self.onto.context_for(q_concepts + neigh).splitlines()
        noise = self._hub_noise(q_concepts)
        facts = [f for f in facts if f not in noise]
        # najprv fakty o pojmoch z otázky (kľúčové slová), potom významovo podobné (BGE-M3) – bez duplikátov
        sem = [f for f in self._sem_facts if f not in facts]
        n_kw = min(len(facts), MAX_FACTS - min(len(sem), SEM_FACTS))
        facts = facts[:n_kw] + sem[:MAX_FACTS - n_kw]
        onto_ctx = "\n".join(facts) or "(žiadne)"
        extra = ""
        if PRICE_RE.search(question):
            # ceny iba z ontológie: celý (krátky) cenník + bez úryvkov s cenami iných výrobcov
            extra += self._price_list() + "\n\n"
            hits = [h for h in hits if not re.search(r"€|\beur\b|\bcen", h.text, re.I)]
        if ALLERGEN_RE.search(question) and (tab := tables_context(question, self.onto)):
            # tabuľka priamo z PDF (stĺpce zloženie / alergény sú oddelené); surový chunk tej istej tabuľky vynechať
            extra += tab + "\n\n"
            hits = [h for h in hits if h.source not in (TABLE_PDF, LIST_PDF)]
        # najrelevantnejšie úryvky prvé (proti efektu "lost in the middle")
        doc_ctx = "\n\n".join(f"[{h.source}, s. {h.page}]\n{h.text}" for h in hits) or "(žiadne dokumenty)"
        user = (f"FAKTY Z ONTOLÓGIE:\n{onto_ctx}\n\n{extra}"
                f"ÚRYVKY Z DOKUMENTOV:\n{doc_ctx}\n\n"
                f"OTÁZKA: {question}")
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        msgs += (history or [])[-6:]  # krátka pamäť konverzácie
        msgs.append({"role": "user", "content": user})
        return msgs, onto_ctx

    def ask(self, question: str, history=None, stream=False):
        q_concepts, hits = self.retrieve(question)
        msgs, onto_ctx = self.build_messages(question, q_concepts, hits, history)
        return chat(msgs, stream=stream), q_concepts, hits, onto_ctx


if __name__ == "__main__":
    import sys
    rag = RAG()
    question = " ".join(sys.argv[1:]) or "Aké suroviny obsahuje tiramisu?"
    answer, concepts, hits, _ = rag.ask(question)
    print("Pojmy:", concepts)
    for h in hits:
        print(f"  rrf={h.score:.4f} cos={h.cosine:.2f} bm25={h.bm25:.1f} {h.ranks}  {h.source} s.{h.page}")
    print("\n" + answer)
