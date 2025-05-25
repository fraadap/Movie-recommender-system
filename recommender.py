"""Recommendation algorithms for Movie Recommender System."""

import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import os
import json
import logging
from database import DatabaseHandler

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """Movie recommendation engine implementing multiple recommendation strategies."""
    
    def __init__(self, db_handler: DatabaseHandler):
        """
        Initialize recommendation engine.
        
        Args:
            db_handler: Database handler instance
        """
        self.db = db_handler
        self.model = None
        self.embeddings = {}
        
    def _load_model(self):
        """Lazy load the embedding model."""
        if self.model is None:
            model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            self.model = SentenceTransformer(model_name)
            
    def _load_embeddings(self):
        """Load movie embeddings from S3."""
        if not self.embeddings:
            try:
                s3 = boto3.client('s3')
                bucket = os.getenv('EMBEDDINGS_BUCKET', 'movie-embeddings')
                key = os.getenv('EMBEDDINGS_OUTPUT_FILE', 'embeddings.jsonl')
                
                response = s3.get_object(Bucket=bucket, Key=key)
                content = response['Body'].read().decode('utf-8')
                
                for line in content.splitlines():
                    item = json.loads(line)
                    self.embeddings[item['movie_id']] = np.array(item['embedding'])
                    
            except Exception as e:
                logger.error(f"Error loading embeddings: {e}")
                raise
                
    def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Perform semantic search based on query text.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of movie recommendations with scores
        """
        self._load_model()
        self._load_embeddings()
        
        # Generate query embedding
        query_embedding = self.model.encode(query)
        
        # Calculate similarities
        similarities = []
        for movie_id, embedding in self.embeddings.items():
            similarity = self._cosine_similarity(query_embedding, embedding)
            similarities.append((movie_id, similarity))
            
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k movies
        results = []
        for movie_id, score in similarities[:top_k]:
            movie = self.db.get_movie(movie_id)
            if movie:
                movie['score'] = float(score)
                results.append(movie)
                
        return results
        
    def content_based_recommendations(self, movie_ids: List[str], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Get content-based recommendations based on a list of movie IDs.
        
        Args:
            movie_ids: List of movie IDs to base recommendations on
            top_k: Number of recommendations to return
            
        Returns:
            List of movie recommendations with scores
        """
        self._load_embeddings()
        
        if not movie_ids:
            return []
            
        # Calculate average embedding of input movies
        embeddings = [self.embeddings[mid] for mid in movie_ids if mid in self.embeddings]
        if not embeddings:
            return []
            
        avg_embedding = np.mean(embeddings, axis=0)
        
        # Calculate similarities
        similarities = []
        for movie_id, embedding in self.embeddings.items():
            if movie_id not in movie_ids:  # Exclude input movies
                similarity = self._cosine_similarity(avg_embedding, embedding)
                similarities.append((movie_id, similarity))
                
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k movies
        results = []
        for movie_id, score in similarities[:top_k]:
            movie = self.db.get_movie(movie_id)
            if movie:
                movie['score'] = float(score)
                results.append(movie)
                
        return results
        
    def collaborative_recommendations(self, user_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Get collaborative filtering recommendations for a user.
        
        Args:
            user_id: User ID to get recommendations for
            top_k: Number of recommendations to return
            
        Returns:
            List of movie recommendations with scores
        """
        # Get user's ratings
        user_ratings = {r['movie_id']: r['rating'] for r in self.db.get_user_ratings(user_id)}
        if not user_ratings:
            return []
            
        # Find similar users
        similar_users = self._find_similar_users(user_id, user_ratings)
        
        # Get recommendations from similar users
        recommendations = {}
        for sim_user_id, similarity in similar_users:
            sim_user_ratings = self.db.get_user_ratings(sim_user_id)
            for rating in sim_user_ratings:
                movie_id = rating['movie_id']
                if movie_id not in user_ratings:  # Only recommend unwatched movies
                    if movie_id not in recommendations:
                        recommendations[movie_id] = {'total': 0, 'count': 0}
                    recommendations[movie_id]['total'] += rating['rating'] * similarity
                    recommendations[movie_id]['count'] += similarity
                    
        # Calculate average scores
        scored_movies = []
        for movie_id, data in recommendations.items():
            if data['count'] > 0:
                score = data['total'] / data['count']
                movie = self.db.get_movie(movie_id)
                if movie:
                    movie['score'] = float(score)
                    scored_movies.append(movie)
                    
        # Sort by score and return top-k
        scored_movies.sort(key=lambda x: x['score'], reverse=True)
        return scored_movies[:top_k]
        
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        
    def _find_similar_users(self, user_id: str, user_ratings: Dict[str, float]) -> List[Tuple[str, float]]:
        """Find users with similar rating patterns."""
        similarities = []
        
        # Get all ratings for movies rated by the user
        movie_ratings = {}
        for movie_id in user_ratings:
            ratings = self.db.get_movie_reviews(movie_id)
            for rating in ratings:
                other_user_id = rating['user_id']
                if other_user_id != user_id:
                    if other_user_id not in movie_ratings:
                        movie_ratings[other_user_id] = {}
                    movie_ratings[other_user_id][movie_id] = rating['rating']
                    
        # Calculate similarities
        for other_user_id, other_ratings in movie_ratings.items():
            # Get common movies
            common_movies = set(user_ratings.keys()) & set(other_ratings.keys())
            
            # Create rating vectors
            u1 = [user_ratings[m] for m in common_movies]
            u2 = [other_ratings[m] for m in common_movies]
            
            # Calculate similarity
            similarity = self._cosine_similarity(np.array(u1), np.array(u2))
            similarities.append((other_user_id, similarity))
            
        # Sort by similarity and return top users
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:50]  # Return top 50 similar users
