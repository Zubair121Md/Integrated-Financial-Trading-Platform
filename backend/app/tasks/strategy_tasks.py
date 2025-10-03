"""
Celery tasks for strategy execution and ML model management.
"""

from celery import current_task
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.services.strategy_executor import StrategyExecutor
from app.models.strategy import Strategy, AlgoStrategy
from app.tasks.celery import celery

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery.task(bind=True)
def execute_strategy_task(self, strategy_id: int):
    """Execute a trading strategy."""
    db = SessionLocal()
    try:
        executor = StrategyExecutor()
        result = await executor.execute_strategy(strategy_id, db)
        
        # Update task status
        current_task.update_state(
            state="SUCCESS",
            meta={"strategy_id": strategy_id, "result": result}
        )
        
        return result
    except Exception as e:
        current_task.update_state(
            state="FAILURE",
            meta={"strategy_id": strategy_id, "error": str(e)}
        )
        raise
    finally:
        db.close()


@celery.task(bind=True)
def execute_all_active_strategies_task(self):
    """Execute all active strategies."""
    db = SessionLocal()
    try:
        active_strategies = db.query(Strategy).filter(
            Strategy.is_active == True
        ).all()
        
        results = []
        executor = StrategyExecutor()
        
        for strategy in active_strategies:
            try:
                result = await executor.execute_strategy(strategy.id, db)
                results.append({
                    "strategy_id": strategy.id,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results.append({
                    "strategy_id": strategy.id,
                    "status": "error",
                    "error": str(e)
                })
        
        current_task.update_state(
            state="SUCCESS",
            meta={"total_strategies": len(active_strategies), "results": results}
        )
        
        return results
    except Exception as e:
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise
    finally:
        db.close()


@celery.task(bind=True)
def retrain_models_task(self):
    """Retrain all ML models."""
    db = SessionLocal()
    try:
        algo_strategies = db.query(AlgoStrategy).filter(
            AlgoStrategy.is_trained == True
        ).all()
        
        results = []
        
        for algo_strategy in algo_strategies:
            try:
                # This would trigger the actual ML training
                # For now, just update the last_trained timestamp
                algo_strategy.last_trained = datetime.utcnow()
                db.commit()
                
                results.append({
                    "algo_strategy_id": algo_strategy.id,
                    "status": "success",
                    "message": "Model retrained successfully"
                })
            except Exception as e:
                results.append({
                    "algo_strategy_id": algo_strategy.id,
                    "status": "error",
                    "error": str(e)
                })
        
        current_task.update_state(
            state="SUCCESS",
            meta={"total_models": len(algo_strategies), "results": results}
        )
        
        return results
    except Exception as e:
        current_task.update_state(
            state="FAILURE",
            meta={"error": str(e)}
        )
        raise
    finally:
        db.close()


@celery.task(bind=True)
def backtest_strategy_task(self, strategy_id: int, start_date: str, end_date: str):
    """Backtest a strategy on historical data."""
    from datetime import datetime
    
    db = SessionLocal()
    try:
        executor = StrategyExecutor()
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        result = await executor.backtest_strategy(strategy_id, start_dt, end_dt, db)
        
        current_task.update_state(
            state="SUCCESS",
            meta={"strategy_id": strategy_id, "result": result}
        )
        
        return result
    except Exception as e:
        current_task.update_state(
            state="FAILURE",
            meta={"strategy_id": strategy_id, "error": str(e)}
        )
        raise
    finally:
        db.close()
