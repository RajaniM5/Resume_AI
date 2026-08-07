# Training & Evaluation Data Requirements

No proprietary resume/hiring data exists in this repo yet. This document defines what's needed before the P1 model work can start, and how to bootstrap in the meantime.

## What's needed
1. **Resume corpus** — anonymized resumes (PDF/DOCX), ideally spanning multiple roles/seniority levels.
2. **Job descriptions** — matched to the roles the resumes were originally submitted for.
3. **Labels** — historical HR outcome per resume/JD pair: shortlisted / rejected at screening stage (minimum), interview/hire outcome (ideal, enables stronger eval).
4. **Demographic proxy fields for fairness eval only** (never used as model features) — e.g., name, school, gap periods — needed to run the bias audit in [ARCHITECTURE.md](ARCHITECTURE.md#governance--compliance-hooks-see-tasksmd-p3), collected/handled per applicable privacy law.

## Sourcing options
- **Preferred**: pull anonymized historical data from the org's existing ATS (requires legal/privacy sign-off — flag to stakeholder before starting P1).
- **Bootstrap/prototyping only**: public resume datasets (e.g., Kaggle "Resume Dataset") can validate the parsing/extraction pipeline shape, but have no HR outcome labels and should never be used for the fairness audit or final model evaluation — they're for plumbing tests only.

## Schema (draft — refine once real data is sourced)
```
resumes/
  resume_id, raw_file_ref, extracted_text, parsed_json, submitted_for_job_id, submitted_at

job_descriptions/
  job_id, title, raw_text, parsed_requirements_json, created_at

labels/
  resume_id, job_id, screened_outcome (shortlisted|rejected), interview_outcome (nullable), hire_outcome (nullable), decided_at
```

## Data directory convention
- `data/raw/` — untouched source files (gitignored — never commit real resumes/PII to the repo)
- `data/processed/` — parsed/anonymized intermediate artifacts (gitignored)
- `data/sample/` — small, synthetic, non-PII fixtures for tests (safe to commit)

## Status
- [ ] Legal/privacy sign-off obtained for using historical ATS data
- [ ] Real dataset sourced and schema-mapped
- [ ] Synthetic sample fixtures created for `data/sample/` (unblocks P1 dev before real data lands)
