from pathlib import Path

import pytest

SAMPLE_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "sample"


@pytest.fixture
def sample_data_dir() -> Path:
    return SAMPLE_DATA_DIR


def read_sample_resume(name: str) -> str:
    return (SAMPLE_DATA_DIR / "resumes" / f"{name}.txt").read_text(encoding="utf-8")


def read_sample_jd(name: str) -> str:
    return (SAMPLE_DATA_DIR / "job_descriptions" / f"{name}.txt").read_text(encoding="utf-8")


class StubDoc:
    def __init__(self, ents: list) -> None:
        self.ents = ents


def stub_nlp_no_entities(text: str) -> StubDoc:
    """A fake spaCy pipeline that finds no entities, so tests exercise the
    deterministic regex/heuristic fallback regardless of whether the real
    en_core_web_sm model happens to be installed in the test environment."""
    return StubDoc(ents=[])
