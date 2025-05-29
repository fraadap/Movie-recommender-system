"""
Database connection and table management module
Provides centralized access to DynamoDB tables using shared configuration
"""
import boto3
from .config import Config

# Initialize DynamoDB resource with optional endpoint URL for local development
def get_dynamodb_resource():
    """Get DynamoDB resource with proper configuration"""
    if Config.DYNAMODB_ENDPOINT_URL:
        return boto3.resource('dynamodb', endpoint_url=Config.DYNAMODB_ENDPOINT_URL)
    return boto3.resource('dynamodb')

# Initialize DynamoDB resource
dynamodb = get_dynamodb_resource()

# Table instances using centralized configuration
users_table = dynamodb.Table(Config.USERS_TABLE)
favorites_table = dynamodb.Table(Config.FAVORITES_TABLE)
activity_table = dynamodb.Table(Config.ACTIVITY_TABLE)
reviews_table = dynamodb.Table(Config.REVIEWS_TABLE)
movies_table = dynamodb.Table(Config.MOVIES_TABLE)

# Table mapping for dynamic access
TABLES = {
    'users': users_table,
    'favorites': favorites_table,
    'activity': activity_table,
    'reviews': reviews_table,
    'movies': movies_table
}

def get_table(table_name):
    """
    Get table instance by name
    Args:
        table_name: Name of the table ('users', 'favorites', 'activity', 'reviews', 'movies')
    Returns:
        DynamoDB table instance
    """
    return TABLES.get(table_name.lower())

def health_check():
    """
    Perform basic health check on database connections
    Returns:
        dict: Health status of each table
    """
    health_status = {}
    
    for name, table in TABLES.items():
        try:
            # Try to describe the table (lightweight operation)
            table.table_status
            health_status[name] = 'healthy'
        except Exception as e:
            health_status[name] = f'error: {str(e)}'
    
    return health_status