import os

# Must be set before `api.config.settings` (and anything that imports it) is
# ever imported, since pydantic-settings reads the environment at instantiation.
os.environ.setdefault("API_KEYS", "test-key")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")

import base64

import pytest


@pytest.fixture
def api_key_headers() -> dict[str, str]:
    return {"X-API-Key": "test-key"}


@pytest.fixture
def sample_resume_base64() -> str:
    text = "Jane Doe\njane@example.com\n\nSkills\nPython, AWS, Docker\n\nExperience\nBackend Engineer, Acme Corp\n2019 - 2023\n"
    return base64.b64encode(text.encode("utf-8")).decode("ascii")
