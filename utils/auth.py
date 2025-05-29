"""Authentication utilities for Movie Recommender System."""

import os
import jwt
import functools
from typing import Callable, Any, Dict
import logging
import time
import json
import base64
import hmac
import hashlib
import boto3

logger = logging.getLogger(__name__)

# JWT secret - in production, use AWS Secrets Manager
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-key')
JWT_EXPIRY = 86400  # 24 hours in seconds

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'MovieRecommender_Users'))

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

def generate_salt():
    """
    Generate random salt for password hashing
    """
    return base64.b64encode(os.urandom(16)).decode()

def hash_password(password, salt):
    """
    Hash password using HMAC-SHA256
    """
    pwdhash = hmac.new(
        salt.encode(),
        password.encode(),
        hashlib.sha256
    ).digest()
    return base64.b64encode(pwdhash).decode()

def verify_password(password, stored_hash, salt):
    """
    Verify password against stored hash
    """
    computed_hash = hash_password(password, salt)
    return computed_hash == stored_hash

def build_response(status_code, body):
    """
    Build API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        },
        'body': json.dumps(body)
    } 