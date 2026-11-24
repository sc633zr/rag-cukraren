# RAG Cukráreň

Lokálny RAG (Retrieval-Augmented Generation) systém pre doménu **cukráreň**. Odpovedá na otázky v slovenčine
na základe vlastnej OWL ontológie (WebProtégé) a 10 slovenských PDF dokumentov. Všetky modely bežia lokálne
cez [Ollama](https://ollama.com): `qwen3:4b-instruct` píše odpovede, `bge-m3` počíta embeddingy.

Podrobná dokumentácia: [`dokumentacia/dokumentacia.pdf`](dokumentacia/dokumentacia.pdf).

## Architektúra

```
INDEXOVANIE (raz)
  10 PDF -> text po stranách -> čistenie -> chunky (~800 znakov, prekryv 150)
         -> značky pojmov ontológie -> embeddingy bge-m3 -> data/index/

OTÁZKA (zakaždým)
  otázka -> pojmy ontológie v otázke (+ susedia v grafe)
         -> vyhľadávanie: vektor (bge-m3) + BM25 -> Reciprocal Rank Fusion -> 4 chunky
         -> prompt: pravidlá + fakty z ontológie (+ cenník / alergény) + úryvky z dokumentov + otázka
         -> qwen3:4b-instruct -> odpoveď so zdrojmi [súbor, s. X] -> webová stránka
```

- **Ontológia = údaje našej cukrárne** (ponuka, ceny, zamestnanci, objednávky, zloženie výrobkov).
  Prevedie sa na graf, fakty (vety pre prompt) a vzory na hľadanie pojmov v texte.
- **Dokumenty = všeobecné znalosti** (recepty, technológia, zloženie, alergény).
- **Ceny** sa berú iba z ontológie; výrobok bez ceny = „Tento produkt v ponuke našej cukrárne nie je.“
- **Tabuľky** (zloženie a alergény) sa čítajú z PDF po stĺpcoch, aby model nezamieňal stĺpce.

## Štruktúra

| Súbor | Popis |
|---|---|
| `src/config.py` | nastavenia (cesty, modely, chunky, parametre vyhľadávania) |
| `src/ontology.py` | OWL → graf, fakty a vzory na hľadanie pojmov |
| `src/ingest.py` | indexovanie PDF → chunky → embeddingy → `data/index/`; čítanie tabuliek po stĺpcoch |
| `src/bm25.py` | vyhľadávanie podľa kľúčových slov |
| `src/rag.py` | hybridné vyhľadávanie, fakty z ontológie, prompt, odpoveď |
| `src/llm.py` | komunikácia s Ollamou |
| `server.py` | webový server (FastAPI) |
| `web/index.html` | webové rozhranie (knižnice `marked` a `vis-network` vo `web/vendor/`) |
| `ontology/` | `cukraren.owl`, `synonyms.json`, `labels_sk.json` |
| `data/pdfs/` | 10 dokumentov (nie sú v repozitári, pozri nižšie) |
| `data/index/` | index (vytvorí `src/ingest.py`) |
| `eval/` | hodnotenie vyhľadávania a testovacie otázky, výsledky |
| `dokumentacia/` | dokumentácia (PDF) |
| `run_web.bat` | spustenie aplikácie |
| `run_public.bat` | spustenie aplikácie s dočasným verejným odkazom |

## Inštalácia a spustenie

1. Nainštalovať Ollama (https://ollama.com/download) a stiahnuť modely (~3,7 GB):
   ```
   ollama pull qwen3:4b-instruct
   ollama pull bge-m3
   ```
2. Python prostredie:
   ```
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt
   ```
3. Dokumenty nie sú súčasťou repozitára (autorské práva). Stiahnuť ich z odkazov v tabuľke nižšie
   do priečinka `data/pdfs/` pod uvedenými názvami súborov a vytvoriť index (~10–15 min na CPU):
   ```
   .venv\Scripts\python src\ingest.py
   ```
4. Spustiť aplikáciu: `run_web.bat` alebo `.venv\Scripts\python server.py` → http://localhost:8000

**Verejný odkaz (voliteľné):** stiahnuť `cloudflared-windows-amd64.exe` z
https://github.com/cloudflare/cloudflared/releases, uložiť ako `tools\cloudflared.exe` a spustiť `run_public.bat`.
V okne sa zobrazí odkaz `https://….trycloudflare.com`, ktorý funguje, kým je okno otvorené.

## Použité dokumenty

| # | Dokument | Súbor v `data/pdfs/` | Zdroj |
|---|---|---|---|
| 1 | Sladké recepty zo Slovenska | `sk_Sladke_recepty_zo_Slovenska.pdf` | https://ivanstefanec.sk/wp-content/uploads/2024/04/Sladke-recepty-web-1.pdf |
| 2 | Francúzske dezerty (SPPK) | `sk_SPPK_francuzske_dezerty.pdf` | https://sppk.sk/download/3557 (Word → PDF) |
| 3 | Ganache (SPPK) | `sk_SPPK_ganache.pdf` | https://www.sppk.sk/download/3555 (Word → PDF) |
| 4 | Čokoláda, temperovanie, pralinky (SPPK) | `sk_SPPK_cokolada_temperovanie_pralinky.pdf` | https://sppk.sk/download/3556 (Word → PDF) |
| 5 | Záverečná skúška 2025/2026, odbor cukrár (SPPK) | `sk_SPPK_zaverecna_skuska_cukrar_2025.pdf` | https://sppk.sk/download/3520 |
| 6 | Katalóg Luigi Dolci 2026 | `sk_Luigi_Dolci_katalog_2026.pdf` | https://www.desert.sk/assets/katalog/Luigi-Dolci-katalog-2026-A4.pdf |
| 7 | Zloženie a alergény (iCukráreň) | `sk_iCukraren_zlozenie_a_alergeny.pdf` | https://www.icukraren.sk |
| 8 | Čokoláda (Wikipédia) | `sk_Cokolada.pdf` | https://sk.wikipedia.org/wiki/Čokoláda (uložiť ako PDF) |
| 9 | Zmrzlina (Wikipédia) | `sk_Zmrzlina.pdf` | https://sk.wikipedia.org/wiki/Zmrzlina (uložiť ako PDF) |
| 10 | Zoznam alergénov 2025 (Starbucks Slovensko) | `sk_zoznam_alergenov.pdf` | https://starbucksslovakia.sk/sites/starbucks-sk-pwa/files/2025-09/SBX_VE126_SK_Alergeny_online.pdf |

## Hodnotenie

Vyhľadávanie (iba krok vyhľadávania, bez generovania odpovede; 13 otázok so známym dokumentom, top-4):
**hit@4 100 %, MRR 0,96** (vektor + BM25).
Odpovede na 22 testovacích otázok: [`eval/vysledky.md`](eval/vysledky.md).
