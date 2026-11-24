"""Hodnotenie VYHĽADÁVANIA (bez LLM) – podľa odporúčania Databricks: retrieval hodnotiť zvlášť.

Metriky (len otázky, pri ktorých vieme, v ktorom dokumente je odpoveď):
  hit@k  – podiel otázok, kde je správny dokument medzi top-k nájdenými chunkmi
  MRR    – priemer 1/poradie prvého správneho chunku (1.0 = vždy na 1. mieste)

Porovnávané konfigurácie: rôzne embedding modely × (iba vektor | vektor+BM25 | vektor+BM25+ontológia).
Spustenie:  .venv\\Scripts\\python eval\\retrieval_eval.py
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import INDEX_ROOT, TOP_K  # noqa: E402
from rag import RAG  # noqa: E402
from run_questions import QUESTIONS  # noqa: E402

CONFIGS = [  # (názov, vektor, bm25, ontológia)
    ("iba vektor", True, False, False),
    ("vektor + BM25", True, True, False),
    ("vektor + BM25 + ontológia", True, True, True),
]


def evaluate(rag: RAG, k=TOP_K):
    docs_in_index = set(rag.meta.get("documents") or {c["source"] for c in rag.chunks})
    rows = []
    for name, v, b, o in CONFIGS:
        hits, rr, n, per_q = 0, 0.0, 0, []
        for cat, q, expected in QUESTIONS:
            exp = [e for e in expected if e in docs_in_index]
            if not exp:
                continue  # otázka bez dokumentu (alebo dokument nie je v tomto indexe)
            _, found = rag.retrieve(q, k=k, use_vector=v, use_bm25=b, use_onto=o, onto_weight=1.0 if o else 0.0)
            srcs = [h.source for h in found]
            pos = next((i for i, s in enumerate(srcs, 1) if s in exp), None)
            n += 1
            hits += pos is not None
            rr += 1 / pos if pos else 0
            per_q.append("✅" if pos else "❌")
        rows.append((name, n, hits / n if n else 0, rr / n if n else 0, " ".join(per_q)))
    return rows


def main():
    out = Path(__file__).parent / "retrieval_vysledky.md"
    lines = ["# Hodnotenie vyhľadávania (bez LLM)\n",
             f"{datetime.now():%Y-%m-%d %H:%M} · top-k = {TOP_K}\n",
             "| embedding model | dokumentov | konfigurácia | otázok | hit@k | MRR | po otázkach |",
             "|---|---|---|---|---|---|---|"]
    rag = RAG()
    for index_dir in sorted(p for p in INDEX_ROOT.iterdir() if (p / "chunks.json").exists()):
        rag.reload_index(index_dir)
        n_docs = len({c["source"] for c in rag.chunks})
        for name, n, hit, mrr, per_q in evaluate(rag):
            lines.append(f"| {index_dir.name} | {n_docs} | {name} | {n} | {hit:.0%} | {mrr:.2f} | {per_q} |")
            print(lines[-1], flush=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Uložené:", out)


if __name__ == "__main__":
    main()
