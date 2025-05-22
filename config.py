"""
Configuration settings for the Movie Recommender System.
This module centralizes all configuration parameters used across the application.
"""

import os

# AWS Service Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
DYNAMODB_ENDPOINT_URL = os.getenv('DYNAMODB_ENDPOINT_URL', 'http://localhost:8000')
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', 'http://localhost:4566')

# DynamoDB Tables
MOVIES_TABLE = os.getenv('DYNAMODB_TABLE', 'Movies')
REVIEWS_TABLE = os.getenv('REVIEWS_TABLE', 'Reviews')
USERS_TABLE = os.getenv('USERS_TABLE', 'MovieRecommender_Users')
FAVORITES_TABLE = os.getenv('FAVORITES_TABLE', 'MovieRecommender_Favorites')
WATCHED_TABLE = os.getenv('WATCHED_TABLE', 'MovieRecommender_Watched')
PREFERENCES_TABLE = os.getenv('PREFERENCES_TABLE', 'MovieRecommender_Preferences')
ACTIVITY_TABLE = os.getenv('ACTIVITY_TABLE', 'MovieRecommender_Activity')

# S3 Configuration
EMBEDDINGS_BUCKET = os.getenv('EMBEDDINGS_BUCKET', 'movie-embeddings')
EMBEDDINGS_OUTPUT_FILE = os.getenv('EMBEDDINGS_OUTPUT_FILE', 'embeddings.jsonl')

# Model Configuration
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')

# API Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'local-dev-secret-key')
TOKEN_EXPIRY = int(os.getenv('TOKEN_EXPIRY', '86400'))  # 24 hours in seconds

# Local Development Settings
LOCAL_MOVIES_CSV = os.getenv('MOVIES_CSV', 'movies_metadata.csv')
LOCAL_CREDITS_CSV = os.getenv('CREDITS_CSV', 'credits.csv')
LOCAL_RATINGS_CSV = os.getenv('RATINGS_CSV', 'ratings.csv')

# API Gateway Configuration
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://localhost:5000')
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

# Feature Flags
ENABLE_RECOMMENDATIONS = os.getenv('ENABLE_RECOMMENDATIONS', 'true').lower() == 'true'
ENABLE_SEARCH = os.getenv('ENABLE_SEARCH', 'true').lower() == 'true'
ENABLE_FAVORITES = os.getenv('ENABLE_FAVORITES', 'true').lower() == 'true'
ENABLE_WATCHED = os.getenv('ENABLE_WATCHED', 'true').lower() == 'true'
