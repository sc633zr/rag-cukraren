"""Indexovanie dokumentov: PDF/DOCX/TXT -> text -> chunky -> embeddingy (Ollama) + značky z ontológie.

Spustenie:  python src/ingest.py            (model z config.EMBED_MODEL)
            python src/ingest.py <model>   (iný embedding model -> vlastný priečinok indexu)
Výsledok:   data/index/<model>/chunks.json, embeddings.npy, meta.json
"""
from __future__ import annotations

import json
import re
import sys
import time
import zipfile
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
from pypdf import PdfReader

from config import CHUNK_OVERLAP, CHUNK_SIZE, DOC_TYPES, DOCS_DIR, EMBED_MODEL, INDEX_ROOT
from llm import embed
from ontology import load_ontology


# " č " medzi písmenami alebo " ž" pred interpunkciou; NIE " č" na začiatku normálneho slova ("bola čokoláda")
DIACRITIC_SPLIT = re.compile(r"(?<=\w) ([čšžťďľňŕĺäôáéíóúýČŠŽŤĎĽŇ])(?: (?=\w)|(?= ?[.,;:!?)]))")


def _clean(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)      # rozdelené slová na konci riadku
    text = re.sub(r"\s+", " ", text).strip()     # normalizácia medzier
    # niektoré PDF (napr. katalóg Luigi Dolci) oddeľujú písmená s diakritikou medzerami: "Ru č ne" -> "Ručne"
    for _ in range(2):  # 2× kvôli dvom takým písmenám za sebou ("dopĺ ň ajú")
        text = DIACRITIC_SPLIT.sub(r"\1", text)
    return text


def pdf_pages(path: Path) -> list[tuple[int, str]]:
    pages = []
    for i, page in enumerate(PdfReader(str(path)).pages, start=1):
        text = _clean(page.extract_text() or "")
        if text:
            pages.append((i, text))
    return pages


def docx_pages(path: Path) -> list[tuple[int, str]]:
    """DOCX nemá strany -> celý text ako "strana" 1 (odseky oddelené novým riadkom)."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    paras = [re.sub(r"<[^>]+>", "", p) for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)]
    return [(1, _clean(". ".join(p for p in paras if p.strip())))]


def txt_pages(path: Path) -> list[tuple[int, str]]:
    return [(1, _clean(path.read_text(encoding="utf-8", errors="ignore")))]


READERS = {".pdf": pdf_pages, ".docx": docx_pages, ".txt": txt_pages}


def list_documents(docs_dir: Path = DOCS_DIR) -> list[Path]:
    return sorted(p for pattern in DOC_TYPES for p in docs_dir.glob(pattern))


def chunk_text(text: str, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP) -> list[str]:
    """Delenie po vetách do chunkov ~size znakov s prekryvom."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) > size and cur:
            chunks.append(cur.strip())
            cur = cur[-overlap:]  # prekryv s predchádzajúcim chunkom
        cur += " " + s
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def build_index(docs_dir: Path = DOCS_DIR, progress=print, embed_model: str = EMBED_MODEL) -> int:
    onto = load_ontology()
    index_dir = INDEX_ROOT / embed_model.replace(":", "_").replace("/", "_")
    records = []
    for doc in list_documents(docs_dir):
        n_before = len(records)
        for page_no, text in READERS[doc.suffix.lower()](doc):
            for ch in chunk_text(text):
                records.append({"source": doc.name, "page": page_no, "text": ch,
                                "concepts": onto.find_concepts(ch)})
        progress(f"{doc.name}: {len(records) - n_before} chunkov")

    if not records:
        progress("V priečinku data/pdfs nie sú žiadne dokumenty.")
        return 0

    progress(f"Počítam embeddingy ({embed_model}) pre {len(records)} chunkov ...")
    t0, vecs, batch = time.time(), [], 16
    for i in range(0, len(records), batch):
        vecs.extend(embed([r["text"] for r in records[i:i + batch]], model=embed_model))
        progress(f"  {min(i + batch, len(records))}/{len(records)}")
    emb = np.array(vecs, dtype=np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9  # normalizácia -> kosínus = skalárny súčin

    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / "chunks.json").write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    np.save(index_dir / "embeddings.npy", emb)
    meta = {"embed_model": embed_model, "created": datetime.now().isoformat(timespec="seconds"),
            "n_chunks": len(records), "dim": int(emb.shape[1]), "embed_seconds": round(time.time() - t0),
            "documents": sorted({r["source"] for r in records}),
            "chunk_size": CHUNK_SIZE, "chunk_overlap": CHUNK_OVERLAP}
    (index_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    progress(f"Hotovo: {len(records)} chunkov uložených do {index_dir}")
    return len(records)


def add_documents(names: list[str], progress=print, embed_model: str = EMBED_MODEL) -> int:
    """Pridá nové dokumenty do existujúceho indexu (embeddingy sa počítajú len pre ne)."""
    onto = load_ontology()
    index_dir = INDEX_ROOT / embed_model.replace(":", "_").replace("/", "_")
    records = json.loads((index_dir / "chunks.json").read_text(encoding="utf-8"))
    emb = np.load(index_dir / "embeddings.npy")
    have = {r["source"] for r in records}
    new = []
    for name in names:
        doc = DOCS_DIR / name
        if name in have:
            progress(f"{name}: už je v indexe")
            continue
        for page_no, text in READERS[doc.suffix.lower()](doc):
            for ch in chunk_text(text):
                new.append({"source": doc.name, "page": page_no, "text": ch, "concepts": onto.find_concepts(ch)})
    if not new:
        return 0
    progress(f"Počítam embeddingy pre {len(new)} nových chunkov ...")
    vecs = []
    for i in range(0, len(new), 16):
        vecs.extend(embed([r["text"] for r in new[i:i + 16]], model=embed_model))
    v = np.array(vecs, dtype=np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
    records += new
    emb = np.vstack([emb, v])
    (index_dir / "chunks.json").write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    np.save(index_dir / "embeddings.npy", emb)
    meta_f = index_dir / "meta.json"
    meta = json.loads(meta_f.read_text(encoding="utf-8"))
    meta.update(n_chunks=len(records), documents=sorted({r["source"] for r in records}),
                updated=datetime.now().isoformat(timespec="seconds"))
    meta_f.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    progress(f"Pridaných {len(new)} chunkov, spolu {len(records)}")
    return len(new)


# ================================================================ čítanie tabuliek z PDF (po stĺpcoch)
# Bežné chunkovanie zlúči tabuľku do jedného riadku a LLM nevie, kde končí stĺpec ZLOŽENIE
# a začína stĺpec ALERGÉNY. Preto sa tieto dve PDF čítajú aj po stĺpcoch (podľa pozície hlavičky).
TABLE_PDF = "sk_iCukraren_zlozenie_a_alergeny.pdf"


def _join_cells(parts: list[str]) -> str:
    out = ""
    for p in (p.strip() for p in parts):
        if not p:
            continue
        if out.endswith("-"):
            out = out[:-1] + p          # rozdelené slovo: Calle- + baut
        else:
            out = f"{out} {p}" if out else p
    return re.sub(r"\s+", " ", out).replace(" )", ")").strip(" ,")


@lru_cache(maxsize=1)
def read_table_by_columns() -> tuple[list[dict], str]:
    """Vráti (riadky tabuľky, poznámky pod tabuľkou)."""
    from pypdf import PdfReader
    path = DOCS_DIR / TABLE_PDF
    if not path.exists():
        return [], ""
    text = PdfReader(str(path)).pages[0].extract_text(extraction_mode="layout")
    lines = text.splitlines()
    head = next(l for l in lines if "ZLOŽENIE" in l and "ALERG" in l)
    z, a = head.index("ZLOŽENIE"), head.index("ALERG")

    rows, group, pending, notes = [], "", [], []
    cur = None
    for i, l in enumerate(lines):
        if l.strip().startswith("V prípade"):           # koniec tabuľky -> poznámky
            notes = [x.strip() for x in lines[i:] if x.strip()]
            break
        if not l.strip():
            continue
        name, comp, alg = l[:z].strip(), l[z:a], l[a:]
        if "ZLOŽENIE" in comp:                           # hlavička sekcie (KORPUSY, PLNKY)
            group, cur = name, None
            continue
        if alg and l[a - 1] != " ":                      # text zloženia pretiekol do stĺpca alergénov
            m = re.match(r"\S*?-", alg) or re.match(r"\S+\s", alg)
            if m:
                comp, alg = comp + m.group(0), alg[m.end():]
        if name:                                         # nový riadok tabuľky
            cur = {"skupina": group, "nazov": name, "_z": [c for c, _ in pending] + [comp],
                   "_a": [x for _, x in pending] + [alg]}
            rows.append(cur)
            pending = []
        elif comp.rstrip().endswith("-") or cur is None:  # pokračuje v nasledujúcom riadku tabuľky
            pending.append((comp, alg))
        else:                                            # pokračovanie predchádzajúceho riadku
            cur["_z"].append(comp)
            cur["_a"].append(alg)
    for r in rows:
        r["zlozenie"] = _join_cells(r.pop("_z"))
        r["alergeny"] = _join_cells(r.pop("_a")) or "žiadne uvedené"
    return rows, _join_cells(notes)


# ---------------------------------------------------------------- tabuľka v tvare zoznamu (jedlo + kávové nápoje)
LIST_PDF = "sk_zoznam_alergenov.pdf"
_UPPER = "A-ZÁČĎÉÍĽĹŇÓÔŔŠŤÚÝŽ"


@lru_cache(maxsize=1)
def read_list_table() -> list[dict]:
    """Riadky zo sk_zoznam_alergenov.pdf:
    jedlo:  'New York Cheesecake 130 Lepok (1), vajcia (3), mlieko (7) Arašidy (5), sója (6)'
            -> obsahuje: lepok, vajcia, mlieko | môže obsahovať stopy: arašidy, sója
    nápoje: 'Caffe Latte (7) Espresso s ...' -> obsahuje: mlieko"""
    from pypdf import PdfReader
    path = DOCS_DIR / LIST_PDF
    if not path.exists():
        return []
    pages = [p.extract_text() or "" for p in PdfReader(str(path)).pages]
    codes = {m.group(1): m.group(2).strip() for p in pages
             for m in re.finditer(r"(\d+) – ([^/\n]+?) /", p)}
    rows = []
    for page_no, text in enumerate(pages, 1):
        lines = [l.strip() for l in text.splitlines()]
        if any("OBSAHUJE ALERG" in l for l in lines):                    # tabuľka JEDLO
            body = lines[lines.index(next(l for l in lines if "OBSAHUJE ALERG" in l)) + 1:]
            cur = None
            for i, l in enumerate(body):
                if not l or (l.isupper() and not re.search(r"\d", l)):  # nadpis sekcie (SENDVIČE)
                    continue
                if "(" not in l and i + 1 < len(body) and body[i + 1].startswith("["):
                    body[i + 1] = l + " " + body[i + 1]                  # 'Makrónka' + '[Pistácia, ...] 20'
                    continue
                m = re.match(r"^(.+?)\s+(\d{2,3})(?:\s+(.*))?$", l)
                if m and "(" not in m.group(1):
                    cur = {"page": page_no, "nazov": m.group(1).strip(), "gramaz": m.group(2),
                           "_t": m.group(3) or "", "typ": "jedlo"}
                    rows.append(cur)
                elif cur:
                    cur["_t"] += " " + l
            continue
        if "NÁZOV + (ALERGÉN)" in text and re.search(r"ESPRESSO|COFFEE", text):  # kávové nápoje
            for l in lines:
                m = re.match(rf"^([{_UPPER}][^()]{{1,40}}?) \(([\d, ]+)\)", l)
                if m:
                    names = [codes.get(c.strip(), c) for c in m.group(2).split(",")]
                    rows.append({"page": page_no, "nazov": m.group(1).strip(), "typ": "káva",
                                 "obsahuje": ", ".join(names), "stopy": ""})
    for r in rows:
        if "_t" in r:
            t = re.sub(r"\s+", " ", r.pop("_t")).strip()
            parts = re.split(rf"\)\s+(?=[{_UPPER}])", t, maxsplit=1)    # 'Lepok (1), mlieko (7) Arašidy (5)'
            clean = lambda x: re.sub(r"\s*\(\d+\)", "", x).strip(" ,").lower()
            r["obsahuje"] = clean(parts[0] + (")" if len(parts) > 1 else ""))
            r["stopy"] = clean(parts[1]) if len(parts) > 1 else ""
    return rows


COFFEE_RE = re.compile(r"\b(káv|kav|espresso|latte|cappuccino|coffee)", re.I)
TABLE_RE = re.compile(r"\b(plnk|náplň|naplň|korpus|piškót)", re.I)


def list_rows_for(question: str, onto) -> list[dict]:
    """Riadky zoznamu, ktoré sa týkajú otázky (podľa spoločných pojmov ontológie s názvom položky)."""
    rows = read_list_table()
    q = set(onto.find_concepts(question))
    g = onto.graph
    general = {c for c in q if sum(d.get("kind") == "subclass" for _, _, d in g.in_edges(c, data=True)) >= 3}
    q -= general                                   # Cake, Dessert ... by vybrali všetko
    scored = [(len(q & set(onto.find_concepts(r["nazov"]))), r) for r in rows if r["typ"] == "jedlo"]
    best = max((s for s, _ in scored), default=0)
    out = [r for s, r in scored if best and s == best]
    if COFFEE_RE.search(question):
        out += [r for r in rows if r["typ"] == "káva"]
    return out


def tables_context(question: str = "", onto=None) -> str:
    """Alergény pre prompt: relevantné riadky zo zoznamu alergénov + tabuľka plniek/korpusov."""
    out = []
    # otázka na plnku / korpus torty -> iba tabuľka plniek; inak zoznam jedál a nápojov
    lst = list_rows_for(question, onto) if onto is not None and not TABLE_RE.search(question) else []
    if lst:
        out.append(f"ZOZNAM ALERGÉNOV [{LIST_PDF}]:")
        for r in lst:
            stopy = f" | môže obsahovať stopy: {r['stopy']}" if r["stopy"] else ""
            out.append(f"- {r['nazov']} (s. {r['page']}): OBSAHUJE: {r['obsahuje'] or 'žiadne'}{stopy}")
    rows, notes = read_table_by_columns()
    if rows and (not lst or TABLE_RE.search(question)):
        out.append(f"TABUĽKA ALERGÉNOV PLNIEK A KORPUSOV [{TABLE_PDF}, s. 1] – alergény sú IBA v stĺpci ALERGÉNY:")
        for r in rows:
            kind = {"KORPUSY": "korpus", "PLNKY": "plnka"}.get(r["skupina"], r["skupina"].lower())
            out.append(f"- {r['nazov']} {kind}: zloženie: {r['zlozenie']} | ALERGÉNY: {r['alergeny']}")
        if notes:
            out.append(f"Poznámky: {notes}")
    if out:
        out.append("Ak sa pýtaný výrobok v týchto zoznamoch nenachádza, napíš, že alergény preň nie sú uvedené.")
    return "\n".join(out)


if __name__ == "__main__":
    # python src/ingest.py            -> celý index nanovo
    # python src/ingest.py --add X.pdf -> len pridať nový dokument
    if len(sys.argv) > 2 and sys.argv[1] == "--add":
        add_documents(sys.argv[2:])
    else:
        build_index(embed_model=sys.argv[1] if len(sys.argv) > 1 else EMBED_MODEL)
