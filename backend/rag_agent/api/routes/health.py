"""
Health check API routes for the RAG Agent Service
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
import logging

from ...services.agent_service import agent_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])



@router.get("/health/service", summary="Check service health")
async def service_health_check() -> Dict[str, Any]:
    """
    Check the health of the entire service including all components
    """
    start_time = time.time()

    try:
        service_health = await agent_service.validate_service_health()

        total_time = time.time() - start_time
        service_health["response_time"] = round(total_time, 4)

        # Return appropriate HTTP status based on health
        if service_health["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail=service_health)

        return service_health

    except Exception as e:
        logger.error(f"Service health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "message": f"Service health check failed: {str(e)}",
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
        )


@router.get("/health", summary="Check overall health")
async def overall_health_check() -> Dict[str, Any]:
    """
    Check the overall health of the system
    """
    start_time = time.time()

    # Check service health
    service_health = await agent_service.validate_service_health()

    total_time = time.time() - start_time

    overall_status = service_health["status"]

    health_result = {
        "status": overall_status,
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "response_time": round(total_time, 4),
        "components": {
            "service": service_health
        }
    }

    # Return appropriate HTTP status based on overall health
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=health_result)

    return health_result