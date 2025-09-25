"""
🎯 Cache Service
High-performance Redis-based caching with intelligent TTL management
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass

import structlog
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = structlog.get_logger(__name__)

@dataclass
class CacheStats:
    """Cache statistics for monitoring"""
    hits: int
    misses: int
    hit_rate: float
    total_keys: int
    memory_usage: int

class CacheService:
    """Professional Redis cache service with advanced features"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.connected = False
        
        # Cache prefixes for organization
        self.prefixes = {
            "api": "api:",
            "user": "user:",
            "product": "product:",
            "pricing": "pricing:",
            "analytics": "analytics:",
            "search": "search:",
            "session": "session:"
        }
        
        # Statistics tracking
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
    
    async def initialize(self):
        """Initialize cache service (alias for connect)"""
        await self.connect()
    
    async def connect(self):
        """Initialize Redis connection"""
        if self.connected:
            return
        
        try:
            # Configure Redis connection
            connection_params = {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "db": settings.REDIS_DB,
                "decode_responses": True,
                "retry_on_timeout": True,
                "health_check_interval": 30,
                "socket_keepalive": True,
                "socket_keepalive_options": {},
                "socket_connect_timeout": 5,
                "socket_timeout": 5
            }
            
            # Add password if configured
            if settings.REDIS_PASSWORD:
                connection_params["password"] = settings.REDIS_PASSWORD
            
            # Add SSL if configured
            if settings.REDIS_SSL:
                connection_params["ssl"] = True
                connection_params["ssl_cert_reqs"] = None
            
            self.redis_client = redis.Redis(**connection_params)
            
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            
            logger.info("Redis cache service connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            # Fall back to in-memory cache if Redis is unavailable
            self._memory_cache = {}
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            logger.info("Redis cache service disconnected")
    
    def _generate_key(self, key: str, prefix: str = "api") -> str:
        """Generate cache key with prefix and namespace"""
        namespace = settings.CACHE_NAMESPACE
        prefix_str = self.prefixes.get(prefix, "api:")
        return f"{namespace}:{prefix_str}{key}"
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for very long keys"""
        if len(key) > 250:  # Redis key length limit
            return hashlib.sha256(key.encode()).hexdigest()
        return key
    
    async def get(
        self, 
        key: str, 
        prefix: str = "api",
        default: Any = None
    ) -> Optional[Any]:
        """Get value from cache with automatic deserialization"""
        cache_key = self._generate_key(self._hash_key(key), prefix)
        
        try:
            if not self.connected:
                # Fall back to memory cache
                return self._memory_cache.get(cache_key, default)
            
            value = await self.redis_client.get(cache_key)
            
            if value is None:
                self._stats["misses"] += 1
                return default
            
            self._stats["hits"] += 1
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.warning(f"Cache get failed for key {cache_key}: {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        prefix: str = "api"
    ) -> bool:
        """Set value in cache with automatic serialization"""
        cache_key = self._generate_key(self._hash_key(key), prefix)
        ttl = ttl or settings.CACHE_TTL_DEFAULT
        
        try:
            # Serialize value
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            elif isinstance(value, (int, float, bool)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            if not self.connected:
                # Fall back to memory cache
                self._memory_cache[cache_key] = serialized_value
                return True
            
            await self.redis_client.setex(cache_key, ttl, serialized_value)
            self._stats["sets"] += 1
            
            return True
            
        except Exception as e:
            logger.warning(f"Cache set failed for key {cache_key}: {e}")
            return False
    
    async def delete(self, key: str, prefix: str = "api") -> bool:
        """Delete key from cache"""
        cache_key = self._generate_key(self._hash_key(key), prefix)
        
        try:
            if not self.connected:
                # Fall back to memory cache
                self._memory_cache.pop(cache_key, None)
                return True
            
            result = await self.redis_client.delete(cache_key)
            self._stats["deletes"] += 1
            
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Cache delete failed for key {cache_key}: {e}")
            return False
    
    async def exists(self, key: str, prefix: str = "api") -> bool:
        """Check if key exists in cache"""
        cache_key = self._generate_key(self._hash_key(key), prefix)
        
        try:
            if not self.connected:
                return cache_key in self._memory_cache
            
            result = await self.redis_client.exists(cache_key)
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Cache exists check failed for key {cache_key}: {e}")
            return False
    
    async def increment(
        self,
        key: str,
        amount: int = 1,
        ttl: Optional[int] = None,
        prefix: str = "api"
    ) -> int:
        """Atomically increment a counter"""
        cache_key = self._generate_key(self._hash_key(key), prefix)
        
        try:
            if not self.connected:
                # Simple memory cache increment
                current = self._memory_cache.get(cache_key, 0)
                if isinstance(current, str):
                    current = int(current)
                new_value = current + amount
                self._memory_cache[cache_key] = str(new_value)
                return new_value
            
            # Use Redis pipeline for atomic operation
            pipe = self.redis_client.pipeline()
            pipe.incr(cache_key, amount)
            
            if ttl:
                pipe.expire(cache_key, ttl)
            
            results = await pipe.execute()
            return results[0]
            
        except Exception as e:
            logger.warning(f"Cache increment failed for key {cache_key}: {e}")
            return 0
    
    async def get_multi(
        self,
        keys: List[str],
        prefix: str = "api"
    ) -> Dict[str, Any]:
        """Get multiple values from cache"""
        if not keys:
            return {}
        
        cache_keys = [self._generate_key(self._hash_key(key), prefix) for key in keys]
        
        try:
            if not self.connected:
                # Fall back to memory cache
                result = {}
                for orig_key, cache_key in zip(keys, cache_keys):
                    value = self._memory_cache.get(cache_key)
                    if value is not None:
                        try:
                            result[orig_key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            result[orig_key] = value
                return result
            
            values = await self.redis_client.mget(cache_keys)
            
            result = {}
            for orig_key, value in zip(keys, values):
                if value is not None:
                    self._stats["hits"] += 1
                    try:
                        result[orig_key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[orig_key] = value
                else:
                    self._stats["misses"] += 1
            
            return result
            
        except Exception as e:
            logger.warning(f"Cache get_multi failed: {e}")
            return {}
    
    async def set_multi(
        self,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
        prefix: str = "api"
    ) -> bool:
        """Set multiple values in cache"""
        if not data:
            return True
        
        ttl = ttl or settings.CACHE_TTL_DEFAULT
        
        try:
            if not self.connected:
                # Fall back to memory cache
                for key, value in data.items():
                    cache_key = self._generate_key(self._hash_key(key), prefix)
                    if isinstance(value, (dict, list, tuple)):
                        self._memory_cache[cache_key] = json.dumps(value)
                    else:
                        self._memory_cache[cache_key] = str(value)
                return True
            
            # Use Redis pipeline for batch operation
            pipe = self.redis_client.pipeline()
            
            for key, value in data.items():
                cache_key = self._generate_key(self._hash_key(key), prefix)
                
                # Serialize value
                if isinstance(value, (dict, list, tuple)):
                    serialized_value = json.dumps(value)
                elif isinstance(value, (int, float, bool)):
                    serialized_value = json.dumps(value)
                else:
                    serialized_value = str(value)
                
                pipe.setex(cache_key, ttl, serialized_value)
            
            await pipe.execute()
            self._stats["sets"] += len(data)
            
            return True
            
        except Exception as e:
            logger.warning(f"Cache set_multi failed: {e}")
            return False
    
    async def clear_pattern(self, pattern: str, prefix: str = "api") -> int:
        """Clear all keys matching a pattern"""
        cache_pattern = self._generate_key(pattern, prefix)
        
        try:
            if not self.connected:
                # Memory cache pattern clearing
                keys_to_delete = [
                    key for key in self._memory_cache.keys()
                    if key.startswith(cache_pattern.replace("*", ""))
                ]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                return len(keys_to_delete)
            
            # Scan for keys matching pattern
            deleted_count = 0
            async for key in self.redis_client.scan_iter(match=cache_pattern):
                await self.redis_client.delete(key)
                deleted_count += 1
            
            logger.info(f"Cleared {deleted_count} cache keys matching pattern: {pattern}")
            return deleted_count
            
        except Exception as e:
            logger.warning(f"Cache clear_pattern failed for pattern {pattern}: {e}")
            return 0
    
    async def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        try:
            if not self.connected:
                return CacheStats(
                    hits=self._stats["hits"],
                    misses=self._stats["misses"],
                    hit_rate=self._stats["hits"] / max(self._stats["hits"] + self._stats["misses"], 1),
                    total_keys=len(self._memory_cache),
                    memory_usage=0
                )
            
            # Get Redis info
            info = await self.redis_client.info("memory")
            
            # Count keys in our namespace
            namespace_pattern = f"{settings.CACHE_NAMESPACE}:*"
            key_count = 0
            async for _ in self.redis_client.scan_iter(match=namespace_pattern):
                key_count += 1
            
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / max(total_requests, 1)
            
            return CacheStats(
                hits=self._stats["hits"],
                misses=self._stats["misses"],
                hit_rate=hit_rate,
                total_keys=key_count,
                memory_usage=info.get("used_memory", 0)
            )
            
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return CacheStats(0, 0, 0.0, 0, 0)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        try:
            if not self.connected:
                return {
                    "status": "degraded",
                    "message": "Using memory cache fallback",
                    "redis_connected": False
                }
            
            # Test Redis connection
            start_time = datetime.utcnow()
            await self.redis_client.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Get basic info
            info = await self.redis_client.info()
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "response_time_ms": response_time,
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": str(e),
                "redis_connected": False
            }

# Global cache service instance
cache_service = CacheService()