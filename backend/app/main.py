"""
Main FastAPI application for the Integrated Financial Trading Platform.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from app.config import settings
from app.routers import assets, strategies, trades, users, ml, reports, subscriptions
from app.database import engine, Base
from app.middleware import RateLimitMiddleware


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Integrated Financial Trading Platform",
        description="A comprehensive trading platform supporting multiple asset classes with algorithmic trading capabilities",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.amazonaws.com"]
    )
    
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware)
    
    # Include routers
    app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
    app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["strategies"])
    app.include_router(trades.router, prefix="/api/v1/trades", tags=["trades"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(ml.router, prefix="/api/v1/ml", tags=["ml"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
    app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
    
    return app


# Create the app instance
app = create_app()


@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks."""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize Redis connection
    from app.database import redis_client
    await redis_client.ping()
    
    print("🚀 Trading Platform started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup tasks on shutdown."""
    from app.database import redis_client
    await redis_client.close()
    print("👋 Trading Platform shutdown complete!")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Integrated Financial Trading Platform API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation not available in production",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
