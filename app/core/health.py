"""
Health check module for the Expense Analyser API.
Implements comprehensive dependency and configuration checks following industry standards.
"""
import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ComponentStatus:
    """Individual component health status"""
    
    def __init__(self, name: str, status: HealthStatus, details: Optional[Dict[str, Any]] = None):
        self.name = name
        self.status = status
        self.details = details or {}
        self.checked_at = datetime.utcnow()


class HealthChecker:
    """Comprehensive health checker for all application dependencies"""
    
    def __init__(self):
        self.checks = {}
        self._register_checks()
    
    def _register_checks(self):
        """Register all health check functions"""
        self.checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "configuration": self._check_configuration,
            "llm_providers": self._check_llm_providers,
            "storage": self._check_storage,
        }
    
    async def check_health(self, include_details: bool = False) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all dependencies.
        
        Args:
            include_details: Whether to include detailed component information
            
        Returns:
            Health check result with overall status and component details
        """
        start_time = time.time()
        components = {}
        overall_status = HealthStatus.HEALTHY
        
        # Run all health checks concurrently
        tasks = {}
        for name, check_func in self.checks.items():
            tasks[name] = asyncio.create_task(check_func())
        
        # Wait for all checks to complete
        for name, task in tasks.items():
            try:
                component_status = await task
                components[name] = component_status
                
                # Determine overall status
                if component_status.status == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif component_status.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                components[name] = ComponentStatus(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    details={"error": str(e)}
                )
                overall_status = HealthStatus.UNHEALTHY
        
        duration = time.time() - start_time
        
        result = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": round(duration, 3),
            "version": "0.1.0",
            "environment": settings.ENVIRONMENT,
        }
        
        if include_details:
            result["components"] = {
                name: {
                    "status": comp.status.value,
                    "checked_at": comp.checked_at.isoformat(),
                    **comp.details
                } for name, comp in components.items()
            }
        else:
            # Just include component statuses without details
            result["components"] = {
                name: comp.status.value for name, comp in components.items()
            }
        
        return result
    
    async def _check_database(self) -> ComponentStatus:
        """Check PostgreSQL database connectivity and basic operations"""
        try:
            db = SessionLocal()
            try:
                # Test basic connectivity
                result = db.execute(text("SELECT 1"))
                result.fetchone()
                
                # Test database version and basic info
                version_result = db.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                
                # Test table existence (basic schema check)
                tables_result = db.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in tables_result.fetchall()]
                
                details = {
                    "version": version.split(" ")[0] if version else "unknown",
                    "connection_pool_size": db.bind.pool.size(),
                    "tables_count": len(tables),
                    "key_tables_present": bool(
                        set(["users", "receipts", "categories", "line_items"]).intersection(set(tables))
                    )
                }
                
                return ComponentStatus("database", HealthStatus.HEALTHY, details)
                
            finally:
                db.close()
                
        except SQLAlchemyError as e:
            return ComponentStatus(
                "database", 
                HealthStatus.UNHEALTHY, 
                {"error": f"Database error: {str(e)[:100]}"}
            )
        except Exception as e:
            return ComponentStatus(
                "database", 
                HealthStatus.UNHEALTHY, 
                {"error": f"Unexpected error: {str(e)[:100]}"}
            )
    
    async def _check_redis(self) -> ComponentStatus:
        """Check Redis cache connectivity and operations"""
        try:
            # Import redis here to handle cases where it's not installed
            import redis
            
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            
            # Test basic connectivity
            pong = redis_client.ping()
            if not pong:
                return ComponentStatus(
                    "redis", 
                    HealthStatus.UNHEALTHY, 
                    {"error": "Redis ping failed"}
                )
            
            # Test basic operations
            test_key = "health_check_test"
            redis_client.set(test_key, "test_value", ex=10)
            retrieved_value = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            if retrieved_value != "test_value":
                return ComponentStatus(
                    "redis", 
                    HealthStatus.DEGRADED, 
                    {"error": "Redis operations not working correctly"}
                )
            
            # Get Redis info
            info = redis_client.info()
            details = {
                "version": info.get("redis_version", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
            return ComponentStatus("redis", HealthStatus.HEALTHY, details)
            
        except ImportError:
            return ComponentStatus(
                "redis", 
                HealthStatus.DEGRADED, 
                {"error": "Redis library not available", "fallback": "in-memory cache"}
            )
        except Exception as e:
            return ComponentStatus(
                "redis", 
                HealthStatus.UNHEALTHY, 
                {"error": f"Redis error: {str(e)[:100]}"}
            )
    
    async def _check_configuration(self) -> ComponentStatus:
        """Check critical configuration settings"""
        issues = []
        warnings = []
        
        # Check required settings
        if not settings.SECRET_KEY or settings.SECRET_KEY == "supersecretkey":
            if settings.ENVIRONMENT == "production":
                issues.append("SECRET_KEY should be changed in production")
            else:
                warnings.append("Using default SECRET_KEY (OK for development)")
        
        if not settings.DATABASE_URL:
            issues.append("DATABASE_URL not configured")
        
        # Check LLM provider configuration
        if settings.DEFAULT_LLM_PROVIDER == "gemini" and not settings.GEMINI_API_KEY:
            issues.append("GEMINI_API_KEY not configured but set as default provider")
        elif settings.DEFAULT_LLM_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
            issues.append("OPENAI_API_KEY not configured but set as default provider")
        
        # Check CORS configuration
        if not settings.CORS_ORIGINS:
            warnings.append("No CORS origins configured")
        
        details = {
            "environment": settings.ENVIRONMENT,
            "llm_provider": settings.DEFAULT_LLM_PROVIDER,
            "cors_origins_count": len(settings.CORS_ORIGINS),
            "database_configured": bool(settings.DATABASE_URL),
            "redis_configured": bool(settings.REDIS_URL),
        }
        
        if warnings:
            details["warnings"] = warnings
        
        if issues:
            details["issues"] = issues
            return ComponentStatus("configuration", HealthStatus.UNHEALTHY, details)
        elif warnings:
            return ComponentStatus("configuration", HealthStatus.DEGRADED, details)
        else:
            return ComponentStatus("configuration", HealthStatus.HEALTHY, details)
    
    async def _check_llm_providers(self) -> ComponentStatus:
        """Check LLM provider availability and configuration"""
        providers_status = {}
        
        # Check Gemini
        if settings.GEMINI_API_KEY:
            try:
                # We can't easily test Gemini without making an actual API call
                # So we just verify the key is present and properly formatted
                if len(settings.GEMINI_API_KEY) > 10:  # Basic validation
                    providers_status["gemini"] = "configured"
                else:
                    providers_status["gemini"] = "invalid_key"
            except Exception as e:
                providers_status["gemini"] = f"error: {str(e)[:50]}"
        else:
            providers_status["gemini"] = "not_configured"
        
        # Check OpenAI
        if settings.OPENAI_API_KEY:
            try:
                # Basic validation for OpenAI key format
                if settings.OPENAI_API_KEY.startswith("sk-") and len(settings.OPENAI_API_KEY) > 20:
                    providers_status["openai"] = "configured"
                else:
                    providers_status["openai"] = "invalid_key"
            except Exception as e:
                providers_status["openai"] = f"error: {str(e)[:50]}"
        else:
            providers_status["openai"] = "not_configured"
        
        details = {
            "default_provider": settings.DEFAULT_LLM_PROVIDER,
            "providers": providers_status
        }
        
        # Determine status
        default_provider_status = providers_status.get(settings.DEFAULT_LLM_PROVIDER, "not_configured")
        
        if default_provider_status == "configured":
            status = HealthStatus.HEALTHY
        elif default_provider_status in ["not_configured", "invalid_key"]:
            status = HealthStatus.UNHEALTHY
            details["error"] = f"Default LLM provider '{settings.DEFAULT_LLM_PROVIDER}' is {default_provider_status}"
        else:
            status = HealthStatus.DEGRADED
        
        return ComponentStatus("llm_providers", status, details)
    
    async def _check_storage(self) -> ComponentStatus:
        """Check file storage and upload capabilities"""
        try:
            import os
            
            # Check if uploads directory exists and is writable
            uploads_dir = "/app/uploads" if os.path.exists("/app/uploads") else "uploads"
            
            if not os.path.exists(uploads_dir):
                try:
                    os.makedirs(uploads_dir, exist_ok=True)
                except Exception as e:
                    return ComponentStatus(
                        "storage", 
                        HealthStatus.UNHEALTHY, 
                        {"error": f"Cannot create uploads directory: {str(e)}"}
                    )
            
            # Test write permissions
            test_file = os.path.join(uploads_dir, "health_check_test.txt")
            try:
                with open(test_file, "w") as f:
                    f.write("health check test")
                
                # Verify we can read it back
                with open(test_file, "r") as f:
                    content = f.read()
                
                os.remove(test_file)
                
                if content != "health check test":
                    return ComponentStatus(
                        "storage", 
                        HealthStatus.DEGRADED, 
                        {"error": "File operations not working correctly"}
                    )
                
            except Exception as e:
                return ComponentStatus(
                    "storage", 
                    HealthStatus.UNHEALTHY, 
                    {"error": f"Cannot write to uploads directory: {str(e)}"}
                )
            
            # Get directory info
            try:
                stat_info = os.statvfs(uploads_dir)
                free_space_mb = (stat_info.f_bavail * stat_info.f_frsize) // (1024 * 1024)
                
                details = {
                    "uploads_directory": uploads_dir,
                    "writable": True,
                    "free_space_mb": free_space_mb
                }
                
                # Warn if low on space
                if free_space_mb < 100:  # Less than 100MB
                    details["warning"] = "Low disk space available"
                    return ComponentStatus("storage", HealthStatus.DEGRADED, details)
                
                return ComponentStatus("storage", HealthStatus.HEALTHY, details)
                
            except Exception as e:
                # If we can't get space info, but basic operations work
                return ComponentStatus(
                    "storage", 
                    HealthStatus.HEALTHY, 
                    {"uploads_directory": uploads_dir, "writable": True, "space_check_failed": str(e)}
                )
                
        except Exception as e:
            return ComponentStatus(
                "storage", 
                HealthStatus.UNHEALTHY, 
                {"error": f"Storage check failed: {str(e)}"}
            )


# Global health checker instance
health_checker = HealthChecker()


async def get_health_status(include_details: bool = False) -> Dict[str, Any]:
    """
    Get comprehensive health status of the application.
    
    Args:
        include_details: Whether to include detailed component information
        
    Returns:
        Health status dictionary
    """
    return await health_checker.check_health(include_details=include_details)


async def get_readiness_status() -> Dict[str, Any]:
    """
    Get readiness status - whether the application is ready to serve traffic.
    This is a lighter check focusing on critical dependencies only.
    """
    start_time = time.time()
    
    # Check only critical components for readiness
    db_status = await health_checker._check_database()
    config_status = await health_checker._check_configuration()
    
    duration = time.time() - start_time
    
    # Application is ready if database and configuration are healthy
    is_ready = (
        db_status.status == HealthStatus.HEALTHY and
        config_status.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    )
    
    return {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "duration_seconds": round(duration, 3),
        "checks": {
            "database": db_status.status.value,
            "configuration": config_status.status.value
        }
    }


async def get_liveness_status() -> Dict[str, Any]:
    """
    Get liveness status - whether the application is alive and functioning.
    This is the most basic check.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time(),  # This would be more accurate with app start time
        "version": "0.1.0"
    }
