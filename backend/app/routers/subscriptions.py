"""
Subscription and payment API endpoints.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.services.payment_service import PaymentService

router = APIRouter()


class SubscriptionCreate(BaseModel):
    """Schema for creating a subscription."""
    plan_id: str
    payment_method_id: str


class PaymentIntentCreate(BaseModel):
    """Schema for creating a payment intent."""
    amount: int
    currency: str = "usd"
    metadata: Dict[str, str] = {}


@router.post("/create-customer")
async def create_customer(
    email: str,
    name: str = None,
    user_id: int = None,
    db: Session = Depends(get_db)
):
    """Create a Stripe customer."""
    payment_service = PaymentService()
    
    try:
        customer = await payment_service.create_customer(
            email=email,
            name=name,
            metadata={"user_id": str(user_id)} if user_id else None
        )
        
        # Update user with customer ID
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.metadata = user.metadata or {}
                user.metadata["stripe_customer_id"] = customer["customer_id"]
                db.commit()
        
        return customer
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-payment-intent")
async def create_payment_intent(
    payment_data: PaymentIntentCreate,
    user_id: int = None
):
    """Create a payment intent for subscription."""
    payment_service = PaymentService()
    
    try:
        metadata = payment_data.metadata.copy()
        if user_id:
            metadata["user_id"] = str(user_id)
        
        intent = await payment_service.create_payment_intent(
            amount=payment_data.amount,
            currency=payment_data.currency,
            metadata=metadata
        )
        
        return intent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-subscription")
async def create_subscription(
    subscription_data: SubscriptionCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Create a subscription for a user."""
    payment_service = PaymentService()
    
    # Get user's Stripe customer ID
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    customer_id = user.metadata.get("stripe_customer_id") if user.metadata else None
    if not customer_id:
        raise HTTPException(status_code=400, detail="User does not have a Stripe customer ID")
    
    try:
        subscription = await payment_service.create_subscription(
            customer_id=customer_id,
            price_id=subscription_data.plan_id,
            metadata={"user_id": str(user_id)}
        )
        
        # Update user subscription status
        user.subscription_tier = "PREMIUM"  # Based on plan
        db.commit()
        
        return subscription
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscription/{subscription_id}")
async def get_subscription(subscription_id: str):
    """Get subscription details."""
    payment_service = PaymentService()
    
    try:
        subscription = await payment_service.get_subscription(subscription_id)
        return subscription
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/subscription/{subscription_id}")
async def cancel_subscription(subscription_id: str):
    """Cancel a subscription."""
    payment_service = PaymentService()
    
    try:
        result = await payment_service.cancel_subscription(subscription_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhook")
async def handle_webhook(request: Request):
    """Handle Stripe webhook events."""
    payment_service = PaymentService()
    
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    try:
        result = await payment_service.handle_webhook(payload, signature)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plans")
async def get_subscription_plans():
    """Get available subscription plans."""
    return {
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Paper trading",
                    "Basic strategies",
                    "Real-time data",
                    "Portfolio tracking"
                ]
            },
            {
                "id": "premium",
                "name": "Premium",
                "price": 2999,  # $29.99
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Everything in Free",
                    "Advanced strategies",
                    "ML predictions",
                    "Priority support",
                    "Advanced analytics"
                ]
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 9999,  # $99.99
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Everything in Premium",
                    "Custom strategies",
                    "API access",
                    "White-label options",
                    "Dedicated support"
                ]
            }
        ]
    }
