from celery import Celery

from libs.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "dispatch",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    include=[
        "apps.workers.event_tasks",
        "apps.workers.import_tasks",
    ],
)
