from celery import Celery

from api.config import settings

# In eager mode (default for this repo — see Settings.celery_task_always_eager)
# tasks run synchronously in-process and never touch the broker, so an
# in-memory result backend keeps the API/worker layer runnable with zero
# external infra. Real deployments set celery_task_always_eager=False and get
# a proper Redis-backed broker/backend for a real worker pool.
_backend = "cache+memory://" if settings.celery_task_always_eager else settings.redis_url

celery_app = Celery("resume_ai", broker=settings.redis_url, backend=_backend)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
    task_store_eager_result=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

# Import task modules so they register on this app.
from worker import tasks  # noqa: F401
