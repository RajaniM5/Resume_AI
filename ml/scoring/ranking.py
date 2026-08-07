"""Combine matching signals into a single candidate score with
explainability, per docs/SCOPE.md ("each score returns the top contributing
factors") and the audit-logging requirement in docs/ARCHITECTURE.md (every
score is tagged with a model version so past decisions stay reproducible).
"""
from __future__ import annotations

from ml.matching.scoring import semantic_similarity, skill_gap
from ml.parsing.degree import find_required_degree_rank, highest_degree_rank
from ml.schemas import CandidateScore, ParsedJobDescription, ParsedResume, ScoreFactor, SkillGap

MODEL_VERSION = "ranking-v1"

SEMANTIC_WEIGHT = 0.40
SKILL_WEIGHT = 0.35
EXPERIENCE_WEIGHT = 0.15
EDUCATION_WEIGHT = 0.10


def score_candidate(
    resume: ParsedResume, jd: ParsedJobDescription, *, resume_id: str | None = None
) -> CandidateScore:
    semantic = semantic_similarity(resume, jd)
    gap = skill_gap(resume, jd)
    skill_score = gap.coverage
    experience_fit = _experience_fit(resume, jd)
    education_fit = _education_fit(resume, jd)

    overall = 100 * (
        semantic * SEMANTIC_WEIGHT
        + skill_score * SKILL_WEIGHT
        + experience_fit * EXPERIENCE_WEIGHT
        + education_fit * EDUCATION_WEIGHT
    )

    factors = [
        ScoreFactor(
            name="semantic_similarity",
            weight=SEMANTIC_WEIGHT,
            value=semantic,
            detail=f"Resume/JD text similarity: {semantic:.0%}.",
        ),
        ScoreFactor(
            name="skill_match",
            weight=SKILL_WEIGHT,
            value=skill_score,
            detail=_skill_detail(gap),
        ),
        ScoreFactor(
            name="experience_fit",
            weight=EXPERIENCE_WEIGHT,
            value=experience_fit,
            detail=_experience_detail(resume, jd),
        ),
        ScoreFactor(
            name="education_fit",
            weight=EDUCATION_WEIGHT,
            value=education_fit,
            detail=_education_detail(resume, jd),
        ),
    ]
    # Largest weighted contribution first, so an HR reviewer / API consumer
    # sees what actually drove the score without re-deriving it.
    factors.sort(key=lambda f: f.weight * f.value, reverse=True)

    return CandidateScore(
        resume_id=resume_id,
        overall_score=round(overall, 2),
        semantic_similarity=round(semantic, 4),
        skill_gap=gap,
        experience_fit=round(experience_fit, 4),
        education_fit=round(education_fit, 4),
        factors=factors,
        model_version=MODEL_VERSION,
    )


def _experience_fit(resume: ParsedResume, jd: ParsedJobDescription) -> float:
    if not jd.min_experience_years or jd.min_experience_years <= 0:
        return 1.0
    return max(0.0, min(resume.total_experience_years / jd.min_experience_years, 1.0))


def _education_fit(resume: ParsedResume, jd: ParsedJobDescription) -> float:
    required_rank = find_required_degree_rank(jd.raw_text)
    if required_rank == 0:
        return 1.0
    candidate_rank = highest_degree_rank([e.degree for e in resume.education if e.degree])
    if candidate_rank == 0:
        return 0.0
    return 1.0 if candidate_rank >= required_rank else 0.5


def _skill_detail(gap: SkillGap) -> str:
    if not gap.matched_skills and not gap.missing_skills:
        return "No required skills were extracted from the JD to compare against."
    matched = ", ".join(gap.matched_skills) or "none"
    missing = ", ".join(gap.missing_skills) or "none"
    return f"Matched: {matched}. Missing: {missing}."


def _experience_detail(resume: ParsedResume, jd: ParsedJobDescription) -> str:
    if not jd.min_experience_years or jd.min_experience_years <= 0:
        return "JD did not specify a minimum years-of-experience requirement."
    return (
        f"{resume.total_experience_years:.1f} yrs of extracted experience "
        f"vs {jd.min_experience_years:.0f}+ yrs required."
    )


def _education_detail(resume: ParsedResume, jd: ParsedJobDescription) -> str:
    required_rank = find_required_degree_rank(jd.raw_text)
    if required_rank == 0:
        return "JD did not specify a degree requirement."
    candidate_rank = highest_degree_rank([e.degree for e in resume.education if e.degree])
    if candidate_rank == 0:
        return "JD requires a degree; none was found on the resume."
    return f"Highest degree rank {candidate_rank} vs required rank {required_rank} (higher is more advanced)."
