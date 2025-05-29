import json
import os
import search_lambda as search_engine
import logging
import jwt
from boto3.dynamodb.conditions import Key
import boto3

from utils.auth import get_authenticated_user
from utils.auth import get_cors_headers

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
    
    path = event.get('path', '').strip('/')
    
    # Parse request body
    request_body = {}
    if event.get('body'):
        try:
            # Parse the body from API Gateway
            request_body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return build_response(400, {'error': 'Invalid JSON in request body'})
    else:
        return build_response(400, {'error': 'Invalid JSON in request body'})
    
    # Determine operation from path or body
    operation = None
    if path in ['search', 'content', 'collaborative', 'similar']:
        operation = path
    else:
        return build_response(400, {'error': 'Invalid path'})
        
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
            # Taking the tuples of (movie_ids, rating)
            movie_ids = request_body.get('movie_ids', [])
                
            if not movie_ids:
                return build_response(400, {'error': 'Missing movie_ids parameter'})
                
            result = search_engine.recommend_content(movie_ids, top_k)
            
        elif operation == 'collaborative':
            # Get the user by the token
            user = get_authenticated_user(event)
            if not user:
                return build_response(401, {'error': 'Authentication required'})
            
            user_id = user.get('user_id')
            result = search_engine.recommend_collaborative(user_id, top_k)

        elif operation == 'similar':
            movie_id = request_body.get('movie_id')
            if not movie_id:
                return build_response(400, {'error': 'Missing movie_id parameter for similar operation'})
            
            result = search_engine.recommend_similar(movie_id, top_k)

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