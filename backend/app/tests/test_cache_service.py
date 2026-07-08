"""Unit tests for cache service."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock


class TestCacheService:
    """Tests for CacheService."""
    
    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(self):
        """Test that get returns None for missing keys."""
        from app.services.cache_service import CacheService
        
        service = CacheService(redis_url="redis://localhost:6379/0")
        
        with patch.object(service, 'get_client') as mock_client:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = None
            mock_client.return_value = mock_redis
            
            result = await service.get("test_key")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_returns_value_for_existing_key(self):
        """Test that get returns value for existing keys."""
        from app.services.cache_service import CacheService
        
        service = CacheService(redis_url="redis://localhost:6379/0")
        
        with patch.object(service, 'get_client') as mock_client:
            mock_redis = AsyncMock()
            mock_redis.get.return_value = b'{"test": "value"}'
            mock_client.return_value = mock_redis
            
            result = await service.get("test_key")
            assert result == {"test": "value"}
    
    @pytest.mark.asyncio
    async def test_set_stores_value_with_ttl(self):
        """Test that set stores value with TTL."""
        from app.services.cache_service import CacheService
        
        service = CacheService(redis_url="redis://localhost:6379/0")
        
        with patch.object(service, 'get_client') as mock_client:
            mock_redis = AsyncMock()
            mock_redis.set = AsyncMock()
            mock_client.return_value = mock_redis
            
            await service.set("test_key", {"test": "value"}, ttl=60)
            
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert call_args[0][0] == "test_key"
            assert "ex" in call_args[1]
    
    @pytest.mark.asyncio
    async def test_delete_removes_key(self):
        """Test that delete removes key."""
        from app.services.cache_service import CacheService
        
        service = CacheService(redis_url="redis://localhost:6379/0")
        
        with patch.object(service, 'get_client') as mock_client:
            mock_redis = AsyncMock()
            mock_redis.delete = AsyncMock()
            mock_client.return_value = mock_redis
            
            await service.delete("test_key")
            
            mock_redis.delete.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_clear_flushes_database(self):
        """Test that clear flushes the database."""
        from app.services.cache_service import CacheService
        
        service = CacheService(redis_url="redis://localhost:6379/0")
        
        with patch.object(service, 'get_client') as mock_client:
            mock_redis = AsyncMock()
            mock_redis.flushdb = AsyncMock()
            mock_client.return_value = mock_redis
            
            await service.clear()
            
            mock_redis.flushdb.assert_called_once()


class TestGetCacheService:
    """Tests for get_cache_service function."""
    
    def test_returns_singleton_instance(self):
        """Test that get_cache_service returns singleton."""
        from app.services.cache_service import get_cache_service, _cache_service
        
        # Reset the singleton
        import app.services.cache_service as cache_module
        cache_module._cache_service = None
        
        service1 = get_cache_service()
        service2 = get_cache_service()
        
        assert service1 is service2