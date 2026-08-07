import base64

import pytest

from integrations.csv_import import InvalidCsvFormat, parse_bulk_csv


def test_parse_encoded_columns() -> None:
    csv_bytes = b"candidate_id,filename,content_base64\ncand-1,a.pdf,YWJj\n"
    resumes = parse_bulk_csv(csv_bytes)
    assert resumes == [{"candidate_id": "cand-1", "filename": "a.pdf", "content_base64": "YWJj"}]


def test_parse_plain_text_column() -> None:
    csv_bytes = b"candidate_id,resume_text\ncand-1,Python developer with AWS experience\n"
    resumes = parse_bulk_csv(csv_bytes)
    assert len(resumes) == 1
    assert resumes[0]["candidate_id"] == "cand-1"
    assert resumes[0]["filename"] == "cand-1.txt"
    decoded = base64.b64decode(resumes[0]["content_base64"]).decode("utf-8")
    assert decoded == "Python developer with AWS experience"


def test_missing_required_columns_raises() -> None:
    with pytest.raises(InvalidCsvFormat):
        parse_bulk_csv(b"candidate_id,notes\ncand-1,hello\n")


def test_empty_resume_text_raises() -> None:
    with pytest.raises(InvalidCsvFormat):
        parse_bulk_csv(b"candidate_id,resume_text\ncand-1,\n")


def test_missing_candidate_id_falls_back_to_row_number() -> None:
    csv_bytes = b"candidate_id,resume_text\n,Some resume text\n"
    resumes = parse_bulk_csv(csv_bytes)
    assert resumes[0]["candidate_id"] is None
    assert resumes[0]["filename"] == "row-2.txt"
