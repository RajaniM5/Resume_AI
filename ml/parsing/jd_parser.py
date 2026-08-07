"""Structured extraction from job description text: required/preferred
skills, minimum experience, and qualification bullet points."""
from __future__ import annotations

import re

from ml.parsing.sections import JD_SECTION_HEADINGS, split_into_blocks, split_sections
from ml.parsing.skills_taxonomy import extract_skills
from ml.schemas import ParsedJobDescription

_EXPERIENCE_YEARS_RE = re.compile(
    r"(\d+)\+?\s*(?:-\s*\d+\s*)?years?(?:\s+of)?(?:\s+experience)?", re.IGNORECASE
)
_BULLET_RE = re.compile(r"^[-•*]\s*")
_MAX_TITLE_LEN = 80


def parse_job_description(text: str) -> ParsedJobDescription:
    body = split_sections(text, section_headings=JD_SECTION_HEADINGS)

    requirements_text = body.get("requirements", "")
    preferred_text = body.get("preferred", "")
    # Skills mentioned in responsibilities/header count toward "required"
    # too - JDs often list stack in a "What you'll do" blurb, not just Reqs.
    required_text = "\n".join(
        part
        for part in (body.get("header", ""), body.get("responsibilities", ""), requirements_text)
        if part
    ) or text

    required_skills = extract_skills(required_text)
    preferred_skills = [s for s in extract_skills(preferred_text) if s not in required_skills]

    return ParsedJobDescription(
        raw_text=text,
        title=_extract_title(body.get("header", text)),
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        min_experience_years=_extract_min_experience(text),
        qualifications=_extract_qualifications(requirements_text),
    )


def _extract_title(header_text: str) -> str | None:
    for line in header_text.splitlines():
        stripped = line.strip()
        if stripped and len(stripped) <= _MAX_TITLE_LEN and not re.search(r"[.!?]", stripped):
            return stripped
    return None


def _extract_min_experience(text: str) -> float | None:
    matches = _EXPERIENCE_YEARS_RE.findall(text)
    if not matches:
        return None
    return float(min(int(m) for m in matches))


def _extract_qualifications(requirements_text: str) -> list[str]:
    qualifications: list[str] = []
    for block in split_into_blocks(requirements_text):
        for line in block:
            if _BULLET_RE.match(line):
                qualifications.append(_BULLET_RE.sub("", line).strip())
    return qualifications
