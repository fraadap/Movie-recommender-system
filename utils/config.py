"""
Shared Configuration Module for Movie Recommendation System
Centralizes all environment variable loading and configuration management
"""
import os

class Config:
    """
    Centralized configuration management for all Lambda functions
    Loads environment variables once and makes them available across the application
    """
    
    # JWT Configuration
    JWT_SECRET = os.getenv('JWT_SECRET')
    JWT_EXPIRY = int(os.getenv('JWT_EXPIRY', '7200'))  # 2 hours in seconds
    
    # DynamoDB Table Names
    USERS_TABLE = os.getenv('USERS_TABLE', 'MovieRecommender_Users')
    FAVORITES_TABLE = os.getenv('FAVORITES_TABLE', 'MovieRecommender_Favorites')
    ACTIVITY_TABLE = os.getenv('ACTIVITY_TABLE', 'MovieRecommender_Activity')
    REVIEWS_TABLE = os.getenv('REVIEWS_TABLE', 'Reviews')
    MOVIES_TABLE = os.getenv('MOVIES_TABLE', 'Movies')
    
    # S3 Configuration for Embeddings
    EMBEDDINGS_BUCKET = os.getenv('EMBEDDINGS_BUCKET', 'movieembeddings')
    EMBEDDINGS_OUTPUT_FILE = os.getenv('EMBEDDINGS_OUTPUT_FILE', 'embeddings.npy')
    
    # ML Model Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    
    # API Configuration
    MAX_RESULTS = int(os.getenv('MAX_RESULTS', '100'))
    DEFAULT_TOP_K = int(os.getenv('DEFAULT_TOP_K', '10'))
    
    # Feature Flags
    ENABLE_ACTIVITY_LOGGING = os.getenv('ENABLE_ACTIVITY_LOGGING', 'true').lower() == 'true'
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*')
    ALLOWED_METHODS = os.getenv('ALLOWED_METHODS', 'GET,POST,PUT,DELETE,OPTIONS')
    ALLOWED_HEADERS = os.getenv('ALLOWED_HEADERS', 'Content-Type,Authorization')
    
    @classmethod
    def validate_required_config(cls):
        """
        Validate that all required configuration values are present
        Should be called during application startup
        """
        required_vars = []
        
        # Check critical configuration
        if not cls.JWT_SECRET or cls.JWT_SECRET == 'P1ywar3K75qD4dfGBFjsJrfbQRLixtZBZKPPYZjJFbQej9pqudua23GDICpfOVihN_2zHdU-hU1pVl57rXAu3Q':
            required_vars.append('JWT_SECRET')
        
        # For production, embeddings bucket should be configured
        if not cls.EMBEDDINGS_BUCKET:
            print("WARNING: EMBEDDINGS_BUCKET not configured - search functionality may not work")
        
        if required_vars:
            error_msg = f"Missing required environment variables: {', '.join(required_vars)}"
            print(f"ERROR: {error_msg}")
            if not cls.DEBUG_MODE:  # In production, fail fast
                raise ValueError(error_msg)
        
        return True
    
    @classmethod
    def get_cors_headers(cls):
        """Get CORS headers for API responses"""
        return {
            'Access-Control-Allow-Origin': cls.ALLOWED_ORIGINS,
            'Access-Control-Allow-Headers': cls.ALLOWED_HEADERS,
            'Access-Control-Allow-Methods': cls.ALLOWED_METHODS,
            'Content-Type': 'application/json'
        }
    
    @classmethod
    def print_config_summary(cls):
        """Print non-sensitive configuration for debugging"""
        if cls.DEBUG_MODE:
            print("=== Configuration Summary ===")
            print(f"Users Table: {cls.USERS_TABLE}")
            print(f"Movies Table: {cls.MOVIES_TABLE}")
            print(f"Reviews Table: {cls.REVIEWS_TABLE}")
            print(f"Favorites Table: {cls.FAVORITES_TABLE}")
            print(f"Activity Table: {cls.ACTIVITY_TABLE}")
            print(f"Embeddings Bucket: {cls.EMBEDDINGS_BUCKET}")
            print(f"Embedding Model: {cls.EMBEDDING_MODEL}")
            print(f"Max Results: {cls.MAX_RESULTS}")
            print(f"Activity Logging: {cls.ENABLE_ACTIVITY_LOGGING}")
            print("============================")


# Validate configuration on module import
try:
    Config.validate_required_config()
    Config.print_config_summary()
except Exception as e:
    print(f"Configuration validation failed: {e}")
    # Don't fail completely in case this is a development/test environment
