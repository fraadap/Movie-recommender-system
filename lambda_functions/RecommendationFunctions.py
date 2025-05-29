import json
import os
from boto3.dynamodb.conditions import Key
import numpy as np
import boto3
from sentence_transformers import SentenceTransformer

from utils.config import Config
from utils.utils_function import get_authenticated_user, build_response
import utils.database as db

# Global variables for caching
_embeddings = None
_model = None
_s3_client = None
_dynamodb = None

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
        result = recommend_semantic(query, top_k)
        
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
        result = recommend_content(movie_ids, top_k)
        
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
        result = recommend_collaborative(user_id, top_k)
        
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
        result = recommend_similar(movie_id, top_k)
        
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
    
    
# Recommendation functions

def recommend_semantic(query, top_k):
    """
    Recommend movies based on semantic similarity to query
    """
    try:
        model = get_model()
        query_emb = model.encode(query).tolist()
        embed_map = load_embeddings()
        sims = [(mid, cosine_similarity(query_emb, emb)) for mid, emb in embed_map.items()]
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:top_k]
    except Exception as e:
        print(f"Error in semantic recommendation: {str(e)}")
        raise


def recommend_content(movie_ids, top_k):
    """
    Recommend movies based on content similarity to user's rated movies
    """
    try:
        embed_map = load_embeddings()

        filtered = [(mid, rating) for mid, rating in movie_ids if mid in embed_map]
        if not filtered:
            return []
        # Estrai gli embedding e i rating
        vectors = [embed_map[mid] for mid, _ in filtered]
        weights = [rating for _, rating in filtered]
        # Calcolo della media pesata degli embedding
        weighted_vectors = np.array(vectors) * np.array(weights)[:, None]  # shape: (n, d)
        avg_emb = np.sum(weighted_vectors, axis=0) / np.sum(weights) #shape: (d,)

        seen_ids = set(mid for mid, _ in movie_ids)
        sims = [(mid, cosine_similarity(avg_emb, emb)) for mid, emb in embed_map.items() if mid not in seen_ids]
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:top_k]
    except Exception as e:
        print(f"Error in content-based recommendation: {str(e)}")
        raise
    

def recommend_similar(movie_id, top_k):
    """
    Recommend movies similar to a given movie
    """
    try:
        embed_map = load_embeddings()
        if movie_id not in embed_map:
            return []
        vector = embed_map[movie_id]
        sims = [(mid, cosine_similarity(vector, emb)) for mid, emb in embed_map.items() if mid != movie_id]
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:top_k]
    except Exception as e:
        print(f"Error in similar movie recommendation: {str(e)}")
        raise


def recommend_collaborative(user_id, top_k):
    """
    Recommend movies using collaborative filtering
    """
    try:
        dynamodb = get_dynamodb()
        reviews_tbl = dynamodb.Table(Config.REVIEWS_TABLE)
        resp = reviews_tbl.query(KeyConditionExpression=Key('user_id').eq(str(user_id)))
        user_ratings = {item['movie_id']: float(item['rating']) for item in resp.get('Items', [])}
        
        if not user_ratings:
            return []
            
        other_users = {}
        for mid in user_ratings:
            resp_movies = reviews_tbl.query(IndexName='MovieIndex', KeyConditionExpression=Key('movie_id').eq(str(mid)))
            for itm in resp_movies.get('Items', []):
                other = itm['user_id']
                rating = float(itm['rating'])
                if other == str(user_id): 
                    continue
                other_users.setdefault(other, {})[mid] = rating
                
        sims_users = []
        for other, ratings in other_users.items():
            common = set(ratings.keys()) & set(user_ratings.keys())
            if len(common) < 2: 
                continue
            u = np.array([user_ratings[m] for m in common])
            v = np.array([ratings[m] for m in common])
            denom = (np.linalg.norm(u) * np.linalg.norm(v))
            sim = float(np.dot(u, v) / denom) if denom != 0 else 0.0
            if sim > 0:
                sims_users.append((other, sim))
                
        sims_users.sort(key=lambda x: x[1], reverse=True)
        top_users = [u for u, _ in sims_users[:10]]
        
        scores = {}
        weights = {}
        for other in top_users:
            sim_score = dict(sims_users)[other]
            resp_user = reviews_tbl.query(KeyConditionExpression=Key('user_id').eq(other))
            for itm in resp_user.get('Items', []):
                mid = itm['movie_id']
                if mid in user_ratings: 
                    continue
                r = float(itm['rating'])
                scores[mid] = scores.get(mid, 0.0) + sim_score * r
                weights[mid] = weights.get(mid, 0.0) + sim_score
                
        results = [(mid, scores[mid] / weights[mid]) for mid in scores if weights.get(mid, 0) > 0]
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    except Exception as e:
        print(f"Error in collaborative filtering recommendation: {str(e)}")
        raise
    
# Utility functions


def load_embeddings():
    """
    Load embeddings from S3 bucket
    """
    global _embeddings
    if _embeddings is None:
        try:
            if not Config.EMBEDDINGS_BUCKET:
                raise ValueError("EMBEDDINGS_BUCKET not configured")
            s3 = get_s3_client()
            obj = s3.get_object(Bucket=Config.EMBEDDINGS_BUCKET, Key=Config.EMBEDDINGS_OUTPUT_FILE)
            temp = {}
            for line in obj["Body"].iter_lines():
                rec = json.loads(line.decode('utf-8'))
                temp[rec['movie_id']] = rec['embedding']
            _embeddings = temp
        except Exception as e:
            print(f"Error loading embeddings: {str(e)}")
            raise
    return _embeddings



def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(Config.EMBEDDING_MODEL)
    return _model


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", endpoint_url=Config.S3_ENDPOINT_URL) if Config.S3_ENDPOINT_URL else boto3.client("s3")
    return _s3_client


def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", endpoint_url=Config.DYNAMODB_ENDPOINT_URL) if Config.DYNAMODB_ENDPOINT_URL else boto3.resource("dynamodb")
    return _dynamodb


def cosine_similarity(a, b):
    a_np = np.array(a)
    b_np = np.array(b)
    denom = (np.linalg.norm(a_np) * np.linalg.norm(b_np))
    return float(np.dot(a_np, b_np) / denom) if denom != 0 else 0.0
