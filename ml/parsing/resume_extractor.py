"""Structured information extraction from resume text.

Rules+ML hybrid: regex/heuristics do the deterministic work (contact info,
date ranges, section layout); spaCy NER (when available) refines the
candidate's name. See ml/parsing/nlp_utils.py for the fallback behavior when
spaCy isn't installed.
"""
from __future__ import annotations

import re
from typing import Any

from ml.parsing import sections
from ml.parsing.degree import DEGREE_RE
from ml.parsing.nlp_utils import get_nlp
from ml.parsing.skills_taxonomy import extract_skills
from ml.schemas import ContactInfo, Education, Experience, ParsedResume

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"
)
_LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", re.IGNORECASE)

_MONTHS = {
    name: i
    for i, name in enumerate(
        [
            "jan", "feb", "mar", "apr", "may", "jun",
            "jul", "aug", "sep", "oct", "nov", "dec",
        ],
        start=1,
    )
}
_MONTH_RE = "|".join(_MONTHS.keys())
_DATE_RANGE_RE = re.compile(
    rf"(?:(?P<start_month>{_MONTH_RE})[a-z]*\.?\s+)?(?P<start_year>\d{{4}})"
    rf"\s*(?:-|–|—|to)\s*"
    rf"(?:(?P<end_month>{_MONTH_RE})[a-z]*\.?\s+)?(?P<end_year>\d{{4}}|present|current)",
    re.IGNORECASE,
)
_INSTITUTION_RE = re.compile(
    r"[A-Z][\w&.,' -]*\b(?:University|College|Institute|Polytechnic|School)\b[\w&.,' -]*"
)
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
_BULLET_RE = re.compile(r"^[-•*•]\s*")


def extract_resume(text: str, *, nlp: Any | None = None) -> ParsedResume:
    body = sections.split_sections(text)
    nlp = nlp if nlp is not None else get_nlp()

    contact = _extract_contact(body.get("header", text), nlp=nlp)
    skills_text = body.get("skills") or text
    skills = extract_skills(skills_text)
    if "skills" not in body:
        # No dedicated skills section: also scan summary/experience so
        # inline mentions ("Built APIs in Python") still count.
        skills = extract_skills(text)

    experience = _extract_experience(body.get("experience", ""))
    education = _extract_education(body.get("education", ""))
    certifications = _extract_certifications(body.get("certifications", ""))

    return ParsedResume(
        raw_text=text,
        contact=contact,
        skills=skills,
        experience=experience,
        education=education,
        certifications=certifications,
        total_experience_years=round(sum(e.duration_years for e in experience), 2),
    )


def _extract_contact(header_text: str, *, nlp: Any | None) -> ContactInfo:
    email_match = _EMAIL_RE.search(header_text)
    phone_match = _PHONE_RE.search(header_text)
    linkedin_match = _LINKEDIN_RE.search(header_text)

    return ContactInfo(
        name=_extract_name(header_text, nlp=nlp),
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        linkedin=linkedin_match.group(0) if linkedin_match else None,
    )


def _extract_name(header_text: str, *, nlp: Any | None) -> str | None:
    lines = [line.strip() for line in header_text.splitlines() if line.strip()]
    if not lines:
        return None

    # Heuristic primary: the first line is conventionally the candidate's
    # name if it's short, has no digits/@ and looks like "Word Word[ Word]".
    first_line = lines[0]
    if (
        "@" not in first_line
        and not any(ch.isdigit() for ch in first_line)
        and 1 <= len(first_line.split()) <= 4
        and len(first_line) <= 60
    ):
        heuristic_name = first_line
    else:
        heuristic_name = None

    if nlp is not None:
        doc = nlp("\n".join(lines[:3]))
        person_ents = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        if person_ents:
            return person_ents[0]

    return heuristic_name


def _parse_date_range(line: str) -> tuple[int | None, int | None, bool, float]:
    match = _DATE_RANGE_RE.search(line)
    if not match:
        return None, None, False, 0.0

    start_year = int(match.group("start_year"))
    start_month = _MONTHS.get((match.group("start_month") or "jan")[:3].lower(), 1)

    end_raw = match.group("end_year").lower()
    is_current = end_raw in ("present", "current")
    if is_current:
        import datetime

        end_year = datetime.date.today().year
        end_month = datetime.date.today().month
    else:
        end_year = int(end_raw)
        end_month = _MONTHS.get((match.group("end_month") or "dec")[:3].lower(), 12)

    months = (end_year * 12 + end_month) - (start_year * 12 + start_month)
    duration_years = max(round(months / 12, 2), 0.0)
    return start_year, end_year, is_current, duration_years


def _extract_experience(section_text: str) -> list[Experience]:
    entries: list[Experience] = []
    for block in sections.split_into_blocks(section_text):
        date_line_idx = next(
            (i for i, line in enumerate(block) if _DATE_RANGE_RE.search(line)), None
        )
        if date_line_idx is None:
            continue

        start_year, end_year, is_current, duration = _parse_date_range(block[date_line_idx])
        header_line = block[0] if date_line_idx != 0 else (block[1] if len(block) > 1 else "")

        title, organization = _split_title_org(header_line)
        entries.append(
            Experience(
                title=title,
                organization=organization,
                start_year=start_year,
                end_year=end_year,
                is_current=is_current,
                duration_years=duration,
                raw_text="\n".join(block),
            )
        )
    return entries


def _split_title_org(header_line: str) -> tuple[str | None, str | None]:
    if not header_line:
        return None, None
    for sep in (",", " at ", " – ", " - ", "|"):
        if sep in header_line:
            title, _, org = header_line.partition(sep)
            return title.strip() or None, org.strip() or None
    return header_line.strip() or None, None


def _extract_education(section_text: str) -> list[Education]:
    entries: list[Education] = []
    for block in sections.split_into_blocks(section_text):
        block_text = " ".join(block)
        degree_match = DEGREE_RE.search(block_text)
        institution_match = _INSTITUTION_RE.search(block_text)
        year_matches = _YEAR_RE.findall(block_text)

        if not degree_match and not institution_match:
            continue

        entries.append(
            Education(
                institution=institution_match.group(0).strip() if institution_match else None,
                degree=degree_match.group(1).strip() if degree_match else None,
                field_of_study=degree_match.group(2).strip() if degree_match and degree_match.group(2) else None,
                graduation_year=int(_YEAR_RE.search(block_text).group(0)) if year_matches else None,
                raw_text="\n".join(block),
            )
        )
    return entries


def _extract_certifications(section_text: str) -> list[str]:
    return [
        _BULLET_RE.sub("", line).strip()
        for line in section_text.splitlines()
        if line.strip()
    ]
