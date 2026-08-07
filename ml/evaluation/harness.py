"""Offline evaluation of the scoring pipeline against labeled HR outcomes.

Per TASKS.md P1 ("Model evaluation harness: precision/recall against labeled
dataset, baseline comparison") and the ranking-quality success metric in
docs/SCOPE.md. Labels follow the `labels/` schema sketched in docs/DATA.md:
a screened_outcome of shortlisted/rejected per (resume, job) pair. Until real
labeled ATS data is sourced (see docs/DATA.md Status), this harness runs
against the synthetic fixtures in data/sample/ - useful for validating the
pipeline's shape, not for real accuracy/fairness claims (see docs/DATA.md).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from ml.matching.scoring import skill_gap
from ml.schemas import ParsedJobDescription, ParsedResume

ScoreFn = Callable[[ParsedResume, ParsedJobDescription], float]


@dataclass
class LabeledExample:
    resume: ParsedResume
    jd: ParsedJobDescription
    shortlisted: bool
    job_id: str = "default"
    resume_id: str | None = None


@dataclass
class EvalResult:
    precision: float
    recall: float
    f1: float
    n: int
    n_positive: int
    n_predicted_positive: int


def _precision_recall_f1(y_true: list[bool], y_pred: list[bool]) -> tuple[float, float, float]:
    tp = sum(t and p for t, p in zip(y_true, y_pred))
    fp = sum((not t) and p for t, p in zip(y_true, y_pred))
    fn = sum(t and (not p) for t, p in zip(y_true, y_pred))
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def evaluate(
    examples: list[LabeledExample], score_fn: ScoreFn, *, threshold: float = 50.0
) -> EvalResult:
    """Precision/recall/F1 of a shortlist decision (score >= threshold)
    against HR's actual screened_outcome labels."""
    if not examples:
        return EvalResult(precision=0.0, recall=0.0, f1=0.0, n=0, n_positive=0, n_predicted_positive=0)

    y_true = [ex.shortlisted for ex in examples]
    y_pred = [score_fn(ex.resume, ex.jd) >= threshold for ex in examples]
    precision, recall, f1 = _precision_recall_f1(y_true, y_pred)
    return EvalResult(
        precision=precision,
        recall=recall,
        f1=f1,
        n=len(examples),
        n_positive=sum(y_true),
        n_predicted_positive=sum(y_pred),
    )


def recall_at_top_k_percent(
    examples: list[LabeledExample], score_fn: ScoreFn, *, k_percent: float = 20.0
) -> float:
    """Fraction of HR-shortlisted candidates captured within the top
    k_percent of the ranking, computed per job_id (candidates only compete
    against others screened for the same req, then averaged). Mirrors the
    docs/SCOPE.md ranking-quality target: "top-20% model ranking captures
    >=90% of candidates HR would have manually shortlisted"."""
    by_job: dict[str, list[LabeledExample]] = {}
    for ex in examples:
        by_job.setdefault(ex.job_id, []).append(ex)

    total_positive = 0
    total_captured = 0
    for job_examples in by_job.values():
        ranked = sorted(job_examples, key=lambda ex: score_fn(ex.resume, ex.jd), reverse=True)
        cutoff = max(1, round(len(ranked) * k_percent / 100))
        top = ranked[:cutoff]
        total_positive += sum(ex.shortlisted for ex in job_examples)
        total_captured += sum(ex.shortlisted for ex in top)

    return total_captured / total_positive if total_positive else 0.0


def keyword_overlap_baseline(resume: ParsedResume, jd: ParsedJobDescription) -> float:
    """Naive baseline: percent of JD-required skills present on the resume,
    ignoring semantic similarity/experience/education entirely. Used to
    check the full ranking model (ml/scoring/ranking.py) actually earns its
    added complexity over a trivial keyword match."""
    return 100 * skill_gap(resume, jd).coverage


def random_baseline(seed: int = 0) -> ScoreFn:
    """A scoring function that ignores its inputs; the floor any real model
    must beat."""
    rng = random.Random(seed)
    return lambda resume, jd: rng.uniform(0, 100)


def compare_to_baselines(
    examples: list[LabeledExample], model_score_fn: ScoreFn, *, threshold: float = 50.0
) -> dict[str, EvalResult]:
    return {
        "model": evaluate(examples, model_score_fn, threshold=threshold),
        "keyword_overlap_baseline": evaluate(examples, keyword_overlap_baseline, threshold=threshold),
        "random_baseline": evaluate(examples, random_baseline(), threshold=threshold),
    }
