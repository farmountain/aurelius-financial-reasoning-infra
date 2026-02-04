"""AURELIUS REST API - Main application entry point."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any

# Add api directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api.log')
    ]
)
logger = logging.getLogger(__name__)

# Import routers
from routers import strategies, backtests, validation, gates, auth
from routers import websocket_router

# Create FastAPI app
app = FastAPI(
    title="AURELIUS API",
    description="REST API for quantitative strategy generation, backtesting, and validation",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(strategies.router)
app.include_router(backtests.router)
app.include_router(validation.router)
app.include_router(gates.router)
app.include_router(websocket_router.router)

# Initialize database
from database.session import Base, engine

# Application metrics
app.state.start_time = None
app.state.request_count = 0

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    app.state.start_time = time.time()
    logger.info("🚀 AURELIUS API starting up...")
    
    # Create tables on startup (wrapped in try/except for graceful degradation)
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.warning(f"⚠️  Database connection failed on startup: {e}")
        logger.warning("⚠️  API will run but database operations may fail")
    
    logger.info("✅ AURELIUS API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("🛑 AURELIUS API shutting down...")

@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests and track metrics."""
    app.state.request_count += 1
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    """API root endpoint with service info."""
    return {
        "service": "AURELIUS Quantitative Trading API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "strategies": "/api/v1/strategies",
            "backtests": "/api/v1/backtests",
            "validation": "/api/v1/validation",
            "gates": "/api/v1/gates",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


@app.get("/health")
async def health():
    """
    Health check endpoint for load balancers and monitoring.
    Returns detailed health status including database connectivity.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AURELIUS API",
        "version": "1.0.0"
    }
    
    # Check database connection
    try:
        from database.session import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = "disconnected"
        health_status["status"] = "degraded"
        logger.error(f"Health check - Database error: {e}")
    
    return health_status


@app.get("/metrics")
async def metrics():
    """
    Prometheus-compatible metrics endpoint.
    Provides runtime metrics for monitoring and alerting.
    """
    uptime = time.time() - app.state.start_time if app.state.start_time else 0
    
    return {
        "uptime_seconds": uptime,
        "request_count": app.state.request_count,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "aurelius-api"
    }


@app.get("/api/v1/status")
async def api_status():
    """Get API status and metrics."""
    return {
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "strategies": "available",
            "backtests": "available",
            "validation": "available",
            "gates": "available",
        },
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
