"""Database handler for Movie Recommender System."""

import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class DatabaseHandler:
    """Handles all database operations for the Movie Recommender System."""
    
    def __init__(self, endpoint_url=None):
        """Initialize database connections."""
        self.endpoint_url = endpoint_url or os.getenv('DYNAMODB_ENDPOINT_URL')
        self.dynamodb = self._get_dynamodb_resource()
        self.tables = {}
        self._initialize_tables()

    def _get_dynamodb_resource(self):
        """Get DynamoDB resource with appropriate configuration."""
        kwargs = {
            'region_name': os.getenv('AWS_REGION', 'us-east-1')
        }
        if self.endpoint_url:
            kwargs.update({
                'endpoint_url': self.endpoint_url,
                'aws_access_key_id': 'dummy',
                'aws_secret_access_key': 'dummy'
            })
        return boto3.resource('dynamodb', **kwargs)

    def _initialize_tables(self):
        """Initialize connections to all required tables."""
        table_names = {
            'movies': os.getenv('DYNAMODB_TABLE', 'Movies'),
            'reviews': os.getenv('REVIEWS_TABLE', 'Reviews'),
            'users': os.getenv('USERS_TABLE', 'MovieRecommender_Users'),
            'favorites': os.getenv('FAVORITES_TABLE', 'MovieRecommender_Favorites'),
            'watched': os.getenv('WATCHED_TABLE', 'MovieRecommender_Watched'),
            'preferences': os.getenv('PREFERENCES_TABLE', 'MovieRecommender_Preferences'),
            'activity': os.getenv('ACTIVITY_TABLE', 'MovieRecommender_Activity')
        }
        
        for key, table_name in table_names.items():
            self.tables[key] = self.dynamodb.Table(table_name)

    def get_movie(self, movie_id):
        """Get a movie by ID."""
        try:
            response = self.tables['movies'].get_item(
                Key={'movie_id': str(movie_id)}
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting movie {movie_id}: {e}")
            return None

    def get_user(self, user_id):
        """Get a user by ID."""
        try:
            response = self.tables['users'].query(
                IndexName='UserIdIndex',
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except ClientError as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    def get_user_by_email(self, email):
        """Get a user by email."""
        try:
            response = self.tables['users'].get_item(
                Key={'email': email}
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting user with email {email}: {e}")
            return None

    def get_user_favorites(self, user_id):
        """Get a user's favorite movies."""
        try:
            response = self.tables['favorites'].query(
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error getting favorites for user {user_id}: {e}")
            return []

    def get_user_watched(self, user_id):
        """Get a user's watched movies."""
        try:
            response = self.tables['watched'].query(
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error getting watched movies for user {user_id}: {e}")
            return []

    def get_user_preferences(self, user_id):
        """Get a user's preferences."""
        try:
            response = self.tables['preferences'].get_item(
                Key={'user_id': user_id}
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting preferences for user {user_id}: {e}")
            return None

    def get_movie_reviews(self, movie_id):
        """Get all reviews for a movie."""
        try:
            response = self.tables['reviews'].query(
                IndexName='MovieIndex',
                KeyConditionExpression=Key('movie_id').eq(str(movie_id))
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error getting reviews for movie {movie_id}: {e}")
            return []

    def add_movie_review(self, user_id, movie_id, rating, timestamp=None):
        """Add or update a movie review."""
        try:
            item = {
                'user_id': str(user_id),
                'movie_id': str(movie_id),
                'rating': rating
            }
            if timestamp:
                item['timestamp'] = timestamp

            self.tables['reviews'].put_item(Item=item)
            return True
        except ClientError as e:
            logger.error(f"Error adding review for movie {movie_id}: {e}")
            return False

    def toggle_favorite(self, user_id, movie_id):
        """Toggle a movie as favorite for a user."""
        try:
            # Check if movie is already favorited
            response = self.tables['favorites'].get_item(
                Key={
                    'user_id': user_id,
                    'movie_id': str(movie_id)
                }
            )
            
            if 'Item' in response:
                # Remove from favorites
                self.tables['favorites'].delete_item(
                    Key={
                        'user_id': user_id,
                        'movie_id': str(movie_id)
                    }
                )
                return False  # Indicates removed from favorites
            else:
                # Add to favorites
                self.tables['favorites'].put_item(
                    Item={
                        'user_id': user_id,
                        'movie_id': str(movie_id),
                        'timestamp': int(time.time())
                    }
                )
                return True  # Indicates added to favorites
        except ClientError as e:
            logger.error(f"Error toggling favorite for movie {movie_id}: {e}")
            return None

    def add_user_activity(self, user_id, activity_type, details=None):
        """Log user activity."""
        try:
            item = {
                'user_id': user_id,
                'timestamp': int(time.time()),
                'activity_type': activity_type
            }
            if details:
                item['details'] = details

            self.tables['activity'].put_item(Item=item)
            return True
        except ClientError as e:
            logger.error(f"Error logging activity for user {user_id}: {e}")
            return False

    def update_user_preferences(self, user_id, preferences):
        """Update a user's preferences."""
        try:
            self.tables['preferences'].put_item(Item={
                'user_id': user_id,
                'preferences': preferences,
                'updated_at': int(time.time())
            })
            return True
        except ClientError as e:
            logger.error(f"Error updating preferences for user {user_id}: {e}")
            return False
