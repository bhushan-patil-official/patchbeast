"""Group similar articles into clusters (pure Python TF-IDF cosine; no ML dependency).

Input is OUR data only: titles + our own summaries. A cluster needs >= `min_domains` independent
outlets, so a single-source item is never rewritten into a "story"."""

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

STOP = set(
    [
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "its",
        "their",
        "they",
        "them",
        "will",
        "not",
        "but",
        "you",
        "your",
        "our",
        "out",
        "can",
        "all",
        "into",
        "over",
        "after",
        "about",
        "more",
        "also",
        "new",
        "been",
        "than",
        "then",
        "when",
        "what",
        "which",
        "who",
        "how",
        "why",
        "just",
        "says",
        "said",
        "report",
        "reports",
        "reported",
        "update",
        "game",
        "games",
        "players",
        "player",
    ]
)
_TOKEN = re.compile(r"\d+(?:\.\d+)+|[a-z0-9]{3,}")


@dataclass(frozen=True)
class Doc:
    id: int
    text: str
    domain: str
    when: datetime | None = None


def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOP]


def _tfidf(docs: list[Doc]) -> list[dict[str, float]]:
    toks = [tokens(d.text) for d in docs]
    df: Counter[str] = Counter()
    for t in toks:
        df.update(set(t))
    n = len(docs)
    vecs = []
    for t in toks:
        tf = Counter(t)
        v = {w: (1 + math.log(c)) * (math.log((1 + n) / (1 + df[w])) + 1) for w, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({w: x / norm for w, x in v.items()})
    return vecs


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(w, 0.0) for w, x in a.items())


def cluster(
    docs: list[Doc], *, threshold: float = 0.30, min_domains: int = 2, max_size: int = 8
) -> list[list[int]]:
    """Greedy average-link clustering. Returns lists of doc ids with >= min_domains distinct domains."""
    if len(docs) < min_domains:
        return []
    order = sorted(
        range(len(docs)),
        key=lambda i: (docs[i].when or datetime.min.replace(tzinfo=None), docs[i].id),
    )
    vecs = _tfidf(docs)
    groups: list[list[int]] = []
    for i in order:
        best, best_sim = None, 0.0
        for g in groups:
            if len(g) >= max_size:
                continue
            sim = sum(cosine(vecs[i], vecs[j]) for j in g) / len(g)
            if sim > best_sim:
                best, best_sim = g, sim
        if best is not None and best_sim >= threshold:
            best.append(i)
        else:
            groups.append([i])
    out = []
    for g in groups:
        if len({docs[i].domain for i in g}) >= min_domains:
            out.append(sorted(docs[i].id for i in g))
    return out
