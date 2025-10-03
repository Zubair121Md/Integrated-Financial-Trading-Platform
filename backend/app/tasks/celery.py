"""
Celery configuration for the trading platform.
"""

from celery import Celery
from app.config import settings

# Create Celery instance
celery = Celery(
    "trading_platform",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.strategy_tasks",
        "app.tasks.data_tasks"
    ]
)

# Celery configuration
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    beat_schedule={
        "execute-strategies": {
            "task": "app.tasks.strategy_tasks.execute_strategy_task",
            "schedule": 300.0,  # Every 5 minutes
        },
        "fetch-market-data": {
            "task": "app.tasks.data_tasks.fetch_market_data_task",
            "schedule": 60.0,  # Every minute
        },
        "update-asset-prices": {
            "task": "app.tasks.data_tasks.update_asset_prices_task",
            "schedule": 30.0,  # Every 30 seconds
        },
        "retrain-models": {
            "task": "app.tasks.strategy_tasks.retrain_models_task",
            "schedule": 86400.0,  # Daily
        },
    },
)
