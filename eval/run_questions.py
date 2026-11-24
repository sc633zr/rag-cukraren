"""Testovacie otázky pre RAG Cukráreň -> eval/vysledky.md

Spustenie:  .venv\\Scripts\\python eval\\run_questions.py
"""
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from config import LLM_MODEL  # noqa: E402
from rag import RAG  # noqa: E402

QUESTIONS = [
    # (kategória, otázka, dokumenty so správnou odpoveďou – pre hodnotenie vyhľadávania; [] = odpoveď je v ontológii / nikde)
    ("ontológia", "Aké druhy zamestnancov pracujú v cukrárni?", []),
    ("ontológia", "Aké platobné metódy môže zákazník použiť?", []),
    ("ontológia", "Kto pripravil cheesecake a koľko stojí?", []),
    ("ontológia", "Aké druhy koláčov (Cake) cukráreň ponúka?", []),
    ("ontológia", "Čo musí obsahovať každá objednávka?", []),
    ("ontológia", "Koľko stojí tiramisu?", []),
    ("dokumenty", "Z čoho sa vyrába zmrzlina?", ["sk_Zmrzlina.pdf"]),
    ("dokumenty", "Ako sa vyrába čokoláda z kakaových bôbov?",
     ["sk_Cokolada.pdf", "sk_SPPK_cokolada_temperovanie_pralinky.pdf"]),
    ("dokumenty", "Ako sa temperuje čokoláda a pri akých teplotách?", ["sk_SPPK_cokolada_temperovanie_pralinky.pdf"]),
    ("dokumenty", "V akom pomere sa mieša čokoláda a smotana pri príprave ganache?", ["sk_SPPK_ganache.pdf"]),
    ("dokumenty", "Ktoré sú najznámejšie francúzske dezerty?", ["sk_SPPK_francuzske_dezerty.pdf"]),
    ("dokumenty", "Ako sa pripravuje piškótový korpus?",
     ["sk_SPPK_francuzske_dezerty.pdf", "sk_Sladke_recepty_zo_Slovenska.pdf"]),
    ("recepty", "Ako sa pripravuje Sacherova torta a aká glazúra sa na ňu používa?",
     ["sk_Sladke_recepty_zo_Slovenska.pdf"]),
    ("recepty", "Ako sa pečú vanilkové rožky?", ["sk_Sladke_recepty_zo_Slovenska.pdf"]),
    ("odbor cukrár", "Aké hygienické zásady musí dodržiavať cukrár pri práci?",
     ["sk_SPPK_zaverecna_skuska_cukrar_2025.pdf"]),
    ("zloženie", "Z čoho sa skladá čokoládová plnka a aké alergény obsahuje?",
     ["sk_iCukraren_zlozenie_a_alergeny.pdf"]),
    ("katalóg", "Aké cheesecaky ponúka Luigi Dolci?", ["sk_Luigi_Dolci_katalog_2026.pdf"]),
    ("katalóg", "Na koľko porcií je torta od Luigi Dolci a ako dlho vydrží zmrazená?",
     ["sk_Luigi_Dolci_katalog_2026.pdf"]),
    ("katalóg + ontológia", "Ktoré produkty obsahujú tiramisu a mascarpone?",
     ["sk_Luigi_Dolci_katalog_2026.pdf", "sk_iCukraren_zlozenie_a_alergeny.pdf"]),
    ("mimo domény", "Koľko stojí pizza margherita?", []),
    ("cena – nie je v ponuke", "Koľko stojí Sacherova torta?", []),
    ("alergény", "Aké alergény má orechová plnka?", ["sk_iCukraren_zlozenie_a_alergeny.pdf"]),
]
# Ceny sa berú iba z ontológie (hasPrice); produkt bez ceny v ontológii = nie je v ponuke.
# Alergény sa berú z tabuľky v sk_iCukraren_zlozenie_a_alergeny.pdf (src/ingest.py).


def main():
    rag = RAG()
    out = Path(__file__).parent / "vysledky.md"
    lines = [f"# Výsledky testovacích otázok\n",
             f"Model: `{LLM_MODEL}` · {datetime.now():%Y-%m-%d %H:%M} · chunkov v indexe: {len(rag.chunks)}\n"]
    for n, (cat, q, _expected) in enumerate(QUESTIONS, 1):
        t0 = time.time()
        try:
            answer, concepts, hits, _ = rag.ask(q)
        except Exception as e:  # noqa: BLE001
            answer, concepts, hits = f"CHYBA: {e}", [], []
        dt = time.time() - t0
        src = "; ".join(f"{h.source} s.{h.page} ({h.score:.2f})" for h in hits)
        lines += [f"\n## {n}. [{cat}] {q}\n",
                  f"- pojmy z ontológie: {', '.join(concepts) or '—'}",
                  f"- nájdené zdroje: {src or '—'}",
                  f"- čas: {dt:.0f} s\n",
                  answer.strip() + "\n"]
        out.write_text("\n".join(lines), encoding="utf-8")  # priebežne ukladať
        print(f"{n}/{len(QUESTIONS)} hotovo ({dt:.0f} s)", flush=True)
    print("Uložené:", out)


if __name__ == "__main__":
    main()
