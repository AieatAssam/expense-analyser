#!/usr/bin/env python3
"""
Script to apply targeted fixes to health tests
"""

import re

def fix_health_comprehensive_tests():
    """Apply targeted fixes to test_health_comprehensive.py"""
    
    with open('tests/test_health_comprehensive.py', 'r') as f:
        content = f.read()
    
    # Fix 1: Redis test_redis_check_not_available
    old_redis_test = '''    @pytest.mark.asyncio
    async def test_redis_check_not_available(self):
        """Test Redis health check when Redis library is not available"""
        with patch('app.core.health.redis', side_effect=ImportError("Redis not installed")):
            # We need to reload the module or mock the import differently
            with patch.dict('sys.modules', {'redis': None}):
                result = await self.health_checker._check_redis()
                
                assert result.status == HealthStatus.DEGRADED
                assert "Redis library not available" in result.details["error"]'''
    
    new_redis_test = '''    @pytest.mark.asyncio
    async def test_redis_check_not_available(self):
        """Test Redis health check when Redis library is not available"""
        with patch('app.core.health.REDIS_AVAILABLE', False):
            result = await self.health_checker._check_redis()
            
            assert result.status == HealthStatus.DEGRADED
            assert "Redis library not available" in result.details["error"]'''
    
    content = content.replace(old_redis_test, new_redis_test)
    
    # Fix 2: Health endpoint tests - fix patch paths
    # test_health_endpoint_healthy
    content = content.replace(
        "with patch('app.core.health.get_health_status') as mock_health:",
        "with patch('app.api.endpoints.health.get_health_status') as mock_health:"
    )
    
    # test_readiness_endpoint_ready
    content = content.replace(
        "with patch('app.core.health.get_readiness_status') as mock_readiness:",
        "with patch('app.api.endpoints.health.get_readiness_status') as mock_readiness:"
    )
    
    # Fix 3: Exception handling tests
    content = content.replace(
        "with patch('app.core.health.get_health_status', side_effect=Exception(\"Internal error\")):",
        "with patch('app.api.endpoints.health.get_health_status', side_effect=Exception(\"Internal error\")):"
    )
    
    content = content.replace(
        "with patch('app.core.health.get_readiness_status', side_effect=Exception(\"Internal error\")):",
        "with patch('app.api.endpoints.health.get_readiness_status', side_effect=Exception(\"Internal error\")):"
    )
    
    content = content.replace(
        "with patch('app.core.health.get_liveness_status', side_effect=Exception(\"Internal error\")):",
        "with patch('app.api.endpoints.health.get_liveness_status', side_effect=Exception(\"Internal error\")):"
    )
    
    with open('tests/test_health_comprehensive.py', 'w') as f:
        f.write(content)
    
    print("Applied health test fixes")

if __name__ == "__main__":
    fix_health_comprehensive_tests()
