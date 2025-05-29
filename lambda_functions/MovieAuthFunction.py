import json
import uuid
import time
import jwt

from utils.config import Config
from utils.utils_function import generate_token, generate_salt, hash_password, verify_password, build_response, validate_password_strength
import utils.database as db

def handle_login(event):
    """
    Handle login request
    """
    try:
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        email = request_body.get('email')
        password = request_body.get('password')
        
        if not email or not password:
            return build_response(400, {'error': 'Email and password are required'})
        
        # Check if user exists
        response = db.users_table.get_item(
            Key={'email': email}
        )
        
        user = response.get('Item')
        if not user:
            return build_response(401, {'error': 'Invalid credentials'})
        
        # Verify password
        stored_password = user.get('password_hash')
        salt = user.get('salt')
        
        if not verify_password(password, stored_password, salt):
            return build_response(401, {'error': 'Invalid credentials'})
        
        # Generate JWT token
        token = generate_token(user)
        
        # Return user info and token
        return build_response(200, {
            'token': token,
            'user': {
                'id': user.get('user_id'),
                'name': user.get('name'),
                'email': user.get('email'),
                'created_at': user.get('created_at')
            }
        })
    
    except Exception as e:
        print(f"Login error: {str(e)}")
        return build_response(500, {'error': 'Error during login'})

def handle_register(event):
    """
    Handle user registration
    """
    try:
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        name = request_body.get('name')
        email = request_body.get('email')
        password = request_body.get('password')
        
        if not name or not email or not password:
            return build_response(400, {'error': 'Name, email, and password are required'})
        
        # Check if user already exists
        response = db.users_table.get_item(
            Key={'email': email}
        )
        
        if 'Item' in response:
            return build_response(409, {'error': 'Email already exists'})
          # Validate password
        if not validate_password_strength(password):
            return build_response(400, {'error': 'Password must be at least 8 characters long and contain letters and numbers'})
        
        # Generate password hash
        salt = generate_salt()
        password_hash = hash_password(password, salt)
        
        # Create user record
        timestamp = int(time.time())
        user_id = str(uuid.uuid4())
        
        user = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'password_hash': password_hash,
            'salt': salt,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Save user to DynamoDB
        db.users_table.put_item(Item=user)
        
        # Generate JWT token
        token = generate_token(user)
        
        # Return user info and token
        return build_response(201, {
            'token': token,
            'user': {
                'id': user_id,
                'name': name,
                'email': email,
                'created_at': timestamp
            }
        })
    
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return build_response(500, {'error': 'Error during registration'})

def handle_refresh(event):
    """
    Handle token refresh
    """
    try:
        # Get Authorization header
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return build_response(401, {'error': 'Invalid token'})
        
        token = auth_header.split(' ')[1]
          # Verify token
        try:
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
        except:
            return build_response(401, {'error': 'Invalid token'})
        
        # Get user from database
        user_id = payload.get('user_id')
        email = payload.get('email')
        
        if not user_id or not email:
            return build_response(401, {'error': 'Invalid token'})
        
        # Get user from DynamoDB
        response = db.users_table.get_item(
            Key={'email': email}
        )
        
        user = response.get('Item')
        if not user or user.get('user_id') != user_id:
            return build_response(401, {'error': 'Invalid token'})
        
        # Generate new token
        new_token = generate_token(user)
        
        # Return new token
        return build_response(200, {
            'token': new_token,
            'user': {
                'id': user.get('user_id'),
                'name': user.get('name'),
                'email': user.get('email'),
                'created_at': user.get('created_at')
            }
        })
    
    except Exception as e:
        print(f"Refresh token error: {str(e)}")
        return build_response(500, {'error': 'Error refreshing token'})