"""
Celery tasks for the trading platform.
"""

from .celery import celery
from .strategy_tasks import execute_strategy_task, retrain_models_task
from .data_tasks import fetch_market_data_task, update_asset_prices_task

__all__ = [
    "celery",
    "execute_strategy_task",
    "retrain_models_task", 
    "fetch_market_data_task",
    "update_asset_prices_task"
]
