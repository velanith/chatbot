"""Health check router for system monitoring endpoints."""

from fastapi import APIRouter, status
from datetime import datetime
import time
import psutil
import os

from src.presentation.schemas.common_schemas import (
    HealthResponse,
    ServiceHealth,
    HealthStatus,
    APIMetadata
)

router = APIRouter()

# Store application start time
_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Get system health status and service availability",
    responses={
        200: {"description": "System is healthy"},
        503: {"description": "System is unhealthy"}
    }
)
async def health_check() -> HealthResponse:
    """
    Get system health status and service availability.
    
    Returns overall system health and individual service statuses.
    """
    services = []
    overall_status = HealthStatus.HEALTHY
    
    # Check database health
    db_health = await _check_database_health()
    services.append(db_health)
    if db_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # Check LLM service health (OpenRouter)
    llm_health = await _check_llm_health()
    services.append(llm_health)
    if llm_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # Check memory usage
    memory_health = _check_memory_health()
    services.append(memory_health)
    if memory_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # Check disk usage
    disk_health = _check_disk_health()
    services.append(disk_health)
    if disk_health.status != HealthStatus.HEALTHY:
        overall_status = HealthStatus.DEGRADED
    
    # Calculate uptime
    uptime_seconds = time.time() - _start_time
    
    # Get application version
    version = os.getenv("APP_VERSION", "1.0.0")
    
    return HealthResponse(
        overall_status=overall_status,
        services=services,
        uptime_seconds=uptime_seconds,
        version=version
    )


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if application is ready to serve requests",
    responses={
        200: {"description": "Application is ready"},
        503: {"description": "Application is not ready"}
    }
)
async def readiness_check() -> dict:
    """
    Check if application is ready to serve requests.
    
    Returns readiness status for load balancer health checks.
    """
    # Check critical services
    db_health = await _check_database_health()
    
    if db_health.status == HealthStatus.HEALTHY:
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    else:
        return {"status": "not_ready", "reason": "database_unavailable", "timestamp": datetime.utcnow().isoformat()}


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Check if application is alive",
    responses={
        200: {"description": "Application is alive"}
    }
)
async def liveness_check() -> dict:
    """
    Check if application is alive.
    
    Simple liveness check for container orchestration.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - _start_time
    }


@router.get(
    "/info",
    response_model=APIMetadata,
    status_code=status.HTTP_200_OK,
    summary="API information",
    description="Get API metadata and build information",
    responses={
        200: {"description": "API information retrieved successfully"}
    }
)
async def api_info() -> APIMetadata:
    """
    Get API metadata and build information.
    
    Returns API version, environment, and build details.
    """
    return APIMetadata(
        version=os.getenv("APP_VERSION", "1.0.0"),
        environment=os.getenv("ENVIRONMENT", "development"),
        build_time=datetime.fromisoformat(os.getenv("BUILD_TIME", datetime.utcnow().isoformat())),
        commit_hash=os.getenv("GIT_COMMIT_HASH")
    )


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="Application metrics",
    description="Get application performance and usage metrics",
    responses={
        200: {"description": "Metrics retrieved successfully"},
        500: {"description": "Failed to retrieve metrics"}
    }
)
async def get_metrics() -> dict:
    """
    Get application performance and usage metrics.
    
    Returns metrics collected by the application including request counts,
    response times, error rates, and system resource usage.
    """
    try:
        from src.infrastructure.logging.metrics import get_metrics_collector
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_all_metrics()
    except Exception as e:
        return {
            "error": f"Failed to retrieve metrics: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get(
    "/performance",
    status_code=status.HTTP_200_OK,
    summary="Performance metrics",
    description="Get detailed performance metrics and system resource usage",
    responses={
        200: {"description": "Performance metrics retrieved successfully"},
        500: {"description": "Failed to retrieve performance metrics"}
    }
)
async def get_performance_metrics() -> dict:
    """
    Get detailed performance metrics and system resource usage.
    
    Returns performance metrics including CPU usage, memory usage,
    response times, and throughput statistics.
    """
    try:
        from src.infrastructure.logging.monitoring import setup_monitoring
        performance_monitor, _ = setup_monitoring()
        return performance_monitor.get_performance_summary()
    except Exception as e:
        return {
            "error": f"Failed to retrieve performance metrics: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


async def _check_database_health() -> ServiceHealth:
    """Check database connectivity and performance."""
    start_time = time.time()
    
    try:
        # TODO: Implement actual database health check
        # For now, simulate a health check
        await _simulate_db_check()
        
        response_time = (time.time() - start_time) * 1000
        
        if response_time > 1000:  # > 1 second
            status = HealthStatus.DEGRADED
            details = {"warning": "High response time"}
        else:
            status = HealthStatus.HEALTHY
            details = {"connection": "ok"}
        
        return ServiceHealth(
            name="database",
            status=status,
            response_time_ms=response_time,
            details=details
        )
        
    except Exception as e:
        return ServiceHealth(
            name="database",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=(time.time() - start_time) * 1000,
            details={"error": str(e)}
        )


async def _check_llm_health() -> ServiceHealth:
    """Check LLM service connectivity (OpenRouter)."""
    start_time = time.time()
    
    try:
        # Check actual LLM service availability
        from src.application.services.llm_service_registry import llm_registry
        from src.infrastructure.config import get_settings
        
        settings = get_settings()
        llm_registry.configure_from_settings(settings)
        
        # Get health status from registry
        health_status = await llm_registry.health_check()
        
        response_time = (time.time() - start_time) * 1000
        
        # Check if any LLM service is available
        is_healthy = any(health_status.values()) if health_status else False
        
        return ServiceHealth(
            name="llm_service",
            status=HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
            response_time_ms=response_time,
            details={
                "providers": health_status,
                "primary_provider": "openrouter" if settings.use_openrouter else "none"
            }
        )
        
    except Exception as e:
        return ServiceHealth(
            name="llm_service",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=(time.time() - start_time) * 1000,
            details={"error": str(e)}
        )


def _check_memory_health() -> ServiceHealth:
    """Check system memory usage."""
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        if memory_percent > 90:
            status = HealthStatus.UNHEALTHY
        elif memory_percent > 80:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        return ServiceHealth(
            name="memory",
            status=status,
            details={
                "usage_percent": memory_percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2)
            }
        )
        
    except Exception as e:
        return ServiceHealth(
            name="memory",
            status=HealthStatus.UNHEALTHY,
            details={"error": str(e)}
        )


def _check_disk_health() -> ServiceHealth:
    """Check disk usage."""
    try:
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        if disk_percent > 95:
            status = HealthStatus.UNHEALTHY
        elif disk_percent > 85:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        return ServiceHealth(
            name="disk",
            status=status,
            details={
                "usage_percent": round(disk_percent, 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2)
            }
        )
        
    except Exception as e:
        return ServiceHealth(
            name="disk",
            status=HealthStatus.UNHEALTHY,
            details={"error": str(e)}
        )


async def _simulate_db_check():
    """Simulate database health check."""
    import asyncio
    await asyncio.sleep(0.1)  # Simulate DB query time


async def _simulate_llm_check():
    """Simulate LLM API health check."""
    import asyncio
    await asyncio.sleep(0.2)  # Simulate API call time