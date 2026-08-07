"""Shared data structures for the parsing -> matching -> scoring pipeline.

Kept framework-agnostic (plain pydantic models, no FastAPI/SQLAlchemy
imports) so `ml/` stays testable in isolation, per docs/ARCHITECTURE.md.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None


class Education(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    graduation_year: int | None = None
    raw_text: str


class Experience(BaseModel):
    title: str | None = None
    organization: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    is_current: bool = False
    duration_years: float = 0.0
    raw_text: str


class ParsedResume(BaseModel):
    raw_text: str
    contact: ContactInfo = Field(default_factory=ContactInfo)
    skills: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    total_experience_years: float = 0.0
    used_ocr: bool = False


class ParsedJobDescription(BaseModel):
    raw_text: str
    title: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_experience_years: float | None = None
    qualifications: list[str] = Field(default_factory=list)


class SkillGap(BaseModel):
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    extra_skills: list[str] = Field(default_factory=list)

    @property
    def coverage(self) -> float:
        """Fraction of required skills the candidate has (0-1)."""
        total = len(self.matched_skills) + len(self.missing_skills)
        return len(self.matched_skills) / total if total else 1.0


class ScoreFactor(BaseModel):
    name: str
    weight: float
    value: float  # normalized 0-1 contribution before weighting
    detail: str


class CandidateScore(BaseModel):
    resume_id: str | None = None
    overall_score: float  # 0-100
    semantic_similarity: float  # 0-1
    skill_gap: SkillGap
    experience_fit: float  # 0-1
    education_fit: float  # 0-1
    factors: list[ScoreFactor] = Field(default_factory=list)
    model_version: str
