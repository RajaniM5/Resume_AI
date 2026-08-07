"""Sentence embeddings for resume/JD semantic similarity.

Per docs/ARCHITECTURE.md: `sentence-transformers` on CPU for MVP, with JD
embeddings cached (a JD doesn't change per-resume within a batch). The
`sentence-transformers` extra is imported lazily so this module - and
anything that only needs skill-gap/rule-based scoring - stays importable
without torch installed.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

DEFAULT_MODEL_NAME = "all-mpnet-base-v2"


@lru_cache(maxsize=1)
def _get_model(model_name: str = DEFAULT_MODEL_NAME) -> Any:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Semantic matching requires the 'ml' extra (sentence-transformers). "
            "Install with: pip install resume-ai[ml]"
        ) from exc

    return SentenceTransformer(model_name)


@lru_cache(maxsize=512)
def embed_text(text: str, *, model_name: str = DEFAULT_MODEL_NAME) -> Any:
    """Return a normalized embedding vector for `text`. Cached by (text,
    model_name) so repeatedly embedding the same JD across a batch of
    resumes is free after the first call."""
    model = _get_model(model_name)
    return model.encode(text, normalize_embeddings=True)


def cosine_similarity(vec_a: Any, vec_b: Any) -> float:
    """Both vectors must already be normalized (see `embed_text`), so this
    is just a dot product, clamped to [0, 1] for use as a match score."""
    score = float(vec_a @ vec_b)
    return max(0.0, min(1.0, score))
