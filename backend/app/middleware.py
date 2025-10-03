"""
Custom middleware for the trading platform.
"""

import time
from typing import Callable
from fastapi import Request, HTTPException
from fastapi.responses import Response
import redis.asyncio as redis

from app.config import settings


class RateLimitMiddleware:
    """Rate limiting middleware using Redis."""
    
    def __init__(self, app):
        self.app = app
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        client_ip = request.client.host
        
        # Check rate limit
        if await self._is_rate_limited(client_ip):
            response = Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": str(self.window)}
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)
    
    async def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit."""
        key = f"rate_limit:{client_ip}"
        current_time = int(time.time())
        window_start = current_time - self.window
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(key, self.window)
        
        results = await pipe.execute()
        current_requests = results[1]
        
        return current_requests >= self.rate_limit
