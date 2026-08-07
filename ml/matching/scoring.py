"""Resume <-> JD matching: semantic similarity and skill-gap scoring."""
from __future__ import annotations

from ml.matching.embeddings import cosine_similarity, embed_text
from ml.schemas import ParsedJobDescription, ParsedResume, SkillGap


def semantic_similarity(resume: ParsedResume, jd: ParsedJobDescription) -> float:
    """Cosine similarity between resume and JD text embeddings, in [0, 1]."""
    resume_vec = embed_text(resume.raw_text)
    jd_vec = embed_text(jd.raw_text)
    return cosine_similarity(resume_vec, jd_vec)


def skill_gap(resume: ParsedResume, jd: ParsedJobDescription) -> SkillGap:
    """Compare extracted resume skills against JD required skills."""
    resume_skills = set(resume.skills)
    required_skills = set(jd.required_skills)

    return SkillGap(
        matched_skills=sorted(resume_skills & required_skills),
        missing_skills=sorted(required_skills - resume_skills),
        extra_skills=sorted(resume_skills - required_skills),
    )
