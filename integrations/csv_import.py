"""Bulk resume import from CSV.

Accepts two column layouts, so HR teams can export plain-text resumes
straight from a spreadsheet without hand-encoding files:

- `candidate_id, filename, content_base64` — pre-encoded files, passed through.
- `candidate_id, resume_text`              — plain text, wrapped into a .txt "file".

Output is a list of dicts shaped like `ResumeFile` (api/schemas.py), ready to
drop into a `BatchScreeningRequest.resumes` payload.
"""

from __future__ import annotations

import base64
import csv
import io
from typing import Any


class InvalidCsvFormat(ValueError):
    pass


def parse_bulk_csv(csv_bytes: bytes) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")))
    if reader.fieldnames is None:
        raise InvalidCsvFormat("CSV has no header row")

    fields = set(reader.fieldnames)
    has_encoded = {"filename", "content_base64"} <= fields
    has_plain_text = "resume_text" in fields
    if not (has_encoded or has_plain_text):
        raise InvalidCsvFormat(
            "CSV must have either 'filename'+'content_base64' columns or a 'resume_text' column"
        )

    resumes: list[dict[str, Any]] = []
    for row_num, row in enumerate(reader, start=2):  # header is row 1
        candidate_id = (row.get("candidate_id") or "").strip() or None

        if has_encoded:
            filename = (row.get("filename") or "").strip()
            content_base64 = (row.get("content_base64") or "").strip()
            if not filename or not content_base64:
                raise InvalidCsvFormat(f"row {row_num}: filename/content_base64 required")
        else:
            resume_text = row.get("resume_text") or ""
            if not resume_text.strip():
                raise InvalidCsvFormat(f"row {row_num}: resume_text is empty")
            filename = f"{candidate_id or f'row-{row_num}'}.txt"
            content_base64 = base64.b64encode(resume_text.encode("utf-8")).decode("ascii")

        resumes.append({"candidate_id": candidate_id, "filename": filename, "content_base64": content_base64})

    return resumes
