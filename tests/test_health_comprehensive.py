"""
Tests for the comprehensive health check system.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.exc import SQLAlchemyError

from app.core.health import HealthChecker, HealthStatus, ComponentStatus


class TestHealthChecker:
    """Test suite for the HealthChecker class"""
    
    def setup_method(self):
        """Set up test instance"""
        self.health_checker = HealthChecker()
    
    @pytest.mark.asyncio
    async def test_check_health_all_healthy(self):
        """Test health check when all components are healthy"""
        # Use AsyncMock to properly mock async methods
        mock_db = AsyncMock(return_value=ComponentStatus("database", HealthStatus.HEALTHY))
        mock_redis = AsyncMock(return_value=ComponentStatus("redis", HealthStatus.HEALTHY))
        mock_config = AsyncMock(return_value=ComponentStatus("configuration", HealthStatus.HEALTHY))
        mock_llm = AsyncMock(return_value=ComponentStatus("llm_providers", HealthStatus.HEALTHY))
        mock_storage = AsyncMock(return_value=ComponentStatus("storage", HealthStatus.HEALTHY))
        
        # Mock the checks dictionary instead of individual methods
        mock_checks = {
            "database": mock_db,
            "redis": mock_redis,
            "configuration": mock_config,
            "llm_providers": mock_llm,
            "storage": mock_storage,
        }
        
        with patch.object(self.health_checker, 'checks', mock_checks):
            result = await self.health_checker.check_health()
            
            assert result["status"] == "healthy"
            assert "timestamp" in result
            assert "duration_seconds" in result
            assert result["version"] == "0.1.0"
            assert len(result["components"]) == 5
    
    @pytest.mark.asyncio
    async def test_check_health_one_unhealthy(self):
        """Test health check when one component is unhealthy"""
        mock_db = AsyncMock(return_value=ComponentStatus("database", HealthStatus.UNHEALTHY))
        mock_healthy = AsyncMock(return_value=ComponentStatus("test", HealthStatus.HEALTHY))
        
        mock_checks = {
            "database": mock_db,
            "redis": mock_healthy,
            "configuration": mock_healthy,
            "llm_providers": mock_healthy,
            "storage": mock_healthy,
        }
            
        with patch.object(self.health_checker, 'checks', mock_checks):
            result = await self.health_checker.check_health()
            
            assert result["status"] == "unhealthy"
            assert result["components"]["database"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_check_health_degraded(self):
        """Test health check when some components are degraded"""
        mock_redis = AsyncMock(return_value=ComponentStatus("redis", HealthStatus.DEGRADED))
        mock_healthy = AsyncMock(return_value=ComponentStatus("test", HealthStatus.HEALTHY))
        
        mock_checks = {
            "database": mock_healthy,
            "redis": mock_redis,
            "configuration": mock_healthy,
            "llm_providers": mock_healthy,
            "storage": mock_healthy,
        }
            
        with patch.object(self.health_checker, 'checks', mock_checks):
            result = await self.health_checker.check_health()
            
            assert result["status"] == "degraded"
            assert result["components"]["redis"] == "degraded"
    
    @pytest.mark.asyncio
    async def test_check_health_include_details(self):
        """Test health check with detailed component information"""
        mock_component = ComponentStatus("database", HealthStatus.HEALTHY, {"version": "16.0"})
        mock_db = AsyncMock(return_value=mock_component)
        mock_healthy = AsyncMock(return_value=ComponentStatus("test", HealthStatus.HEALTHY))
        
        mock_checks = {
            "database": mock_db,
            "redis": mock_healthy,
            "configuration": mock_healthy,
            "llm_providers": mock_healthy,
            "storage": mock_healthy,
        }
        
        with patch.object(self.health_checker, 'checks', mock_checks):
            result = await self.health_checker.check_health(include_details=True)
            
            assert "components" in result
            assert "version" in result["components"]["database"]
            assert result["components"]["database"]["version"] == "16.0"
            assert "checked_at" in result["components"]["database"]


class TestDatabaseHealthCheck:
    """Test suite for database health checks"""
    
    def setup_method(self):
        self.health_checker = HealthChecker()
    
    @pytest.mark.asyncio
    async def test_database_check_healthy(self):
        """Test database health check when database is healthy"""
        # Mock SessionLocal and database operations
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = ["PostgreSQL 16.0"]
        mock_db.execute.return_value = mock_result
        mock_db.bind.pool.size.return_value = 5
        
        # Mock table query result
        mock_tables_result = MagicMock()
        mock_tables_result.fetchall.return_value = [("users",), ("receipts",), ("categories",)]
        
        with patch('app.core.health.SessionLocal', return_value=mock_db):
            # Set up multiple execute calls
            mock_db.execute.side_effect = [
                mock_result,  # First call for SELECT 1
                mock_result,  # Second call for version
                mock_tables_result  # Third call for tables
            ]
            
            result = await self.health_checker._check_database()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.name == "database"
            assert "version" in result.details
            assert result.details["key_tables_present"] is True
    
    @pytest.mark.asyncio
    async def test_database_check_unhealthy(self):
        """Test database health check when database is unhealthy"""
        with patch('app.core.health.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.execute.side_effect = SQLAlchemyError("Connection failed")
            
            result = await self.health_checker._check_database()
            
            assert result.status == HealthStatus.UNHEALTHY
            assert result.name == "database"
            assert "error" in result.details


class TestRedisHealthCheck:
    """Test suite for Redis health checks"""
    
    def setup_method(self):
        self.health_checker = HealthChecker()
    
    @pytest.mark.asyncio
    async def test_redis_check_healthy(self):
        """Test Redis health check when Redis is healthy"""
        mock_redis_client = MagicMock()
        mock_redis_client.ping.return_value = True
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = "test_value"
        mock_redis_client.delete.return_value = 1
        mock_redis_client.info.return_value = {
            "redis_version": "7.0.0",
            "used_memory_human": "1.0M",
            "connected_clients": 1,
            "uptime_in_seconds": 3600
        }
        
        with patch('redis.from_url', return_value=mock_redis_client):
            result = await self.health_checker._check_redis()
            
            assert result.status == HealthStatus.HEALTHY
            assert result.name == "redis"
            assert result.details["version"] == "7.0.0"
    
    @pytest.mark.asyncio
    async def test_redis_check_not_available(self):
        """Test Redis health check when Redis library is not available"""
        with patch('app.core.health.REDIS_AVAILABLE', False):
            result = await self.health_checker._check_redis()
            
            assert result.status == HealthStatus.DEGRADED
            assert "Redis library not available" in result.details["error"]
    
    @pytest.mark.asyncio
    async def test_redis_check_connection_failed(self):
        """Test Redis health check when connection fails"""
        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = Exception("Connection refused")
        
        with patch('redis.from_url', return_value=mock_redis_client):
            result = await self.health_checker._check_redis()
            
            assert result.status == HealthStatus.UNHEALTHY
            assert "error" in result.details


class TestConfigurationHealthCheck:
    """Test suite for configuration health checks"""
    
    def setup_method(self):
        self.health_checker = HealthChecker()
    
    @pytest.mark.asyncio
    async def test_configuration_check_healthy(self):
        """Test configuration health check when all settings are proper"""
        from app.core.config import settings
        
        with patch.object(settings, 'SECRET_KEY', 'properly-configured-secret'):
            with patch.object(settings, 'DATABASE_URL', 'postgresql://...'):
                with patch.object(settings, 'DEFAULT_LLM_PROVIDER', 'gemini'):
                    with patch.object(settings, 'GEMINI_API_KEY', 'valid-api-key'):
                        with patch.object(settings, 'CORS_ORIGINS', ['http://localhost:3000']):
                            with patch.object(settings, 'ENVIRONMENT', 'production'):
                                
                                result = await self.health_checker._check_configuration()
                                
                                assert result.status == HealthStatus.HEALTHY
                                assert result.details["database_configured"] is True
    
    @pytest.mark.asyncio
    async def test_configuration_check_unhealthy(self):
        """Test configuration health check when critical settings are missing"""
        from app.core.config import settings
        
        with patch.object(settings, 'SECRET_KEY', 'supersecretkey'):  # Default key
            with patch.object(settings, 'ENVIRONMENT', 'production'):
                with patch.object(settings, 'DEFAULT_LLM_PROVIDER', 'gemini'):
                    with patch.object(settings, 'GEMINI_API_KEY', ''):  # Missing API key
                        
                        result = await self.health_checker._check_configuration()
                        
                        assert result.status == HealthStatus.UNHEALTHY
                        assert "issues" in result.details


class TestHealthEndpoints:
    """Test suite for health check endpoints"""
    
    def test_health_endpoint_healthy(self, client):
        """Test /health endpoint when system is healthy"""
        with patch('app.api.endpoints.health.get_health_status') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "timestamp": "2023-01-01T00:00:00",
                "duration_seconds": 0.1,
                "version": "0.1.0",
                "environment": "test",
                "components": {"database": "healthy"}
            }
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_health_endpoint_unhealthy(self, client):
        """Test /health endpoint when system is unhealthy"""
        with patch('app.api.endpoints.health.get_health_status') as mock_health:
            mock_health.return_value = {
                "status": "unhealthy",
                "timestamp": "2023-01-01T00:00:00",
                "duration_seconds": 0.1,
                "version": "0.1.0",
                "environment": "test",
                "components": {"database": "unhealthy"}
            }
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
    
    def test_health_endpoint_with_details(self, client):
        """Test /health endpoint with details parameter"""
        with patch('app.api.endpoints.health.get_health_status') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "components": {
                    "database": {
                        "status": "healthy",
                        "version": "16.0",
                        "checked_at": "2023-01-01T00:00:00"
                    }
                }
            }
            
            response = client.get("/api/v1/health?details=true")
            
            assert response.status_code == 200
            mock_health.assert_called_once_with(include_details=True)
    
    def test_readiness_endpoint_ready(self, client):
        """Test /health/ready endpoint when ready"""
        with patch('app.api.endpoints.health.get_readiness_status') as mock_readiness:
            mock_readiness.return_value = {
                "status": "ready",
                "timestamp": "2023-01-01T00:00:00",
                "duration_seconds": 0.1,
                "checks": {"database": "healthy", "configuration": "healthy"}
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
    
    def test_readiness_endpoint_not_ready(self, client):
        """Test /health/ready endpoint when not ready"""
        with patch('app.api.endpoints.health.get_readiness_status') as mock_readiness:
            mock_readiness.return_value = {
                "status": "not_ready",
                "timestamp": "2023-01-01T00:00:00",
                "duration_seconds": 0.1,
                "checks": {"database": "unhealthy", "configuration": "healthy"}
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"
    
    def test_liveness_endpoint(self, client):
        """Test /health/live endpoint"""
        with patch('app.core.health.get_liveness_status') as mock_liveness:
            mock_liveness.return_value = {
                "status": "alive",
                "timestamp": "2023-01-01T00:00:00",
                "uptime_seconds": 3600,
                "version": "0.1.0"
            }
            
            response = client.get("/api/v1/health/live")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "alive"
    
    def test_simple_status_endpoint(self, client):
        """Test /health/status endpoint"""
        response = client.get("/api/v1/health/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "expense-analyser-api"
        assert data["version"] == "0.1.0"
    
    def test_ping_endpoint(self, client):
        """Test /api/v1/ping endpoint"""
        response = client.get("/api/v1/ping")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ping"] == "pong"
    
    def test_root_health_endpoint(self, client):
        """Test root /health endpoint"""
        with patch('app.main.get_health_status') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "timestamp": "2023-01-01T00:00:00"
            }
            
            response = client.get("/health")
            
            assert response.status_code == 200
    
    def test_root_ping_endpoint(self, client):
        """Test root /ping endpoint"""
        response = client.get("/ping")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ping"] == "pong"
        assert data["status"] == "ok"
    
    def test_root_ready_endpoint(self, client):
        """Test root /ready endpoint"""
        with patch('app.api.endpoints.health.get_readiness_status') as mock_readiness:
            mock_readiness.return_value = {"status": "ready"}
            
            response = client.get("/ready")
            
            assert response.status_code == 200
    
    def test_root_live_endpoint(self, client):
        """Test root /live endpoint"""
        with patch('app.core.health.get_liveness_status') as mock_liveness:
            mock_liveness.return_value = {"status": "alive"}
            
            response = client.get("/live")
            
            assert response.status_code == 200


class TestHealthExceptionHandling:
    """Test suite for health check exception handling"""
    
    def test_health_endpoint_exception(self, client):
        """Test health endpoint handles exceptions gracefully"""
        with patch('app.api.endpoints.health.get_health_status', side_effect=Exception("Internal error")):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert "error" in data
    
    def test_readiness_endpoint_exception(self, client):
        """Test readiness endpoint handles exceptions gracefully"""
        with patch('app.api.endpoints.health.get_readiness_status', side_effect=Exception("Internal error")):
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"
            assert "error" in data
    
    def test_liveness_endpoint_exception(self, client):
        """Test liveness endpoint handles exceptions gracefully"""
        with patch('app.api.endpoints.health.get_liveness_status', side_effect=Exception("Internal error")):
            response = client.get("/api/v1/health/live")
            
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "dead"
            assert "error" in data
