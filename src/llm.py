"""Komunikácia s lokálnym Ollama serverom (REST API)."""
from __future__ import annotations

import requests

from config import EMBED_MODEL, LLM_MODEL, OLLAMA_URL


def embed(texts: list[str], model: str = EMBED_MODEL) -> list[list[float]]:
    r = requests.post(f"{OLLAMA_URL}/api/embed", json={"model": model, "input": texts}, timeout=300)
    r.raise_for_status()
    return r.json()["embeddings"]


def chat(messages: list[dict], model: str | None = None, stream: bool = False):
    """messages = [{"role": "system"|"user"|"assistant", "content": "..."}]"""
    model = model or LLM_MODEL
    payload = {"model": model, "messages": messages, "stream": stream, "keep_alive": "30m",
               "options": {"temperature": 0.2, "num_predict": 400, "num_ctx": 4096, "repeat_penalty": 1.2}}
    if model.startswith("qwen3") and "instruct" not in model:
        
        payload["think"] = False
    if not stream:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=600)
        r.raise_for_status()
        return r.json()["message"]["content"]

    def gen():
        import json
        with requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=600) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    part = json.loads(line)
                    yield part.get("message", {}).get("content", "")
    return gen()


def ollama_status() -> tuple[bool, list[str]]:
    """(beží server?, zoznam stiahnutých modelov)"""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        r.raise_for_status()
        return True, [m["name"] for m in r.json().get("models", [])]
    except requests.RequestException:
        return False, []
