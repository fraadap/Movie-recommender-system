import json
import os
import search_lambda as search_engine
import logging

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
            return {
                'statusCode': 400,
                'headers': get_cors_headers(),
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
    elif event.get('operation') or path == 'recommend':
        # Direct Lambda invocation or generic endpoint
        request_body = event
    
    # Determine operation from path or body
    operation = None
    if path in ['search', 'content', 'collaborative', 'recommend']:
        operation = path
    else:
        operation = request_body.get('operation')
    
    # If no operation found, return error
    if not operation:
        return {
            'statusCode': 400,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': 'Missing operation parameter'})
        }
    
    # Extract common parameters
    top_k = int(request_body.get('top_k', 10))
    
    # Route to appropriate handler
    try:
        if operation == 'search':
            query = request_body.get('query')
            if not query:
                return error_response('Missing query parameter')
            result = search_engine.recommend_semantic(query, top_k)
            
        elif operation == 'content':
            # Handle both movieId (single) and movie_ids (array) for flexibility
            movie_ids = request_body.get('movie_ids', [])
            
            # Support for movieId coming from frontend
            single_movie_id = request_body.get('movieId')
            if single_movie_id and not movie_ids:
                movie_ids = [single_movie_id]
                
            if not movie_ids:
                return error_response('Missing movie_ids parameter')
                
            result = search_engine.recommend_content(movie_ids, top_k) # da controllare
            
        elif operation == 'collaborative':
            # Support both user_id and movieId parameters
            user_id = request_body.get('user_id')
            movie_id = request_body.get('movie_id')
            
            # If movieId is provided but not user_id, use movieId as the parameter
            if movie_id and not user_id:
                user_id = movie_id
                
            if not user_id:
                return error_response('Missing user_id or movie_id parameter')
                
            result = search_engine.recommend_collaborative(user_id, top_k)
            
        elif operation == 'recommend':
            # Questa operazione è superflua, fa una ricerca utilizzando il modello
            # Handle recommendations (can be based on history or genre preferences)
            # For now, just return popular movies if no specific parameters
            user_id = request_body.get('user_id')
            genre = request_body.get('genre')
            
            if user_id:
                # Personalized recommendations based on user history
                result = search_engine.recommend_collaborative(user_id, top_k)
            elif genre:
                # Genre-based recommendations
                result = search_engine.recommend_semantic(f"Movies in genre {genre}", top_k)
            else:
                # Default recommendations (popular movies)
                result = search_engine.recommend_semantic("Popular highly rated movies", top_k)
            
        else:
            return error_response(f'Invalid operation: {operation}')
        
        # Load metadata for each result
        movies = []
        for movie_id, score in result:
            movie = get_movie_metadata(movie_id)
            if movie:
                movie['score'] = score
                movies.append(movie)
        
        # Return successful response
        return {
            'statusCode': 200,
            'headers': get_cors_headers(),
            'body': json.dumps(movies)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': get_cors_headers(),
            'body': json.dumps({'error': f'Server error: {str(e)}'})
        }

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

def error_response(message, status_code=400):
    """Format an error response"""
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps({'error': message})
    }

def get_cors_headers():
    """Get CORS headers for responses"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Content-Type': 'application/json'
    } 