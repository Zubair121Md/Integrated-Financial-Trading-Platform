"""
Asset-related API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import Asset
from app.services.asset_handlers import AssetHandlerService
from shared.enums.asset_types import AssetType

router = APIRouter()


@router.get("/", response_model=List[dict])
async def get_assets(
    asset_type: Optional[AssetType] = Query(None, description="Filter by asset type"),
    limit: int = Query(100, ge=1, le=1000, description="Number of assets to return"),
    offset: int = Query(0, ge=0, description="Number of assets to skip"),
    db: Session = Depends(get_db)
):
    """Get list of assets with optional filtering."""
    query = db.query(Asset).filter(Asset.is_active == True)
    
    if asset_type:
        query = query.filter(Asset.type == asset_type)
    
    assets = query.offset(offset).limit(limit).all()
    return [asset.to_dict() for asset in assets]


@router.get("/{asset_id}", response_model=dict)
async def get_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get a specific asset by ID."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset.to_dict()


@router.get("/symbol/{symbol}", response_model=dict)
async def get_asset_by_symbol(symbol: str, db: Session = Depends(get_db)):
    """Get a specific asset by symbol."""
    asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset.to_dict()


@router.get("/type/{asset_type}", response_model=List[dict])
async def get_assets_by_type(
    asset_type: AssetType,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get assets by type."""
    assets = db.query(Asset).filter(
        Asset.type == asset_type,
        Asset.is_active == True
    ).offset(offset).limit(limit).all()
    
    return [asset.to_dict() for asset in assets]


@router.post("/{asset_type}/{symbol}/fetch", response_model=dict)
async def fetch_asset_data(
    asset_type: AssetType,
    symbol: str,
    db: Session = Depends(get_db)
):
    """Fetch and update asset data from external APIs."""
    try:
        handler_service = AssetHandlerService()
        data = await handler_service.fetch_asset_data(asset_type, symbol)
        
        # Update or create asset in database
        asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
        if not asset:
            asset = Asset(
                symbol=symbol.upper(),
                name=data.get('name', symbol),
                type=asset_type
            )
            db.add(asset)
        
        # Update asset data
        asset.current_price = data.get('price')
        asset.previous_close = data.get('previous_close')
        asset.day_high = data.get('day_high')
        asset.day_low = data.get('day_low')
        asset.volume = data.get('volume')
        asset.market_cap = data.get('market_cap')
        asset.metadata = data.get('metadata', {})
        
        db.commit()
        db.refresh(asset)
        
        return asset.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch asset data: {str(e)}")


@router.get("/search/{query}", response_model=List[dict])
async def search_assets(
    query: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search assets by symbol or name."""
    search_term = f"%{query.upper()}%"
    assets = db.query(Asset).filter(
        Asset.is_active == True,
        (Asset.symbol.ilike(search_term) | Asset.name.ilike(search_term))
    ).limit(limit).all()
    
    return [asset.to_dict() for asset in assets]
