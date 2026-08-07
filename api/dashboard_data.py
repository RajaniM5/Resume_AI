"""Sample-data loader for the HR admin dashboard (docs/UI_DESIGN.md phase 1).

Reads static fixtures from data/sample/dashboard.json instead of the database —
there is no scoring/candidate API yet (see TASKS.md P1/P2). Swap this module
for real DB-backed queries once those endpoints exist; the route layer should
not need to change shape.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample" / "dashboard.json"


@lru_cache
def _load() -> dict[str, Any]:
    with DATA_PATH.open() as f:
        return json.load(f)


def list_job_reqs() -> list[dict[str, Any]]:
    data = _load()
    counts: dict[str, int] = {}
    for c in data["candidates"]:
        counts[c["job_req_id"]] = counts.get(c["job_req_id"], 0) + 1
    reqs = []
    for req in data["job_reqs"]:
        reqs.append({**req, "candidate_count": counts.get(req["id"], 0)})
    return reqs


def get_job_req(job_req_id: str) -> dict[str, Any] | None:
    return next((r for r in _load()["job_reqs"] if r["id"] == job_req_id), None)


def list_candidates(job_req_id: str) -> list[dict[str, Any]]:
    candidates = [c for c in _load()["candidates"] if c["job_req_id"] == job_req_id]
    return sorted(candidates, key=lambda c: c["score"], reverse=True)


def get_candidate(candidate_id: str) -> dict[str, Any] | None:
    return next((c for c in _load()["candidates"] if c["id"] == candidate_id), None)


def override_candidate(candidate_id: str, reason: str) -> None:
    """Mutate the in-process cache and append an audit entry.

    In-memory only — process restart resets it. A real implementation
    writes to Postgres per the audit logging requirement in TASKS.md P3.
    """
    from datetime import datetime, timezone

    data = _load()
    candidate = next((c for c in data["candidates"] if c["id"] == candidate_id), None)
    if candidate is None:
        return
    candidate["status"] = "overridden"
    candidate["override_reason"] = reason
    data["audit_log"].append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate_id": candidate_id,
            "action": "override",
            "actor": "hr-reviewer:demo-user",
            "model_version": "matcher-v0.3.1",
            "reason": reason,
        }
    )


def list_audit_log(candidate_id: str | None = None) -> list[dict[str, Any]]:
    entries = _load()["audit_log"]
    if candidate_id:
        entries = [e for e in entries if e["candidate_id"] == candidate_id]
    candidates_by_id = {c["id"]: c for c in _load()["candidates"]}
    enriched = []
    for e in sorted(entries, key=lambda e: e["timestamp"], reverse=True):
        candidate = candidates_by_id.get(e["candidate_id"])
        enriched.append({**e, "candidate_name": candidate["name"] if candidate else e["candidate_id"]})
    return enriched
