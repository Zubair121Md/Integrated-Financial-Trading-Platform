#!/usr/bin/env python3
"""
ML model training script for the trading platform.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import engine
from app.services.ml_models import MLModelService
from app.models.asset import Asset
from app.models.strategy import AlgoStrategy
from app.config import settings

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def train_models_for_asset(asset_id: int, db_session):
    """Train all ML models for a specific asset."""
    ml_service = MLModelService()
    
    print(f"Training models for asset {asset_id}...")
    
    # Train LSTM model
    print("  Training LSTM model...")
    lstm_result = await ml_service.train_lstm_model(asset_id, db=db_session)
    print(f"    LSTM Result: {lstm_result}")
    
    # Train Random Forest model
    print("  Training Random Forest model...")
    rf_result = await ml_service.train_random_forest_model(asset_id, db=db_session)
    print(f"    Random Forest Result: {rf_result}")
    
    # Train SVM model
    print("  Training SVM model...")
    svm_result = await ml_service.train_svm_model(asset_id, db=db_session)
    print(f"    SVM Result: {svm_result}")
    
    return {
        "asset_id": asset_id,
        "lstm": lstm_result,
        "random_forest": rf_result,
        "svm": svm_result
    }


async def train_all_models():
    """Train ML models for all active assets."""
    db = SessionLocal()
    
    try:
        # Get all active assets
        assets = db.query(Asset).filter(Asset.is_active == True).limit(10).all()
        
        if not assets:
            print("No active assets found for training")
            return
        
        print(f"Found {len(assets)} assets for training")
        
        results = []
        for asset in assets:
            try:
                result = await train_models_for_asset(asset.id, db)
                results.append(result)
            except Exception as e:
                print(f"Error training models for asset {asset.id}: {e}")
                results.append({
                    "asset_id": asset.id,
                    "error": str(e)
                })
        
        # Print summary
        print("\n" + "="*50)
        print("TRAINING SUMMARY")
        print("="*50)
        
        for result in results:
            if "error" in result:
                print(f"Asset {result['asset_id']}: ERROR - {result['error']}")
            else:
                print(f"Asset {result['asset_id']}:")
                for model_type, model_result in result.items():
                    if model_type != "asset_id":
                        status = model_result.get("status", "unknown")
                        if status == "success":
                            metrics = model_result.get("metrics", {})
                            r2 = metrics.get("r2", 0)
                            print(f"  {model_type}: SUCCESS (R² = {r2:.3f})")
                        else:
                            print(f"  {model_type}: FAILED - {model_result.get('message', 'Unknown error')}")
        
    finally:
        db.close()


async def train_models_for_strategy(strategy_id: int):
    """Train models for a specific algorithmic strategy."""
    db = SessionLocal()
    
    try:
        # Get the strategy
        algo_strategy = db.query(AlgoStrategy).filter(
            AlgoStrategy.strategy_id == strategy_id
        ).first()
        
        if not algo_strategy:
            print(f"Algorithmic strategy {strategy_id} not found")
            return
        
        # Get the associated strategy
        strategy = algo_strategy.strategy
        if not strategy:
            print(f"Parent strategy not found for algo strategy {strategy_id}")
            return
        
        print(f"Training models for strategy: {strategy.name}")
        
        # Get assets associated with this strategy (simplified)
        assets = db.query(Asset).filter(Asset.is_active == True).limit(5).all()
        
        for asset in assets:
            try:
                result = await train_models_for_asset(asset.id, db)
                print(f"Trained models for asset {asset.symbol}: {result}")
            except Exception as e:
                print(f"Error training models for asset {asset.symbol}: {e}")
        
        # Update algo strategy
        algo_strategy.is_trained = True
        algo_strategy.last_trained = datetime.utcnow()
        db.commit()
        
        print(f"Strategy {strategy.name} training completed")
        
    finally:
        db.close()


async def main():
    """Main training function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train ML models for trading")
    parser.add_argument("--asset-id", type=int, help="Train models for specific asset")
    parser.add_argument("--strategy-id", type=int, help="Train models for specific strategy")
    parser.add_argument("--all", action="store_true", help="Train models for all assets")
    
    args = parser.parse_args()
    
    if args.asset_id:
        db = SessionLocal()
        try:
            result = await train_models_for_asset(args.asset_id, db)
            print(f"Training completed for asset {args.asset_id}: {result}")
        finally:
            db.close()
    
    elif args.strategy_id:
        await train_models_for_strategy(args.strategy_id)
    
    elif args.all:
        await train_all_models()
    
    else:
        print("Please specify --asset-id, --strategy-id, or --all")
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
