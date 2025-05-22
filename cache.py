"""Rate limiting and caching utilities for Movie Recommender System."""

import time
import json
from typing import Dict, Any, Optional, Callable
import logging
from functools import wraps
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = {}  # user_id -> list of timestamps
        
    def is_allowed(self, user_id: str) -> bool:
        """Check if request is allowed for the user."""
        now = time.time()
        
        # Clean up old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                ts for ts in self.requests[user_id]
                if now - ts < self.time_window
            ]
        else:
            self.requests[user_id] = []
            
        # Check rate limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False
            
        # Add new request
        self.requests[user_id].append(now)
        return True

class Cache:
    """Simple cache implementation using DynamoDB."""
    
    def __init__(self, table_name: str = 'MovieRecommender_Cache', ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            table_name: DynamoDB table name for cache
            ttl: Time-to-live in seconds
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.ttl = ttl
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            response = self.table.get_item(Key={'key': key})
            
            if 'Item' not in response:
                return None
                
            item = response['Item']
            
            # Check if item has expired
            if 'expires_at' in item and item['expires_at'] < int(time.time()):
                self.delete(key)
                return None
                
            return json.loads(item['value'])
            
        except ClientError as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
            
    def set(self, key: str, value: Any) -> bool:
        """Set value in cache."""
        try:
            self.table.put_item(Item={
                'key': key,
                'value': json.dumps(value),
                'expires_at': int(time.time()) + self.ttl
            })
            return True
        except ClientError as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
            
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self.table.delete_item(Key={'key': key})
            return True
        except ClientError as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

def rate_limit(max_requests: int = 100, time_window: int = 60):
    """Decorator to apply rate limiting to a function."""
    limiter = RateLimiter(max_requests, time_window)
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(event: Dict[str, Any], context: Dict[str, Any], *args, **kwargs):
            # Get user ID from event
            user = event.get('user', {})
            user_id = user.get('user_id', 'anonymous')
            
            if not limiter.is_allowed(user_id):
                return {
                    'statusCode': 429,
                    'headers': {
                        'Access-Control-Allow-Origin': '*',
                        'Content-Type': 'application/json'
                    },
                    'body': {
                        'error': 'Rate limit exceeded'
                    }
                }
                
            return func(event, context, *args, **kwargs)
        return wrapper
    return decorator

def cache_result(ttl: int = 3600):
    """Decorator to cache function results."""
    cache = Cache()
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(event: Dict[str, Any], context: Dict[str, Any], *args, **kwargs):
            # Generate cache key from function name and event body
            cache_key = f"{func.__name__}:{hash(json.dumps(event, sort_keys=True))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
                
            # Execute function and cache result
            result = func(event, context, *args, **kwargs)
            cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator
