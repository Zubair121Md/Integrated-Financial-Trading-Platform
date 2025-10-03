"""
Celery tasks for market data fetching and processing.
"""

from celery import current_task
from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.services.asset_handlers import AssetHandlerService
from app.models.asset import Asset
from app.models.market_data import MarketData
from shared.enums.asset_types import AssetType

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery.task(bind=True)
def fetch_market_data_task(self, asset_type: str = None):
    """Fetch market data for all assets or specific asset type."""
    db = SessionLocal()
    try:
        asset_handler = AssetHandlerService()
        
        # Get assets to fetch data for
        query = db.query(Asset).filter(Asset.is_active == True)
        if asset_type:
            query = query.filter(Asset.type == AssetType(asset_type))
        
        assets = query.limit(50).all()  # Limit to prevent overwhelming APIs
        
        results = []
        for asset in assets:
            try:
                # Fetch data from external API
                data = await asset_handler.fetch_asset_data(asset.type, asset.symbol)
                
                # Create market data record
                market_data = MarketData(
                    asset_id=asset.id,
                    symbol=asset.symbol,
                    price=data.get('price', 0),
                    open_price=data.get('open_price'),
                    high_price=data.get('day_high'),
                    low_price=data.get('day_low'),
                    previous_close=data.get('previous_close'),
                    volume=data.get('volume'),
                    change=data.get('change'),
                    change_percent=data.get('change_percent'),
                    metadata=data.get('metadata', {})
                )
                
                db.add(market_data)
                
                # Update asset current price
                asset.current_price = data.get('price')
                asset.last_price_update = datetime.utcnow()
                
                results.append({
                    "asset_id": asset.id,
                    "symbol": asset.symbol,
                    "price": data.get('price'),
                    "status": "success"
                })
                
            except Exception as e:
                results.append({
                    "asset_id": asset.id,
                    "symbol": asset.symbol,
                    "status": "error",
                    "error": str(e)
                })
        
        db.commit()
        
        current_task.update_state(
            state="SUCCESS",
            meta={"total_assets": len(assets), "results": results}
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
def update_asset_prices_task(self):
    """Update asset prices from cached market data."""
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        # Get assets that need price updates
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        assets = db.query(Asset).filter(
            Asset.is_active == True,
            (Asset.last_price_update < cutoff_time) | (Asset.last_price_update.is_(None))
        ).limit(20).all()
        
        results = []
        asset_handler = AssetHandlerService()
        
        for asset in assets:
            try:
                # Fetch latest data
                data = await asset_handler.fetch_asset_data(asset.type, asset.symbol)
                
                # Update asset
                asset.current_price = data.get('price')
                asset.previous_close = data.get('previous_close')
                asset.day_high = data.get('day_high')
                asset.day_low = data.get('day_low')
                asset.volume = data.get('volume')
                asset.last_price_update = datetime.utcnow()
                
                results.append({
                    "asset_id": asset.id,
                    "symbol": asset.symbol,
                    "price": data.get('price'),
                    "status": "success"
                })
                
            except Exception as e:
                results.append({
                    "asset_id": asset.id,
                    "symbol": asset.symbol,
                    "status": "error",
                    "error": str(e)
                })
        
        db.commit()
        
        current_task.update_state(
            state="SUCCESS",
            meta={"total_assets": len(assets), "results": results}
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
def calculate_technical_indicators_task(self, asset_id: int):
    """Calculate technical indicators for an asset."""
    from app.services.technical_analysis import TechnicalAnalysisService
    
    db = SessionLocal()
    try:
        # Get recent market data
        market_data = db.query(MarketData).filter(
            MarketData.asset_id == asset_id
        ).order_by(MarketData.timestamp.desc()).limit(100).all()
        
        if len(market_data) < 20:
            return {"status": "insufficient_data", "asset_id": asset_id}
        
        # Calculate indicators
        ta_service = TechnicalAnalysisService()
        indicators = ta_service.calculate_indicators(market_data)
        
        # Update the latest market data record with indicators
        latest_data = market_data[0]
        latest_data.rsi = indicators.get('rsi')
        latest_data.macd = indicators.get('macd')
        latest_data.sma_20 = indicators.get('sma_20')
        latest_data.sma_50 = indicators.get('sma_50')
        latest_data.ema_12 = indicators.get('ema_12')
        latest_data.ema_26 = indicators.get('ema_26')
        
        db.commit()
        
        current_task.update_state(
            state="SUCCESS",
            meta={"asset_id": asset_id, "indicators": indicators}
        )
        
        return {"status": "success", "asset_id": asset_id, "indicators": indicators}
    except Exception as e:
        current_task.update_state(
            state="FAILURE",
            meta={"asset_id": asset_id, "error": str(e)}
        )
        raise
    finally:
        db.close()
