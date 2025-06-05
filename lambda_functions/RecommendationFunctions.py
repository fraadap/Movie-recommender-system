import json
from boto3.dynamodb.conditions import Key
import numpy as np
import boto3
import os
import tempfile
import onnxruntime
from tokenizers import Tokenizer

from utils.config import Config
from utils.utils_function import get_authenticated_user, build_response, get_item_converted
import utils.database as db

# Global variables for caching
_embeddings = None
_model = None
_tokenizer = None
_model_config = None
_onnx_session = None
_s3_client = None
_dynamodb = None

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

        movies = get_item_converted(movies)
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

        movies = get_item_converted(movies)
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

        movies = get_item_converted(movies)
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
        movies = get_item_converted(movies)
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
        movie = resp.get('Item')
        movie = get_item_converted(movie)
        return movie
    except Exception as e:
        print(f"Error fetching movie metadata for {movie_id}: {str(e)}")
        return None
    
    
# Recommendation functions

def recommend_semantic(query, top_k):
    """
    Recommend movies based on semantic similarity to query using ONNX model
    """
    try:
        # Get ONNX model components
        onnx_session, tokenizer, model_config = get_model()
        
        # Encode the query using the ONNX model
        encoded = tokenizer.encode(query)
        
        # Prepare inputs for ONNX model
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        token_type_ids = np.array([encoded.type_ids], dtype=np.int64)
        
        onnx_inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids
        }
        
        # Run inference
        onnx_outputs = onnx_session.run(None, onnx_inputs)
        
        # Extract embeddings (typically from last hidden state)
        # For sentence transformers, we usually take the mean of token embeddings
        last_hidden_state = onnx_outputs[0]  # Shape: (batch_size, seq_len, hidden_size)
        
        # Apply attention mask and compute mean pooling
        attention_mask_expanded = np.expand_dims(attention_mask, -1)
        masked_embeddings = last_hidden_state * attention_mask_expanded
        sum_embeddings = np.sum(masked_embeddings, axis=1)
        sum_mask = np.sum(attention_mask, axis=1, keepdims=True)
        query_embedding = (sum_embeddings / np.maximum(sum_mask, 1e-9))[0]  # Take first batch item
        
        # Normalize the embedding
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_emb = query_embedding.tolist()
        
        # Compare with precomputed embeddings
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
        results = get_item_converted(results)
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
    """
    Load ONNX model, tokenizer, and config from S3
    """
    global _onnx_session, _tokenizer, _model_config
    
    if _onnx_session is None or _tokenizer is None or _model_config is None:
        try:
            if not Config.MODEL_BUCKET:
                raise ValueError("MODEL_BUCKET not configured")
            
            s3 = get_s3_client()
            
            # Create temporary directory for model files
            temp_dir = tempfile.mkdtemp()
            
            try:
                # Download model config
                config_path = os.path.join(temp_dir, "config.json")
                s3.download_file(Config.MODEL_BUCKET, Config.MODEL_CONFIG_FILE, config_path)
                
                with open(config_path, 'r', encoding='utf-8') as f:
                    _model_config = json.load(f)
                
                # Download tokenizer
                tokenizer_path = os.path.join(temp_dir, "tokenizer.json")
                s3.download_file(Config.MODEL_BUCKET, Config.MODEL_TOKENIZER_FILE, tokenizer_path)
                
                _tokenizer = Tokenizer.from_file(tokenizer_path)
                  # Configure tokenizer padding and truncation
                max_seq_length = _model_config.get("max_position_embeddings", 128)
                pad_token_id = _tokenizer.token_to_id("[PAD]")
                if pad_token_id is None:
                    print("Warning: '[PAD]' token not found. Assuming ID 0 for padding.")
                    pad_token_id = 0
                
                _tokenizer.enable_truncation(max_length=max_seq_length)
                _tokenizer.enable_padding(
                    direction='right',
                    length=max_seq_length,
                    pad_id=pad_token_id,
                    pad_token='[PAD]',
                    pad_type_id=0
                )
                
                # Download and load ONNX model
                model_path = os.path.join(temp_dir, "model.onnx")
                s3.download_file(Config.MODEL_BUCKET, Config.MODEL_ONNX_FILE, model_path)
                
                _onnx_session = onnxruntime.InferenceSession(
                    model_path, 
                    providers=['CPUExecutionProvider']
                )
                
                print("ONNX model, tokenizer, and config loaded successfully from S3")
                
            finally:
                # Clean up temporary files
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    print(f"Warning: Could not clean up temp directory: {cleanup_error}")
            
        except Exception as e:
            print(f"Error loading ONNX model from S3: {str(e)}")
            raise
    
    return _onnx_session, _tokenizer, _model_config


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3")
    return _s3_client


def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb


def cosine_similarity(a, b):
    a_np = np.array(a)
    b_np = np.array(b)
    denom = (np.linalg.norm(a_np) * np.linalg.norm(b_np))
    return float(np.dot(a_np, b_np) / denom) if denom != 0 else 0.0
