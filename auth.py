"""Authentication utilities for Movie Recommender System."""

import os
import jwt
import functools
from typing import Callable, Any, Dict
import logging

logger = logging.getLogger(__name__)

def auth_required(f: Callable[[Dict[str, Any], Dict[str, Any]], Any]) -> Callable:
    """
    Decorator to handle JWT authentication for Lambda functions.
    """
    @functools.wraps(f)
    def wrapper(event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Skip auth for OPTIONS requests (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return build_cors_response({})

        # Get the authorization header
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization') or headers.get('authorization')
        
        if not auth_header:
            return build_error_response('No authorization header', 401)
            
        try:
            # Remove 'Bearer ' prefix if present
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            else:
                token = auth_header
                
            # Verify and decode the token
            jwt_secret = os.environ.get('JWT_SECRET', 'local-dev-secret-key')
            payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
            
            # Add user info to the event for the handler
            event['user'] = payload
            
            # Call the actual handler
            return f(event, context)
            
        except jwt.ExpiredSignatureError:
            return build_error_response('Token has expired', 401)
        except jwt.InvalidTokenError:
            return build_error_response('Invalid token', 401)
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            return build_error_response('Authorization failed', 401)
            
    return wrapper

def build_error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    """Build an error response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': {'error': message}
    }

def build_cors_response(body: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Build a success response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': body
    }

def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers for responses."""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE',
        'Content-Type': 'application/json'
    }

def generate_token(user: Dict[str, Any], expiry: int = None) -> str:
    """Generate a JWT token for a user."""
    if expiry is None:
        expiry = int(os.environ.get('TOKEN_EXPIRY', 86400))  # 24 hours default
        
    jwt_secret = os.environ.get('JWT_SECRET', 'local-dev-secret-key')
    
    token = jwt.encode({
        'user_id': user['user_id'],
        'email': user['email'],
        'name': user.get('name', ''),
        'exp': int(time.time()) + expiry
    }, jwt_secret, algorithm='HS256')
    
    return token

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    jwt_secret = os.environ.get('JWT_SECRET', 'local-dev-secret-key')
    return jwt.decode(token, jwt_secret, algorithms=['HS256'])
