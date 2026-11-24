"""Spoločné nastavenia projektu (cesty, modely, parametre vyhľadávania)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_FILE = ROOT / "ontology" / "cukraren.owl"
SYNONYMS_FILE = ROOT / "ontology" / "synonyms.json"
LABELS_SK_FILE = ROOT / "ontology" / "labels_sk.json"
DOCS_DIR = ROOT / "data" / "pdfs"          
PDF_DIR = DOCS_DIR                          
DOC_TYPES = ("*.pdf", "*.docx", "*.txt")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3:4b-instruct")
# bge-m3 je viacjazyčný (SK + EN) 
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")


INDEX_ROOT = ROOT / "data" / "index"
INDEX_DIR = INDEX_ROOT / EMBED_MODEL.replace(":", "_").replace("/", "_")

CHUNK_SIZE = 800      # znakov na jeden chunk
CHUNK_OVERLAP = 150   # prekryv medzi chunkmi

# --- vyhľadávanie (hybridné: vektor + BM25 + ontológia, spojené cez Reciprocal Rank Fusion)
TOP_K = 4             # koľko chunkov ide do promptu
CANDIDATES = 30       # koľko najlepších kandidátov z každého zoznamu vstupuje do RRF
RRF_K = 60            # konštanta RRF
MIN_SIM = 0.35        # chunk s nižšou kosínusovou podobnosťou a bez zhody kľúčových slov sa zahodí
