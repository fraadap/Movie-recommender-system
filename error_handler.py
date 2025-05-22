"""Error handling utilities for Movie Recommender System."""

from typing import Dict, Any, Type, Optional
import logging
import traceback

logger = logging.getLogger(__name__)

class MovieRecommenderError(Exception):
    """Base exception class for Movie Recommender System."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code
        self.message = message

class AuthenticationError(MovieRecommenderError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class AuthorizationError(MovieRecommenderError):
    """Raised when user doesn't have required permissions."""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)

class ValidationError(MovieRecommenderError):
    """Raised when input validation fails."""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=400)

class NotFoundError(MovieRecommenderError):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class DatabaseError(MovieRecommenderError):
    """Raised when database operations fail."""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=500)

def handle_error(error: Exception) -> Dict[str, Any]:
    """Convert exceptions to API responses with appropriate status codes."""
    if isinstance(error, MovieRecommenderError):
        status_code = error.status_code
        message = error.message
    else:
        status_code = 500
        message = "Internal server error"
        
    # Log the full error for server-side debugging
    logger.error(f"Error: {str(error)}")
    logger.error(traceback.format_exc())
    
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Content-Type': 'application/json'
        },
        'body': {
            'error': message
        }
    }

def validate_input(data: Dict[str, Any], required_fields: Dict[str, Type]) -> Optional[str]:
    """
    Validate input data against required fields and their types.
    Returns None if valid, error message if invalid.
    """
    for field, field_type in required_fields.items():
        if field not in data:
            return f"Missing required field: {field}"
            
        if not isinstance(data[field], field_type):
            return f"Invalid type for field {field}. Expected {field_type.__name__}"
            
    return None

def safe_execute(func):
    """Decorator to handle exceptions and convert them to API responses."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return handle_error(e)
    return wrapper
