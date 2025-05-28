import json
import boto3
import os
import uuid
import hashlib
import hmac
import base64
import time
import jwt
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'MovieRecommender_Users'))

# JWT secret - in production, use AWS Secrets Manager
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-key')
JWT_EXPIRY = 86400  # 24 hours in seconds

def lambda_handler(event, context):
    """
    Main entry point for the Auth Lambda function
    """
    try:
        # Extract path and HTTP method
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        
        # Route request to appropriate handler
        if path.endswith('/auth/login') and http_method == 'POST':
            return handle_login(event)
        elif path.endswith('/auth/register') and http_method == 'POST':
            return handle_register(event)
        elif path.endswith('/auth/refresh') and http_method == 'POST':
            return handle_refresh(event)
        else:
            return build_response(404, {'error': 'Not found'})
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return build_response(500, {'error': 'Internal server error'})

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
        response = users_table.get_item(
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
        response = users_table.get_item(
            Key={'email': email}
        )
        
        if 'Item' in response:
            return build_response(409, {'error': 'Email already exists'})
        
        # Validate password
        if len(password) < 8:
            return build_response(400, {'error': 'Password must be at least 8 characters'})
        
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
        users_table.put_item(Item=user)
        
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
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except:
            return build_response(401, {'error': 'Invalid token'})
        
        # Get user from database
        user_id = payload.get('user_id')
        email = payload.get('email')
        
        if not user_id or not email:
            return build_response(401, {'error': 'Invalid token'})
        
        # Get user from DynamoDB
        response = users_table.get_item(
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

# Helper functions
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
    
    
    """   Funzioni buttate
    
    def handle_password_change(event):

    #Handle password change
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        current_password = request_body.get('current_password')
        new_password = request_body.get('new_password')
        
        if not current_password or not new_password:
            return build_response(400, {'error': 'Current password and new password are required'})
        
        # Verify current password
        if not verify_password(current_password, user.get('password_hash'), user.get('salt')):
            return build_response(401, {'error': 'Current password is incorrect'})
        
        # Validate new password
        if len(new_password) < 8:
            return build_response(400, {'error': 'New password must be at least 8 characters'})
        
        # Generate new password hash
        salt = generate_salt()
        password_hash = hash_password(new_password, salt)
        
        # Update user record
        users_table.update_item(
            Key={'email': user.get('email')},
            UpdateExpression='SET password_hash = :ph, salt = :s, updated_at = :u',
            ExpressionAttributeValues={
                ':ph': password_hash,
                ':s': salt,
                ':u': int(time.time())
            }
        )
        
        return build_response(200, {'message': 'Password updated successfully'})
    
    except Exception as e:
        print(f"Password change error: {str(e)}")
        return build_response(500, {'error': 'Error changing password'})

def handle_profile_update(event):
    # Handle profile update

    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        name = request_body.get('name')
        
        if not name:
            return build_response(400, {'error': 'Name is required'})
        
        # Update user record
        users_table.update_item(
            Key={'email': user.get('email')},
            UpdateExpression='SET #name = :n, updated_at = :u',
            ExpressionAttributeNames={
                '#name': 'name'  # 'name' is a reserved word in DynamoDB
            },
            ExpressionAttributeValues={
                ':n': name,
                ':u': int(time.time())
            }
        )
        
        # Get updated user
        response = users_table.get_item(
            Key={'email': user.get('email')}
        )
        
        updated_user = response.get('Item', {})
        
        return build_response(200, {
            'user': {
                'id': updated_user.get('user_id'),
                'name': updated_user.get('name'),
                'email': updated_user.get('email'),
                'created_at': updated_user.get('created_at')
            }
        })
    
    except Exception as e:
        print(f"Profile update error: {str(e)}")
        return build_response(500, {'error': 'Error updating profile'})

    """