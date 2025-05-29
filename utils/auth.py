"""Authentication utilities for Movie Recommender System."""

import os
import jwt
import functools
from typing import Callable, Any, Dict
import logging
import time

logger = logging.getLogger(__name__)

# JWT secret - in production, use AWS Secrets Manager
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-key')
JWT_EXPIRY = 86400  # 24 hours in seconds

def get_cors_headers():
    """Get CORS headers for responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Content-Type': 'application/json'
    }

def generate_token(user):
    """
    Generate JWT token
    """
    now = int(time.time())
    payload = {
        'user_id': user.get('user_id'),
        'email': user.get('email'),
        'name': user.get('name'),
        'iat': now,
        'exp': now + JWT_EXPIRY
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def get_authenticated_user(event):
    """
    Get authenticated user from JWT token
    """
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        email = payload.get('email')
        
        if not email:
            return None
        
        # Get user from DynamoDB
        response = users_table.get_item(
            Key={'email': email}
        )
        
        return response.get('Item')
    except:
        return None

