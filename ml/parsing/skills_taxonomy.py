"""Skill gazetteer used for keyword-based skill extraction.

MVP approach per docs/ARCHITECTURE.md: a curated skill list matched against
resume/JD text, rather than a trained NER model (no labeled skill-span
training data exists yet — see docs/DATA.md). Swap for a trained model once
labeled data is available; callers only depend on `extract_skills`, not on
the taxonomy shape.
"""
from __future__ import annotations

import re

# Canonical skill name -> alternate surface forms found in resumes/JDs.
# Canonical names are what downstream matching/scoring code compares against.
SKILL_SYNONYMS: dict[str, list[str]] = {
    "python": ["python", "python3"],
    "java": ["java"],
    "javascript": ["javascript", "js", "es6"],
    "typescript": ["typescript", "ts"],
    "c++": ["c++", "cpp"],
    "c#": ["c#", "csharp"],
    "go": ["golang", "go lang"],
    "sql": ["sql"],
    "r": ["r programming"],
    "react": ["react", "react.js", "reactjs"],
    "angular": ["angular", "angular.js", "angularjs"],
    "vue": ["vue", "vue.js", "vuejs"],
    "node.js": ["node.js", "node", "nodejs"],
    "django": ["django"],
    "flask": ["flask"],
    "fastapi": ["fastapi"],
    "spring": ["spring", "spring boot"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "terraform": ["terraform"],
    "ci/cd": ["ci/cd", "continuous integration", "continuous deployment"],
    "git": ["git"],
    "linux": ["linux"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "elasticsearch": ["elasticsearch"],
    "kafka": ["kafka", "apache kafka"],
    "spark": ["spark", "apache spark"],
    "hadoop": ["hadoop"],
    "airflow": ["airflow", "apache airflow"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning"],
    "nlp": ["nlp", "natural language processing"],
    "computer vision": ["computer vision", "cv"],
    "pytorch": ["pytorch"],
    "tensorflow": ["tensorflow"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "tableau": ["tableau"],
    "power bi": ["power bi", "powerbi"],
    "excel": ["excel", "microsoft excel"],
    "salesforce": ["salesforce"],
    "sap": ["sap"],
    "jira": ["jira"],
    "agile": ["agile"],
    "scrum": ["scrum"],
    "project management": ["project management"],
    "product management": ["product management"],
    "data analysis": ["data analysis"],
    "data engineering": ["data engineering"],
    "rest api": ["rest api", "restful api", "rest apis"],
    "graphql": ["graphql"],
    "microservices": ["microservices"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "communication": ["communication skills", "communication"],
    "leadership": ["leadership"],
    "public speaking": ["public speaking"],
    "financial modeling": ["financial modeling"],
    "accounting": ["accounting"],
    "negotiation": ["negotiation"],
    "customer service": ["customer service"],
    "sales": ["sales"],
    "marketing": ["marketing"],
    "seo": ["seo", "search engine optimization"],
    "content writing": ["content writing", "copywriting"],
}


def _build_pattern() -> re.Pattern[str]:
    surface_to_canonical: list[tuple[str, str]] = [
        (surface, canonical)
        for canonical, surfaces in SKILL_SYNONYMS.items()
        for surface in surfaces
    ]
    # Longest surface forms first so e.g. "react.js" wins over a bare "react"
    # match inside the same span, and word-boundary each alternative.
    surface_to_canonical.sort(key=lambda pair: len(pair[0]), reverse=True)
    alternation = "|".join(re.escape(surface) for surface, _ in surface_to_canonical)
    return re.compile(rf"(?<![\w+#.]){alternation}(?![\w+#])", re.IGNORECASE)


_SURFACE_TO_CANONICAL = {
    surface.lower(): canonical
    for canonical, surfaces in SKILL_SYNONYMS.items()
    for surface in surfaces
}
_SKILL_PATTERN = _build_pattern()


def extract_skills(text: str) -> list[str]:
    """Return canonical skill names found in `text`, in first-seen order."""
    seen: dict[str, None] = {}
    for match in _SKILL_PATTERN.finditer(text):
        canonical = _SURFACE_TO_CANONICAL[match.group(0).lower()]
        seen.setdefault(canonical, None)
    return list(seen.keys())
