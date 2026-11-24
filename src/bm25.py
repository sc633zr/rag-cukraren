"""Jednoduchý BM25 (vyhľadávanie podľa kľúčových slov) bez externých knižníc.

Vektorové vyhľadávanie zle nachádza presné názvy (napr. "bábovka", "krémeš", kódy výrobkov),
preto ho kombinujeme s BM25 (odporúčanie z článku Databricks: hybrid search).
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

STEM_LEN = 5  # hrubý "stemmer" pre slovenčinu: bábovka/bábovky/bábovku -> "babov"


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))  # odstránenie diakritiky
    return [t[:STEM_LEN] for t in re.findall(r"[a-z0-9]+", text) if len(t) >= 3]


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tfs = [Counter(tokenize(d)) for d in docs]
        self.lens = [sum(tf.values()) for tf in self.tfs]
        self.avg = sum(self.lens) / max(len(self.lens), 1)
        df = Counter(t for tf in self.tfs for t in tf)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        q = set(tokenize(query))
        out = []
        for tf, ln in zip(self.tfs, self.lens):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * ln / self.avg))
            out.append(s)
        return out
