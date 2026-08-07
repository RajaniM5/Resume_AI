"""Split resume/JD text into labeled sections by heading line."""
from __future__ import annotations

import re

# canonical section name -> heading text variants that map to it
_SECTION_HEADINGS: dict[str, list[str]] = {
    "summary": ["summary", "professional summary", "objective", "profile"],
    "skills": ["skills", "technical skills", "core competencies", "competencies"],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
    ],
    "education": ["education", "academic background"],
    "certifications": ["certifications", "certification", "licenses & certifications"],
    "projects": ["projects", "personal projects"],
}
# job-description-specific headings (distinct enough from resume headings
# that they're kept separate rather than merged into one big map)
JD_SECTION_HEADINGS: dict[str, list[str]] = {
    "responsibilities": ["responsibilities", "what you'll do", "the role", "duties"],
    "requirements": [
        "requirements",
        "qualifications",
        "required qualifications",
        "minimum qualifications",
        "what you'll need",
        "you have",
    ],
    "preferred": [
        "preferred qualifications",
        "nice to have",
        "nice-to-have",
        "bonus points",
        "preferred",
    ],
}

_HEADING_TO_SECTION = {
    heading: section for section, headings in _SECTION_HEADINGS.items() for heading in headings
}
# A heading line is short, has no sentence punctuation, and its normalized
# text is a known heading (case/spacing/trailing-colon insensitive).
_MAX_HEADING_LEN = 40


def _normalize_heading(line: str, heading_map: dict[str, str]) -> str | None:
    stripped = line.strip().rstrip(":").strip()
    if not stripped or len(stripped) > _MAX_HEADING_LEN:
        return None
    if re.search(r"[.!?]", stripped):
        return None
    return heading_map.get(stripped.lower())


def split_sections(text: str, *, section_headings: dict[str, list[str]] | None = None) -> dict[str, str]:
    """Return {section_name: body_text}. Text before the first recognized
    heading is returned under "header" (name/contact info usually lives
    there). Pass `section_headings` (canonical -> variants) to use a
    different heading vocabulary, e.g. JD_SECTION_HEADINGS."""
    heading_map = (
        _HEADING_TO_SECTION
        if section_headings is None
        else {h: s for s, hs in section_headings.items() for h in hs}
    )
    lines = text.splitlines()
    sections: dict[str, list[str]] = {"header": []}
    current = "header"

    for line in lines:
        section = _normalize_heading(line, heading_map)
        if section is not None:
            current = section
            sections.setdefault(current, [])
            continue
        sections[current].append(line)

    return {name: "\n".join(body_lines).strip() for name, body_lines in sections.items()}


def split_into_blocks(section_text: str) -> list[list[str]]:
    """Split a section body into blank-line-separated entry blocks, dropping
    empty lines within/around each block."""
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in section_text.splitlines():
        if line.strip():
            current.append(line.strip())
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks
