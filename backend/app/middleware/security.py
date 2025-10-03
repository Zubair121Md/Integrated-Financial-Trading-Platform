"""
Security middleware for the trading platform.
"""

import time
from typing import Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
import redis.asyncio as redis
from app.config import settings


class SecurityMiddleware:
    """Security middleware for rate limiting and attack prevention."""
    
    def __init__(self, app):
        self.app = app
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.rate_limit = 100  # requests per minute
        self.window = 60  # seconds
        self.block_duration = 300  # 5 minutes
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        client_ip = request.client.host
        
        # Check if IP is blocked
        if await self._is_ip_blocked(client_ip):
            response = Response(
                content="IP address is temporarily blocked",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )
            await response(scope, receive, send)
            return
        
        # Check rate limit
        if await self._is_rate_limited(client_ip):
            await self._record_failed_attempt(client_ip)
            response = Response(
                content="Rate limit exceeded",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={"Retry-After": str(self.window)}
            )
            await response(scope, receive, send)
            return
        
        # Reset failed attempts on successful request
        await self._reset_failed_attempts(client_ip)
        
        await self.app(scope, receive, send)
    
    async def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is currently blocked."""
        block_key = f"blocked_ip:{client_ip}"
        return await self.redis_client.exists(block_key)
    
    async def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if IP has exceeded rate limit."""
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
    
    async def _record_failed_attempt(self, client_ip: str):
        """Record a failed attempt for an IP."""
        key = f"failed_attempts:{client_ip}"
        current_time = int(time.time())
        
        # Add failed attempt
        await self.redis_client.zadd(key, {str(current_time): current_time})
        
        # Set expiration
        await self.redis_client.expire(key, 3600)  # 1 hour
        
        # Check if IP should be blocked
        failed_attempts = await self.redis_client.zcard(key)
        if failed_attempts >= 10:  # Block after 10 failed attempts
            await self._block_ip(client_ip)
    
    async def _reset_failed_attempts(self, client_ip: str):
        """Reset failed attempts for an IP."""
        key = f"failed_attempts:{client_ip}"
        await self.redis_client.delete(key)
    
    async def _block_ip(self, client_ip: str):
        """Block an IP address."""
        block_key = f"blocked_ip:{client_ip}"
        await self.redis_client.setex(block_key, self.block_duration, "blocked")


class InputValidationMiddleware:
    """Middleware for input validation and sanitization."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            response = Response(
                content="Request too large",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            )
            await response(scope, receive, send)
            return
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data", "application/x-www-form-urlencoded")):
                response = Response(
                    content="Invalid content type",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)


class SecurityHeadersMiddleware:
    """Middleware for adding security headers."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                
                # Add security headers
                security_headers = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"x-xss-protection", b"1; mode=block"),
                    (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"content-security-policy", b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"),
                ]
                
                headers.extend(security_headers)
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
