"""Maps Workday Recruiting candidate payloads to our internal resume format.

Workday's recruiting API schema is tenant-customized (field names vary by
customer configuration), so this is a best-effort generic mapping rather than
a byte-exact spec implementation. It expects the caller's Workday integration
to have already normalized the payload to roughly:

    {
        "candidateId": "C-12345",
        "resumeAttachment": {"fileName": "resume.docx", "fileContentBase64": "..."}
    }

Adjust the field lookups below to match the actual tenant's payload shape
before relying on this in production.
"""

from __future__ import annotations

from typing import Any


class MissingResumeAttachment(ValueError):
    pass


def from_workday_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    candidate_id = payload.get("candidateId") or payload.get("candidate_id")
    attachment = payload.get("resumeAttachment") or payload.get("resume_attachment")

    if not attachment:
        raise MissingResumeAttachment("candidate payload has no resume attachment")

    filename = attachment.get("fileName") or attachment.get("filename")
    content_base64 = attachment.get("fileContentBase64") or attachment.get("content_base64")
    if not filename or not content_base64:
        raise MissingResumeAttachment("resume attachment missing filename or base64 content")

    return {
        "candidate_id": str(candidate_id) if candidate_id else None,
        "filename": filename,
        "content_base64": content_base64,
    }
