import os
import json
import boto3
import numpy as np
from sentence_transformers import SentenceTransformer
from boto3.dynamodb.conditions import Key

import utils.database as db

# Lazy-loaded resources
_model = None
_embeddings = None
_s3_client = None
_dynamodb = None

# Environment variables
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDINGS_BUCKET = os.getenv("EMBEDDINGS_BUCKET")
EMBEDDINGS_FILE = os.getenv("EMBEDDINGS_OUTPUT_FILE", "embeddings.jsonl")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "Movies")
REVIEWS_TABLE = os.getenv("REVIEWS_TABLE", "Reviews")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
DDB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT_URL")


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", endpoint_url=S3_ENDPOINT_URL) if S3_ENDPOINT_URL else boto3.client("s3")
    return _s3_client


def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", endpoint_url=DDB_ENDPOINT_URL) if DDB_ENDPOINT_URL else boto3.resource("dynamodb")
    return _dynamodb


def cosine_similarity(a, b):
    a_np = np.array(a)
    b_np = np.array(b)
    denom = (np.linalg.norm(a_np) * np.linalg.norm(b_np))
    return float(np.dot(a_np, b_np) / denom) if denom != 0 else 0.0


def load_embeddings():
    """
    Load embeddings from S3 bucket
    """
    global _embeddings
    if _embeddings is None:
        try:
            if not EMBEDDINGS_BUCKET:
                raise ValueError("EMBEDDINGS_BUCKET environment variable not set")
            s3 = get_s3_client()
            obj = s3.get_object(Bucket=EMBEDDINGS_BUCKET, Key=EMBEDDINGS_FILE)
            temp = {}
            for line in obj["Body"].iter_lines():
                rec = json.loads(line.decode('utf-8'))
                temp[rec['movie_id']] = rec['embedding']
            _embeddings = temp
        except Exception as e:
            print(f"Error loading embeddings: {str(e)}")
            raise
    return _embeddings


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
        reviews_tbl = dynamodb.Table(REVIEWS_TABLE)
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


def lambda_handler(event, context):
    """
    Testing handler - the actual routing is handled by search_lambda_router.py
    """
    try:
        op = event.get('operation')
        top_k = int(event.get('top_k', 10))
        
        if op == 'search':
            query = event.get('query')
            if not query:
                return {'statusCode': 400, 'body': json.dumps({'error': 'query is required'})}
            sims = recommend_semantic(query, top_k)
        elif op == 'content':
            mids = event.get('movie_ids', [])
            sims = recommend_content(mids, top_k)
        elif op == 'collaborative':
            uid = event.get('user_id')
            if not uid:
                return {'statusCode': 400, 'body': json.dumps({'error': 'user_id is required'})}
            sims = recommend_collaborative(uid, top_k)
        elif op == 'similar':
            movie_id = event.get('movie_id')
            if not movie_id:
                return {'statusCode': 400, 'body': json.dumps({'error': 'movie_id is required'})}
            sims = recommend_similar(movie_id, top_k)
        else:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid operation'})}
            
        results = []
        for mid, score in sims:
            movie = get_movie_metadata(mid)
            if movie:
                movie['score'] = score
                results.append(movie)
                
        return {'statusCode': 200, 'body': json.dumps(results)}
        
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal server error'})}