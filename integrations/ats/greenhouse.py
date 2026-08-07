"""Maps Greenhouse Harvest API candidate objects to our internal resume format.

Reference shape (Greenhouse "Candidate" object, trimmed to the fields we use):
    {
        "id": 12345,
        "first_name": "Jane",
        "last_name": "Doe",
        "attachments": [
            {"filename": "resume.pdf", "type": "resume", "content_base64": "..."}
        ]
    }

Greenhouse's actual API returns attachments as a signed `url` to fetch, not
inline content — fetching that URL is left to the caller (keeps this module
free of network calls / auth-token plumbing). If `content_base64` is already
present (e.g. pre-fetched by the caller), it's used directly.
"""

from __future__ import annotations

from typing import Any


class MissingResumeAttachment(ValueError):
    pass


def from_greenhouse_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(payload.get("id", "")) or None
    attachments = payload.get("attachments") or []
    resume_attachment = next((a for a in attachments if a.get("type") == "resume"), None)

    if resume_attachment is None:
        raise MissingResumeAttachment("candidate has no attachment of type 'resume'")
    if "content_base64" not in resume_attachment:
        raise MissingResumeAttachment(
            "attachment has no inline content_base64 — fetch its 'url' and re-attach before mapping"
        )

    return {
        "candidate_id": candidate_id,
        "filename": resume_attachment.get("filename", "resume.pdf"),
        "content_base64": resume_attachment["content_base64"],
    }
