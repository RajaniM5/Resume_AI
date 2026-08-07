"""Degree detection + ranking, shared by resume extraction and education-fit
scoring (ml/scoring/ranking.py)."""
from __future__ import annotations

import re

DEGREE_RE = re.compile(
    r"(Ph\.?D\.?|Doctorate|Master'?s?|M\.?S\.?|M\.?A\.?|M\.?B\.?A\.?|"
    r"Bachelor'?s?|B\.?S\.?|B\.?A\.?|Associate'?s?)"
    r"(?:\s+(?:of|in|degree in)\s+([A-Za-z][A-Za-z &,]*?))?(?=[,\n]|$)",
    re.IGNORECASE,
)


def degree_rank(degree_text: str) -> int:
    """Coarse seniority rank for a degree string, 0 (unrecognized) to 4 (PhD)."""
    normalized = re.sub(r"[.\s']", "", degree_text).lower()
    if normalized in ("phd", "doctorate"):
        return 4
    if normalized in ("mba", "ms", "ma") or normalized.startswith("master"):
        return 3
    if normalized in ("bs", "ba") or normalized.startswith("bachelor"):
        return 2
    if normalized.startswith("associate"):
        return 1
    return 0


def highest_degree_rank(degrees: list[str]) -> int:
    return max((degree_rank(d) for d in degrees), default=0)


def find_required_degree_rank(text: str) -> int:
    """Look for the first degree mention in JD text and rank it. Returns 0
    if the JD doesn't mention a degree requirement."""
    match = DEGREE_RE.search(text)
    return degree_rank(match.group(1)) if match else 0
