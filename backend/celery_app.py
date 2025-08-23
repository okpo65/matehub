from celery import Celery
import time
import os

# Get configuration from environment or use defaults
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_RESULT_EXPIRES = int(os.getenv("CELERY_RESULT_EXPIRES", "3600"))

# Create Celery instance
celery_app = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Result backend configuration
    result_backend=CELERY_RESULT_BACKEND,
    result_expires=CELERY_RESULT_EXPIRES,
    task_track_started=True,
    # Additional result handling settings
    task_ignore_result=False,  # Store task results
    result_persistent=True,    # Persist results to disk
    task_store_eager_result=True,  # Store results even for eager tasks
    # Task execution settings
    task_acks_late=True,      # Acknowledge tasks after completion
    worker_prefetch_multiplier=1,  # Process one task at a time per worker
    # Redis result backend settings
    # result_backend_transport_options={
    #     'master_name': 'mymaster',
    #     'visibility_timeout': 3600,
    #     'retry_policy': {
    #         'timeout': 5.0
    #     }
    # },
    # Include task modules
    include=[
        'celery_app',
        'app.llm.tasks',  # Re-enabled for LLM tasks
    ]
)

@celery_app.task
def add_numbers(x: int, y: int) -> int:
    """Simple task to add two numbers"""
    time.sleep(2)  # Simulate some work
    return x + y

@celery_app.task
def process_data(data: str) -> str:
    """Simple task to process data"""
    time.sleep(3)  # Simulate processing time
    return f"Processed: {data.upper()}"
