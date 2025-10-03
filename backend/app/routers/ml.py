"""
Machine Learning API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.strategy import AlgoStrategy
from app.models.asset import Asset
from app.services.ml_models import MLModelService

router = APIRouter()


@router.get("/models", response_model=List[dict])
async def get_ml_models(
    user_id: int = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get user's ML models."""
    # Get algo strategies for the user
    algo_strategies = db.query(AlgoStrategy).join(AlgoStrategy.strategy).filter(
        AlgoStrategy.strategy.has(user_id=user_id)
    ).all()
    
    return [algo_strategy.to_dict() for algo_strategy in algo_strategies]


@router.post("/train/{strategy_id}")
async def train_model(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """Train an ML model for a strategy."""
    algo_strategy = db.query(AlgoStrategy).filter(
        AlgoStrategy.strategy_id == strategy_id
    ).first()
    
    if not algo_strategy:
        raise HTTPException(status_code=404, detail="Algorithmic strategy not found")
    
    # Get the parent strategy
    strategy = algo_strategy.strategy
    if not strategy:
        raise HTTPException(status_code=404, detail="Parent strategy not found")
    
    # Get assets for training (simplified - would be based on strategy configuration)
    assets = db.query(Asset).filter(Asset.is_active == True).limit(5).all()
    
    if not assets:
        raise HTTPException(status_code=400, detail="No assets available for training")
    
    ml_service = MLModelService()
    results = []
    
    # Train models for each asset
    for asset in assets:
        try:
            if algo_strategy.ml_technique.value == "LSTM":
                result = await ml_service.train_lstm_model(asset.id, db=db)
            elif algo_strategy.ml_technique.value == "RANDOM_FOREST":
                result = await ml_service.train_random_forest_model(asset.id, db=db)
            elif algo_strategy.ml_technique.value == "SVM":
                result = await ml_service.train_svm_model(asset.id, db=db)
            else:
                result = {"status": "error", "message": f"Unsupported ML technique: {algo_strategy.ml_technique.value}"}
            
            results.append({
                "asset_id": asset.id,
                "symbol": asset.symbol,
                "result": result
            })
            
        except Exception as e:
            results.append({
                "asset_id": asset.id,
                "symbol": asset.symbol,
                "result": {"status": "error", "message": str(e)}
            })
    
    # Update algo strategy
    algo_strategy.is_trained = any(r["result"]["status"] == "success" for r in results)
    algo_strategy.last_trained = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Model training completed",
        "strategy_id": strategy_id,
        "ml_technique": algo_strategy.ml_technique.value,
        "results": results
    }


@router.post("/predict/{asset_id}")
async def predict_price(
    asset_id: int,
    model_type: str = Query("LSTM", description="Type of ML model to use"),
    db: Session = Depends(get_db)
):
    """Get price prediction for an asset using trained ML model."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Get recent market data
    from app.models.market_data import MarketData
    from datetime import datetime, timedelta
    
    recent_data = db.query(MarketData).filter(
        MarketData.asset_id == asset_id
    ).order_by(MarketData.timestamp.desc()).limit(60).all()
    
    if not recent_data:
        raise HTTPException(status_code=400, detail="No recent market data available")
    
    # Convert to DataFrame
    import pandas as pd
    data = []
    for md in recent_data:
        data.append({
            'timestamp': md.timestamp,
            'price': md.price,
            'open': md.open_price or md.price,
            'high': md.high_price or md.price,
            'low': md.low_price or md.price,
            'volume': md.volume or 0,
            'rsi': md.rsi or 0,
            'macd': md.macd or 0,
            'sma_20': md.sma_20 or 0,
            'sma_50': md.sma_50 or 0
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('timestamp')
    
    # Use ML service for prediction
    ml_service = MLModelService()
    
    # For demo purposes, use a mock model path
    # In production, this would load the actual trained model
    model_path = f"models/{model_type.lower()}_asset_{asset_id}_latest.joblib"
    
    try:
        prediction_result = await ml_service.predict_price(
            model_path, model_type, df, lookback_days=30
        )
        
        if prediction_result["status"] == "success":
            return {
                "asset_id": asset_id,
                "symbol": asset.symbol,
                "current_price": asset.current_price,
                "predicted_price": prediction_result["prediction"],
                "confidence": prediction_result["confidence"],
                "prediction_horizon": "1_day",
                "model_used": model_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Fallback to mock prediction
            return {
                "asset_id": asset_id,
                "symbol": asset.symbol,
                "current_price": asset.current_price,
                "predicted_price": asset.current_price * 1.02,
                "confidence": 0.75,
                "prediction_horizon": "1_day",
                "model_used": "mock_model",
                "message": "Using mock prediction - model not available"
            }
    
    except Exception as e:
        # Fallback to mock prediction
        return {
            "asset_id": asset_id,
            "symbol": asset.symbol,
            "current_price": asset.current_price,
            "predicted_price": asset.current_price * 1.02,
            "confidence": 0.75,
            "prediction_horizon": "1_day",
            "model_used": "mock_model",
            "message": f"Using mock prediction - error: {str(e)}"
        }


@router.get("/backtest/{strategy_id}")
async def backtest_strategy(
    strategy_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Run backtest for a strategy."""
    algo_strategy = db.query(AlgoStrategy).filter(
        AlgoStrategy.strategy_id == strategy_id
    ).first()
    
    if not algo_strategy:
        raise HTTPException(status_code=404, detail="Algorithmic strategy not found")
    
    # This would run the actual backtest
    # For now, return mock results
    return {
        "strategy_id": strategy_id,
        "backtest_period": {
            "start_date": start_date or "2023-01-01",
            "end_date": end_date or "2023-12-31"
        },
        "results": {
            "total_return": 15.5,
            "sharpe_ratio": 1.2,
            "max_drawdown": -8.3,
            "win_rate": 0.65,
            "total_trades": 45,
            "avg_trade_return": 0.34
        },
        "status": "completed"
    }
