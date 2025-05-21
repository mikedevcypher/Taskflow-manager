# src/task_management/cache/redis_client.py
"""
Redis client module for TaskFlow.
This module provides functions for caching and cache invalidation.
"""
import redis
import json
from functools import wraps
import logging

# Initialize Redis client
redis_client = None
logger = logging.getLogger(__name__)

def init_redis(app):
    """
    Initialize Redis client with the Flask app configuration.

    """
    global redis_client
    
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    try:
        redis_client = redis.from_url(redis_url)
        # Test the connection
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except redis.ConnectionError:
        logger.warning("Redis connection failed - caching will be disabled")
        redis_client = None
    except Exception as e:
        logger.error(f"Redis initialization error: {str(e)}")
        redis_client = None

def cache_data(key_prefix, expire=300):
    """
    Decorator to cache function results in Redis.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if redis_client is None:
                return f(*args, **kwargs)
                
            # Create a unique key based on the function arguments
            key_parts = [key_prefix]
            
            # Add args to key
            for arg in args[1:]:  # Skip self/cls
                key_parts.append(str(arg))
                
            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}:{v}")
                
            cache_key = ":".join(key_parts)
            
            try:
                # Try to get data from cache
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"Error retrieving from cache: {str(e)}")
                return f(*args, **kwargs)
                
            # If not in cache, call the original function
            data = f(*args, **kwargs)
            
            try:
                # Store in cache
                redis_client.setex(
                    cache_key,
                    expire,
                    json.dumps(data)
                )
            except Exception as e:
                logger.error(f"Error storing in cache: {str(e)}")
                
            return data
        return decorated_function
    return decorator

def invalidate_cache(pattern):
    """
    Invalidate cache entries matching the pattern.
    """
    if redis_client is None:
        return 0
    
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        return 0

def clear_all_cache():
    """
    Clear all cache entries.
    """
    if redis_client is None:
        return False
    
    try:
        redis_client.flushdb()
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False

def check_redis():
    """
    Check if Redis is available.
    """
    if redis_client is None:
        return False
    
    try:
        redis_client.ping()
        return True
    except Exception:
        return False