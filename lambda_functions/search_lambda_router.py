import json
import os
import search_lambda as search_engine
import logging
import jwt
from boto3.dynamodb.conditions import Key
import boto3

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'MovieRecommender_Users'))

# JWT secret - in production, use AWS Secrets Manager
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-key')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Main entry point for the Lambda function.
    Routes requests based on the path or operation parameter.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Extract path from API Gateway event
    path = None
    if event.get('resource'):
        path = event.get('path', '').strip('/')
    
    # Parse request body
    request_body = {}
    if event.get('body'):
        try:
            # Parse the body from API Gateway
            request_body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return build_response(400, {'error': 'Invalid JSON in request body'})
    elif event.get('operation') or path == 'recommend':
        # Direct Lambda invocation or generic endpoint
        request_body = event
    
    # Determine operation from path or body
    operation = None
    if path in ['search', 'content', 'collaborative']:
        operation = path
    else:
        operation = request_body.get('operation')
    
    # If no operation found, return error
    if not operation:
        return build_response(400, {'error': 'Missing operation parameter'})
    
    # Extract common parameters
    top_k = int(request_body.get('top_k', 10))
    
    # Route to appropriate handler
    try:
        if operation == 'search':
            query = request_body.get('query')
            if not query:
                return build_response(400, {'error': 'Missing query parameter'})
            result = search_engine.recommend_semantic(query, top_k)
            
        elif operation == 'content':
            # Handle both movieId (single) and movie_ids (array) for flexibility
            movie_ids = request_body.get('movie_ids', [])
            
            # Support for movieId coming from frontend
            single_movie_id = request_body.get('movieId')
            if single_movie_id and not movie_ids:
                movie_ids = [single_movie_id]
                
            if not movie_ids:
                return build_response(400, {'error': 'Missing movie_ids parameter'})
                
            result = search_engine.recommend_content(movie_ids, top_k)
            
        elif operation == 'collaborative':
            # Get authenticated user
            user = get_authenticated_user(event)
            if not user:
                return build_response(401, {'error': 'Authentication required'})
            
            user_id = user.get('user_id')
            result = search_engine.recommend_collaborative(user_id, top_k)
            
        else:
            return build_response(400, {'error': f'Invalid operation: {operation}'})
        
        # Load metadata for each result
        movies = []
        for movie_id, score in result:
            movie = get_movie_metadata(movie_id)
            if movie:
                movie['score'] = score
                movies.append(movie)
        
        # Return successful response
        return build_response(200, movies)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return build_response(500, {'error': f'Server error: {str(e)}'})

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

def get_movie_metadata(movie_id):
    """Fetch movie metadata from DynamoDB"""
    try:
        db = search_engine.get_dynamodb()
        table = db.Table(os.getenv("DYNAMODB_TABLE", "Movies"))
        resp = table.get_item(Key={'movie_id': str(movie_id)})
        return resp.get('Item')
    except Exception as e:
        logger.error(f"Error fetching movie {movie_id}: {str(e)}")
        return None

def build_response(status_code, body):
    """
    Build API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(body)
    }

def get_cors_headers():
    """Get CORS headers for responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Content-Type': 'application/json'
    }