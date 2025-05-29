import json
import os
import search_lambda as search_engine

from utils.utils_function import get_authenticated_user, build_response
import utils.database as db

# JWT secret - in production, use AWS Secrets Manager
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-key')

def lambda_handler(event, context):
    """
    Main entry point for the Search Lambda function
    """
    try:
        # Extract path and HTTP method
        path = event.get('path', '').strip('/')
        http_method = event.get('httpMethod', '')
        
        # Route request to appropriate handler
        if path == 'search' and http_method == 'POST':
            return handle_semantic_search(event)
        elif path == 'content' and http_method == 'POST':
            return handle_content_based_search(event)
        elif path == 'collaborative' and http_method == 'POST':
            return handle_collaborative_search(event)
        elif path == 'similar' and http_method == 'POST':
            return handle_similar_search(event)
        else:
            return build_response(404, {'error': 'Not found'})
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return build_response(500, {'error': 'Internal server error'})


def handle_semantic_search(event):
    """
    Handle semantic search request
    """
    try:
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        query = request_body.get('query')
        top_k = int(request_body.get('top_k', 10))
        
        if not query:
            return build_response(400, {'error': 'Query is required'})
        
        # Perform semantic search
        result = search_engine.recommend_semantic(query, top_k)
        
        # Load metadata for each result
        movies = []
        for movie_id, score in result:
            movie = get_movie_metadata(movie_id)
            if movie:
                movie['score'] = score
                movies.append(movie)
        
        return build_response(200, movies)
        
    except json.JSONDecodeError:
        return build_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        print(f"Semantic search error: {str(e)}")
        return build_response(500, {'error': 'Error performing semantic search'})


def handle_content_based_search(event):
    """
    Handle content-based search request
    """
    try:
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        movie_ids = request_body.get('movie_ids', [])
        top_k = int(request_body.get('top_k', 10))
        
        if not movie_ids:
            return build_response(400, {'error': 'Movie IDs are required'})
        
        # Perform content-based search
        result = search_engine.recommend_content(movie_ids, top_k)
        
        # Load metadata for each result
        movies = []
        for movie_id, score in result:
            movie = get_movie_metadata(movie_id)
            if movie:
                movie['score'] = score
                movies.append(movie)
        
        return build_response(200, movies)
        
    except json.JSONDecodeError:
        return build_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        print(f"Content-based search error: {str(e)}")
        return build_response(500, {'error': 'Error performing content-based search'})


def handle_collaborative_search(event):
    """
    Handle collaborative filtering search request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        top_k = int(request_body.get('top_k', 10))
        
        user_id = user.get('user_id')
        
        # Perform collaborative filtering
        result = search_engine.recommend_collaborative(user_id, top_k)
        
        # Load metadata for each result
        movies = []
        for movie_id, score in result:
            movie = get_movie_metadata(movie_id)
            if movie:
                movie['score'] = score
                movies.append(movie)
        
        return build_response(200, movies)
        
    except json.JSONDecodeError:
        return build_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        print(f"Collaborative search error: {str(e)}")
        return build_response(500, {'error': 'Error performing collaborative search'})


def handle_similar_search(event):
    """
    Handle similar movies search request
    """
    try:
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        movie_id = request_body.get('movie_id')
        top_k = int(request_body.get('top_k', 10))
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        # Perform similar movie search
        result = search_engine.recommend_similar(movie_id, top_k)
        
        # Load metadata for each result
        movies = []
        for similar_movie_id, score in result:
            movie = get_movie_metadata(similar_movie_id)
            if movie:
                movie['score'] = score
                movies.append(movie)
        
        return build_response(200, movies)
        
    except json.JSONDecodeError:
        return build_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        print(f"Similar search error: {str(e)}")
        return build_response(500, {'error': 'Error performing similar movie search'})


def get_movie_metadata(movie_id):
    """
    Fetch movie metadata from DynamoDB
    """
    try:
        resp = db.movies_table.get_item(Key={'movie_id': str(movie_id)})
        return resp.get('Item')
    except Exception as e:
        print(f"Error fetching movie metadata for {movie_id}: {str(e)}")
        return None