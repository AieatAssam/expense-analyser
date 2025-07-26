"""
Health check endpoints for the Expense Analyser API.
Implements industry-standard health check patterns for Kubernetes and monitoring systems.
"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import logging

from app.core.health import get_health_status, get_readiness_status, get_liveness_status

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["Health"], summary="Comprehensive Health Check")
async def health_check(
    details: bool = Query(
        False, 
        description="Include detailed component information in the response"
    )
):
    """
    Comprehensive health check endpoint that verifies all application dependencies.
    
    This endpoint checks:
    - Database connectivity and operations
    - Redis cache availability (with fallback to in-memory)
    - Configuration validation
    - LLM provider setup
    - File storage capabilities
    
    Returns HTTP 200 for healthy/degraded status, HTTP 503 for unhealthy status.
    
    **Query Parameters:**
    - `details` (bool): Include detailed component information (default: false)
    
    **Response Statuses:**
    - `healthy`: All components are functioning normally
    - `degraded`: Some non-critical components have issues but service is operational
    - `unhealthy`: Critical components are failing and service may not function properly
    """
    try:
        health_data = await get_health_status(include_details=details)
        
        # Return appropriate HTTP status based on health
        if health_data["status"] == "unhealthy":
            return JSONResponse(
                status_code=503,
                content=health_data
            )
        else:
            return JSONResponse(
                status_code=200,
                content=health_data
            )
            
    except Exception as e:
        logger.error(f"Health check failed with exception: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": "Health check failed with internal error",
                "timestamp": None
            }
        )


@router.get("/health/ready", tags=["Health"], summary="Readiness Probe")
async def readiness_check():
    """
    Kubernetes-style readiness probe endpoint.
    
    Indicates whether the application is ready to receive traffic.
    This checks only critical dependencies required for basic operation:
    - Database connectivity
    - Essential configuration
    
    Returns HTTP 200 when ready, HTTP 503 when not ready.
    
    **Use this endpoint for:**
    - Kubernetes readiness probes
    - Load balancer health checks
    - Determining when to start sending traffic after deployment
    """
    try:
        readiness_data = await get_readiness_status()
        
        if readiness_data["status"] == "ready":
            return JSONResponse(
                status_code=200,
                content=readiness_data
            )
        else:
            return JSONResponse(
                status_code=503,
                content=readiness_data
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed with exception: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": "Readiness check failed with internal error"
            }
        )


@router.get("/health/live", tags=["Health"], summary="Liveness Probe")
async def liveness_check():
    """
    Kubernetes-style liveness probe endpoint.
    
    Indicates whether the application is alive and should continue running.
    This is the most basic health check that should almost always return success
    unless the application is completely broken.
    
    Returns HTTP 200 when alive, HTTP 503 when dead.
    
    **Use this endpoint for:**
    - Kubernetes liveness probes
    - Basic monitoring to detect if the application needs to be restarted
    - Automated recovery systems
    """
    try:
        liveness_data = await get_liveness_status()
        return JSONResponse(
            status_code=200,
            content=liveness_data
        )
        
    except Exception as e:
        logger.error(f"Liveness check failed with exception: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "dead",
                "error": "Liveness check failed with internal error"
            }
        )


@router.get("/health/status", tags=["Health"], summary="Simple Status Check")
async def simple_status():
    """
    Simple status endpoint for basic monitoring.
    
    Returns a lightweight response indicating the service is responding.
    This is the fastest health check endpoint with minimal dependencies.
    
    Always returns HTTP 200 unless the application is completely unresponsive.
    """
    return {
        "status": "ok", 
        "service": "expense-analyser-api",
        "version": "0.1.0"
    }


# Legacy endpoint for backward compatibility
@router.get("/ping", tags=["Health"], summary="Legacy Ping Endpoint")
async def ping():
    """
    Legacy ping endpoint for backward compatibility.
    
    Simple ping response for basic connectivity testing.
    """
    return {"ping": "pong", "status": "ok"}
