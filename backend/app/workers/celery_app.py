from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "knowledge_sphere",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max
    task_queues={
        "documents": {"exchange": "documents", "routing_key": "documents"},
        "embeddings": {"exchange": "embeddings", "routing_key": "embeddings"},
        "graphs": {"exchange": "graphs", "routing_key": "graphs"},
        "reports": {"exchange": "reports", "routing_key": "reports"},
    }
)

# Auto-discover tasks from the workers package
celery_app.autodiscover_tasks(["app.workers"])
