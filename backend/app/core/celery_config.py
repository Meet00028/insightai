"""
# Architect: Meet Kumar
# InsightAI - Celery Configuration
"""

from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "insightai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.services.tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=settings.DOCKER_TIMEOUT,
    task_soft_time_limit=settings.DOCKER_TIMEOUT - 10,
    
    # Result backend
    result_backend=settings.REDIS_URL,
    result_expires=3600 * 24 * 7,  # 7 days
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_heartbeat=30,
    
    # Task routes
    task_routes={
        "app.services.tasks.process_dataset": {"queue": "data_processing"},
        "app.services.tasks.run_analysis": {"queue": "analysis"},
    },
    
    # Task annotations
    task_annotations={
        "*": {
            "rate_limit": "10/m",
        }
    },
)

# Define queues
celery_app.conf.task_queues = {
    "celery": {"exchange": "celery", "routing_key": "celery"},
    "data_processing": {"exchange": "data_processing", "routing_key": "data_processing"},
    "analysis": {"exchange": "analysis", "routing_key": "analysis"},
}
