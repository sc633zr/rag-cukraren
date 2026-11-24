"""RAG Cukráreň – webová aplikácia (FastAPI backend + web/index.html frontend).
Spustenie:  .venv\\Scripts\\python server.py   ->  http://localhost:8000
"""
from __future__ import annotations

import json
import queue
import re
import sys
import threading
import time
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from config import DOCS_DIR, EMBED_MODEL, LLM_MODEL, TOP_K 
from ingest import list_rows_for, list_documents 
from llm import chat, ollama_status  
from rag import RAG  

app = FastAPI(title="RAG Cukráreň")
app.mount("/vendor", StaticFiles(directory=ROOT / "web" / "vendor"), name="vendor")

rag = RAG()
llm_lock = threading.Lock()   

SUGGESTED = [ 
    "Čo máte v ponuke?",
    "Koľko stojí tiramisu?",
    "Z čoho je tiramisu?",
    "Aké plnky do tort si môžem vybrať?",
    "Máte aj bezlepkové torty?",
    "Ako môžem zaplatiť?",
    "Koľko stojí cheesecake?",
    "Aké alergény má čokoládová plnka do torty?",
]


PREFIX = ("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
          "PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
          "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n")
SPARQL_PRESETS = [
    {"id": "ceny", "title": "Ceny produktov", "icon": "💶",
     "query": """SELECT ?produkt ?nazov ?cena ?hmotnost WHERE {
  ?i ?pc ?cena . ?pc rdfs:label "hasPrice" . ?i rdfs:label ?produkt .
  OPTIONAL { ?i ?pn ?nazov . ?pn rdfs:label "hasName" }
  OPTIONAL { ?i ?pw ?hmotnost . ?pw rdfs:label "hasWeight" }
} ORDER BY DESC(?cena)"""},
    {"id": "kto", "title": "Kto pripravuje produkty", "icon": "👩‍🍳",
     "query": """SELECT ?produkt ?pripravil WHERE {
  ?i ?p ?c . ?p rdfs:label "preparedBy" . ?i rdfs:label ?produkt . ?c rdfs:label ?pripravil .
}"""},
    {"id": "suroviny", "title": "Suroviny podľa ontológie", "icon": "🥚",
     "query": """SELECT ?trieda ?surovina WHERE {
  ?c rdfs:subClassOf|owl:equivalentClass/owl:intersectionOf/rdf:rest*/rdf:first ?r .
  ?r owl:onProperty ?p ; owl:someValuesFrom ?s . ?p rdfs:label "hasIngredient" .
  ?c rdfs:label ?trieda . ?s rdfs:label ?surovina .
} ORDER BY ?trieda"""},
    {"id": "sortiment", "title": "Sortiment (kategórie → produkty)", "icon": "🍰",
     "query": """SELECT ?kategoria ?produkt WHERE {
  ?k rdfs:subClassOf ?prod . ?prod rdfs:label "Product" .
  ?p rdfs:subClassOf ?k . ?k rdfs:label ?kategoria . ?p rdfs:label ?produkt .
} ORDER BY ?kategoria ?produkt"""},
    {"id": "zamestnanci", "title": "Zamestnanci", "icon": "🧑‍💼",
     "query": """SELECT ?rola ?osoba WHERE {
  ?c rdfs:subClassOf ?e . ?e rdfs:label "Employee" . ?c rdfs:label ?rola .
  OPTIONAL { ?i a ?c . ?i rdfs:label ?osoba }
}"""},
    {"id": "objednavky", "title": "Objednávky", "icon": "🧾",
     "query": """SELECT ?objednavka ?zakaznik ?produkt ?platba ?spracoval WHERE {
  ?o ?p1 ?z . ?p1 rdfs:label "hasCustomer" . ?o rdfs:label ?objednavka . ?z rdfs:label ?zakaznik .
  OPTIONAL { ?o ?p2 ?x . ?p2 rdfs:label "containsProduct" . ?x rdfs:label ?produkt }
  OPTIONAL { ?o ?p3 ?y . ?p3 rdfs:label "hasPaymentMethod" . ?y rdfs:label ?platba }
  OPTIONAL { ?o ?p4 ?w . ?p4 rdfs:label "processedBy" . ?w rdfs:label ?spracoval }
}"""},
]


def run_sparql(query: str) -> dict:
    q = query.strip()
    if not re.match(r"^(PREFIX[^\n]*\n\s*)*SELECT\b", q, re.IGNORECASE):
        raise HTTPException(400, "Povolené sú len dotazy SELECT.")
    t0 = time.perf_counter()
    res = rag.onto.rdf.query(PREFIX + q)
    rows = [[("" if v is None else str(v)) for v in row] for row in res]
    return {"vars": [str(v) for v in res.vars], "rows": rows, "ms": round((time.perf_counter() - t0) * 1000, 1)}


def concept_docs(concept: str, limit: int = 3) -> list[dict]:
    hits = [c for c in rag.chunks if concept in c["concepts"]]
    per_doc = Counter(c["source"] for c in hits)
    return [{"source": s, "count": n,
             "sample": next(c for c in hits if c["source"] == s)["text"][:260]} for s, n in per_doc.most_common(limit)]


def sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"



@app.get("/", response_class=HTMLResponse)
def index():
    return (ROOT / "web" / "index.html").read_text(encoding="utf-8")


@app.get("/api/info")
def info():
    ok, models = ollama_status()
    docs = list_documents()
    return {"ollama": ok, "models": models, "llm": LLM_MODEL, "embed": rag.embed_model,
            "llm_ready": any(m.startswith(LLM_MODEL) for m in models),
            "embed_ready": any(m.startswith(rag.embed_model) for m in models),
            "n_docs": len(docs), "n_chunks": len(rag.chunks),
            "n_nodes": rag.onto.graph.number_of_nodes(), "n_edges": rag.onto.graph.number_of_edges(),
            "n_facts": len({f for fs in rag.onto.facts.values() for f in fs}),
            "suggested": SUGGESTED, "top_k": TOP_K}


@app.get("/api/menu")
def menu():
    """Ponuka cukrárne = produkty s cenou v ontológii (+ hmotnosť, zloženie, kto ich pripravuje)."""
    g, sk = rag.onto.graph, rag.onto.labels_sk
    out = []
    for n, d in g.nodes(data=True):
        data = d.get("data", {})
        if "hasPrice" not in data:
            continue
        edges = [(e["label"], v) for _, v, e in g.out_edges(n, data=True)]
        cls = next((v for lab, v in edges if lab == "instance of"), None)
        ingr = [v for _, v, e in g.out_edges(cls, data=True) if e["label"] == "hasIngredient"] if cls else []
        parents = {p for i in ingr for _, p, e in g.out_edges(i, data=True) if e.get("kind") == "subclass"}
        ingr = [i for i in dict.fromkeys(ingr) if i not in parents]  # "mliečny výrobok" vynechať, ak je tam mascarpone
        out.append({"name": sk.get(cls, data.get("hasName", n)) if cls else data.get("hasName", n),
                    "price": float(data["hasPrice"]), "weight": data.get("hasWeight"),
                    "ingredients": [sk.get(i, i) for i in ingr],
                    "chef": next((v for lab, v in edges if lab == "preparedBy"), None),
                   
                    "has_allergens": bool(list_rows_for(sk.get(cls, n) if cls else n, rag.onto))})
    return sorted(out, key=lambda x: x["name"])


class AskBody(BaseModel):
    question: str
    history: list[dict] = []


@app.post("/api/ask")
def ask(body: AskBody):
    question = body.question.strip()
    if not question:
        raise HTTPException(400, "Prázdna otázka")

    def stream():
        t0 = time.perf_counter()
        try:
            search_q = question
            # doplňujúca otázka bez pojmu ("A z čoho je?") -> hľadať spolu s predchádzajúcou otázkou (bez volania LLM)
            if body.history and not rag.onto.find_concepts(question):
                prev = next((m["content"] for m in reversed(body.history) if m.get("role") == "user"), "")
                search_q = f"{prev} {question}".strip()

            yield sse("stage", {"stage": "retrieve"})
            concepts, hits = rag.retrieve(search_q)
            msgs, onto_ctx = rag.build_messages(question, concepts, hits, body.history)
            neigh = sorted(rag.onto.neighbours(concepts, depth=1) - set(concepts))
            yield sse("concepts", {"concepts": concepts, "neighbours": neigh,
                                   "sk": {c: rag.onto.labels_sk.get(c, "") for c in concepts + neigh}})
            sem = set(rag._sem_facts)
            yield sse("facts", {"facts": [{"text": f, "semantic": f in sem} for f in onto_ctx.splitlines()
                                          if f != "(žiadne)"]})
            yield sse("sources", {"sources": [
                {"source": h.source, "page": h.page, "text": h.text, "rrf": round(h.score, 4),
                 "cos": round(h.cosine, 3), "bm25": round(h.bm25, 2), "ranks": h.ranks, "concepts": h.concepts}
                for h in hits]})
            t_ret = time.perf_counter() - t0

            yield sse("stage", {"stage": "generate", "retrieve_s": round(t_ret, 1)})
            n_tok, t_first = 0, None
            parts = queue.Queue()

            def generate():
                try:
                    with llm_lock:
                        for part in chat(msgs, stream=True):
                            parts.put(("token", part))
                except Exception as e:  # noqa: BLE001
                    parts.put(("error", e))
                parts.put(("end", None))

            threading.Thread(target=generate, daemon=True).start()
            while True:
                try:
                    kind, part = parts.get(timeout=15)
                except queue.Empty:
                    yield ": ping\n\n"
                    continue
                if kind == "end":
                    break
                if kind == "error":
                    raise part
                if part:
                    if t_first is None:
                        t_first = time.perf_counter()
                    n_tok += 1
                    yield sse("token", {"t": part})
            t_end = time.perf_counter()
            gen_s = (t_end - t_first) if t_first else 0
            yield sse("done", {"total_s": round(t_end - t0, 1), "retrieve_s": round(t_ret, 1),
                               "first_token_s": round((t_first or t_end) - t0, 1),
                               "tokens": n_tok, "tok_per_s": round(n_tok / gen_s, 1) if gen_s else 0,
                               "model": LLM_MODEL})
        except Exception as e:  # noqa: BLE001
            yield sse("error", {"message": str(e)})

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/graph")
def graph(min_mentions: int = 2):
    g = rag.onto.graph
    nodes = [{"id": n, "label": n, "kind": d.get("kind", "class"), "sk": rag.onto.labels_sk.get(n, ""),
              "data": d.get("data", {})} for n, d in g.nodes(data=True)]
    edges = [{"from": s, "to": o, "label": d.get("label", ""), "kind": d.get("kind", "relation")}
             for s, o, d in g.edges(data=True)]
    per_doc: dict[str, Counter] = {}
    for c in rag.chunks:
        per_doc.setdefault(c["source"], Counter()).update(c["concepts"])
    docs = []
    for doc, cnt in per_doc.items():
        docs.append({"id": "doc:" + doc, "label": doc})
        edges += [{"from": "doc:" + doc, "to": k, "label": "", "kind": "mentions", "value": n}
                  for k, n in cnt.items() if n >= min_mentions and k in g]
    return {"nodes": nodes, "docs": docs, "edges": edges}


@app.get("/api/concept/{name}")
def concept(name: str):
    if name.startswith("doc:"):
        doc = name[4:]
        cnt = Counter(k for c in rag.chunks if c["source"] == doc for k in c["concepts"])
        return {"name": doc, "kind": "document", "concepts": cnt.most_common(12),
                "chunks": sum(c["source"] == doc for c in rag.chunks)}
    if name not in rag.onto.graph:
        raise HTTPException(404, "Neznámy pojem")
    d = rag.onto.graph.nodes[name]
    return {"name": name, "kind": d.get("kind"), "sk": rag.onto.labels_sk.get(name, ""),
            "data": d.get("data", {}), "facts": rag.onto.facts.get(name, []),
            "docs": concept_docs(name)}


@app.get("/api/sparql/presets")
def sparql_presets():
    return SPARQL_PRESETS


class SparqlBody(BaseModel):
    query: str


@app.post("/api/sparql")
def sparql(body: SparqlBody):
    try:
        return run_sparql(body.query)
    except HTTPException:
        raise
    except Exception as e:  
        raise HTTPException(400, f"Chyba v dotaze: {e}")


@app.get("/api/docs")
def docs():
    out = []
    for p in list_documents():
        chunks = [c for c in rag.chunks if c["source"] == p.name]
        cnt = Counter(k for c in chunks for k in c["concepts"])
        out.append({"name": p.name, "size_kb": round(p.stat().st_size / 1024),
                    "pages": max((c["page"] for c in chunks), default=0), "chunks": len(chunks),
                    "concepts": [k for k, _ in cnt.most_common(8)]})
    return out


@app.get("/api/pdf/{name}")
def pdf(name: str):
    allowed = {p.name: p for p in list_documents()}
    if name not in allowed:
        raise HTTPException(404, "Dokument neexistuje")
    return FileResponse(allowed[name], media_type="application/pdf" if name.endswith(".pdf") else None)


@app.get("/api/eval")
def eval_results():
    files = {}
    for f in sorted((ROOT / "eval").glob("*.md")):
        files[f.name] = f.read_text(encoding="utf-8")
    return files


if __name__ == "__main__":
    import uvicorn
    print("RAG Cukráreň beží na http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
