"""
Payment processing service using Stripe.
"""

import stripe
from typing import Dict, Any, Optional
from fastapi import HTTPException

from app.config import settings


class PaymentService:
    """Service for handling payment processing with Stripe."""
    
    def __init__(self):
        stripe.api_key = settings.stripe_secret_key
    
    async def create_payment_intent(
        self, 
        amount: int, 
        currency: str = "usd",
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a payment intent for subscription."""
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "status": intent.status
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Payment error: {str(e)}")
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a subscription for a customer."""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                metadata=metadata or {},
                expand=['latest_invoice.payment_intent'],
            )
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Subscription error: {str(e)}")
    
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Create a Stripe customer."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            return {
                "customer_id": customer.id,
                "email": customer.email
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Customer creation error: {str(e)}")
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription details."""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=404, detail=f"Subscription not found: {str(e)}")
    
    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancel a subscription."""
        try:
            subscription = stripe.Subscription.delete(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "canceled_at": subscription.canceled_at
            }
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Subscription cancellation error: {str(e)}")
    
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.stripe_webhook_secret
            )
            
            if event['type'] == 'payment_intent.succeeded':
                return await self._handle_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                return await self._handle_invoice_payment_succeeded(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                return await self._handle_subscription_deleted(event['data']['object'])
            
            return {"status": "ignored", "event_type": event['type']}
            
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")
    
    async def _handle_payment_succeeded(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment."""
        # Update user subscription status in database
        return {
            "status": "payment_succeeded",
            "payment_intent_id": payment_intent['id'],
            "amount": payment_intent['amount']
        }
    
    async def _handle_invoice_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful invoice payment."""
        # Update subscription status
        return {
            "status": "invoice_payment_succeeded",
            "subscription_id": invoice['subscription'],
            "amount_paid": invoice['amount_paid']
        }
    
    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation."""
        # Update user subscription status
        return {
            "status": "subscription_deleted",
            "subscription_id": subscription['id'],
            "canceled_at": subscription['canceled_at']
        }
