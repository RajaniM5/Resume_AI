"""Shared, optional spaCy access.

Per docs/ARCHITECTURE.md this pipeline is a rules+ML hybrid: regex/heuristics
carry the deterministic extraction (contact info, dates, skills-by-gazetteer)
and spaCy NER is used only to refine ambiguous fields (person names, org
names). If the `en_core_web_sm` model isn't installed, callers fall back to
heuristics alone rather than failing - this keeps the pipeline usable before
the model is downloaded and keeps unit tests independent of the ~500MB model.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def get_nlp() -> Any | None:
    """Return a loaded spaCy pipeline, or None if unavailable."""
    try:
        import spacy
    except ImportError:
        return None

    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        return None
