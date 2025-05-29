"""
Utility functions for authentication, response building, and common operations
Uses shared configuration for consistent behavior across Lambda functions
"""
import jwt
import logging
import time
import json
import base64
import hmac
import hashlib
import os
from .config import Config
from . import database as db

logger = logging.getLogger(__name__)

def get_cors_headers():
    """Get CORS headers for responses using shared configuration"""
    return Config.get_cors_headers()

def generate_token(user):
    """
    Generate JWT token using shared configuration
    Args:
        user: User object containing user_id, email, name
    Returns:
        str: JWT token
    """
    now = int(time.time())
    payload = {
        'user_id': user.get('user_id'),
        'email': user.get('email'),
        'name': user.get('name'),
        'iat': now,
        'exp': now + Config.JWT_EXPIRY
    }
    
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')

def get_authenticated_user(event):
    """
    Get authenticated user from JWT token
    Args:
        event: Lambda event object containing headers
    Returns:
        dict: User object if valid token, None otherwise
    """
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        email = payload.get('email')
        
        if not email:
            return None
        
        # Get user from DynamoDB
        response = db.users_table.get_item(
            Key={'email': email}
        )
        
        return response.get('Item')
    except jwt.ExpiredSignatureError:
        if Config.DEBUG_MODE:
            print("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        if Config.DEBUG_MODE:
            print("Invalid JWT token")
        return None
    except Exception as e:
        if Config.DEBUG_MODE:
            print(f"Error validating JWT token: {str(e)}")
        return None

def generate_salt():
    """
    Generate random salt for password hashing
    Returns:
        str: Base64 encoded salt
    """
    return base64.b64encode(os.urandom(16)).decode()

def hash_password(password, salt):
    """
    Hash password using HMAC-SHA256
    Args:
        password: Plain text password
        salt: Salt for hashing
    Returns:
        str: Base64 encoded hash
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
    Args:
        password: Plain text password to verify
        stored_hash: Stored password hash
        salt: Salt used for hashing
    Returns:
        bool: True if password matches, False otherwise
    """
    computed_hash = hash_password(password, salt)
    return computed_hash == stored_hash

def build_response(status_code, body):
    """
    Build API Gateway response with proper CORS headers
    Args:
        status_code: HTTP status code
        body: Response body (will be JSON encoded)
    Returns:
        dict: API Gateway response object
    """
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(body) if not isinstance(body, str) else body
    }

def validate_email(email):
    """
    Basic email validation
    Args:
        email: Email address to validate
    Returns:
        bool: True if email format is valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Validate password strength
    Args:
        password: Password to validate
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    return True, ""

def log_user_activity(user_id, action, data=None):
    """
    Log user activity to activity table if logging is enabled
    Args:
        user_id: User ID performing the action
        action: Action being performed
        data: Optional additional data
    """
    if not Config.ENABLE_ACTIVITY_LOGGING:
        return
    
    timestamp = int(time.time() * 1000)  # Milliseconds for sorting
    
    item = {
        'user_id': user_id,
        'timestamp': timestamp,
        'action': action
    }
    
    if data:
        item['data'] = data
    
    try:
        db.activity_table.put_item(Item=item)
    except Exception as e:
        print(f"Error logging activity: {str(e)}")

def sanitize_input(input_string, max_length=None):
    """
    Basic input sanitization
    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length
    Returns:
        str: Sanitized string
    """
    if not isinstance(input_string, str):
        return ""
    
    # Remove null bytes and control characters
    sanitized = ''.join(char for char in input_string if ord(char) >= 32 or char in '\t\n\r')
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Apply length limit
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized