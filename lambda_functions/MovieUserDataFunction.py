import json
import boto3
import os
import time
import jwt
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'MovieRecommender_Users'))
favorites_table = dynamodb.Table(os.environ.get('FAVORITES_TABLE', 'MovieRecommender_Favorites'))
watched_table = dynamodb.Table(os.environ.get('WATCHED_TABLE', 'MovieRecommender_Watched'))
activity_table = dynamodb.Table(os.environ.get('ACTIVITY_TABLE', 'MovieRecommender_Activity'))
reviews_table = dynamodb.Table(os.environ.get('REVIEWS_TABLE', 'Reviews'))

# JWT secret - in production, use AWS Secrets Manager
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-jwt-secret-key')

def lambda_handler(event, context):
    """
    Main entry point for the User Data Lambda function
    """
    try:
        # Extract path and HTTP method
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        
        # Route request to appropriate handler
        if path.endswith('/user-data/favorites') and http_method == 'GET':
            return handle_get_favorites(event)
        elif path.endswith('/user-data/favorites') and http_method == 'POST':
            return handle_add_favorite(event)
        elif '/user-data/favorites/' in path and http_method == 'DELETE':
            return handle_remove_favorite(event)
        elif '/user-data/favorites/toggle/' in path and http_method == 'GET':
            return handle_toggle_favorite(event)
        elif path.endswith('/user-data/watched') and http_method == 'GET':
            return handle_get_watched(event)
        elif path.endswith('/user-data/watched') and http_method == 'POST':
            return handle_add_watched(event)
        elif '/user-data/watched/toggle/' in path and http_method == 'GET':
            return handle_toggle_watched(event)
        elif '/user-data/watched/' in path and http_method == 'DELETE':
            return handle_remove_watched(event)
        elif path.endswith('/user/account') and http_method == 'DELETE':
            return handle_delete_account(event)
        elif path.endswith('/user/activity') and http_method == 'GET':
            return handle_get_activity(event)
        elif path.endswith('/user-data/reviews') and http_method == 'POST':
            return handle_add_review(event)
        elif path.endswith('/user-data/reviews') and http_method == 'GET':
            return handle_get_reviews(event)
        else:
            return build_response(404, {'error': 'Not found'})
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return build_response(500, {'error': 'Internal server error'})

def handle_get_favorites(event):
    """
    Handle get favorites request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        user_id = user.get('user_id')
        
        # Query favorites table for user's favorites
        response = favorites_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        favorite_items = response.get('Items', [])
        
        # Format response
        return build_response(200, {
            'movies': favorite_items
        })
    
    except Exception as e:
        print(f"Get favorites error: {str(e)}")
        return build_response(500, {'error': 'Error getting favorites'})

def handle_add_favorite(event):
    """
    Handle add favorite request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        movie_id = request_body.get('movieId')
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        timestamp = int(time.time())
        
        # Add to favorites table
        favorites_table.put_item(
            Item={
                'user_id': user_id,
                'movie_id': movie_id,
                'created_at': timestamp
            }
        )
        
        # Log activity
        log_user_activity(user_id, 'add_favorite', {'movie_id': movie_id})
        
        return build_response(200, {'message': 'Movie added to favorites'})
    
    except Exception as e:
        print(f"Add favorite error: {str(e)}")
        return build_response(500, {'error': 'Error adding favorite'})

def handle_remove_favorite(event):
    """
    Handle remove favorite request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Extract movie ID from path
        path = event.get('path', '')
        path_parts = path.split('/')
        movie_id = path_parts[-1]
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        
        # Remove from favorites table
        favorites_table.delete_item(
            Key={
                'user_id': user_id,
                'movie_id': movie_id
            }
        )
        
        # Log activity
        log_user_activity(user_id, 'remove_favorite', {'movie_id': movie_id})
        
        return build_response(200, {'message': 'Movie removed from favorites'})
    
    except Exception as e:
        print(f"Remove favorite error: {str(e)}")
        return build_response(500, {'error': 'Error removing favorite'})

def handle_toggle_favorite(event):
    """
    Handle toggle favorite request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        path = event.get('path', '')
        movie_id = path.split('/')[-1]
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        
        # Check if movie is already a favorite
        response = favorites_table.get_item(
            Key={
                'user_id': user_id,
                'movie_id': movie_id
            }
        )
        
        is_favorite = 'Item' in response
        
        return build_response(200, {
            'isFavorite': is_favorite
        })
    
    except Exception as e:
        print(f"Toggle favorite error: {str(e)}")
        return build_response(500, {'error': 'Error toggling favorite'})

def handle_get_watched(event):
    """
    Handle get watched movies request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        user_id = user.get('user_id')
        
        # Query watched table for user's watched movies
        response = watched_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        watched_items = response.get('Items', [])
        
        # Format response
        return build_response(200, {
            'movies': watched_items
        })
    
    except Exception as e:
        print(f"Get watched movies error: {str(e)}")
        return build_response(500, {'error': 'Error getting watched movies'})

def handle_add_watched(event):
    """
    Handle add watched movie request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        movie_id = request_body.get('movieId')
        rating = request_body.get('rating')
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        timestamp = int(time.time())
        
        # Add to watched table
        item = {
            'user_id': user_id,
            'movie_id': movie_id,
            'watched_at': timestamp
        }
        
        if rating is not None:
            item['rating'] = rating
        
        watched_table.put_item(Item=item)
        
        # Log activity
        activity_data = {'movie_id': movie_id}
        if rating is not None:
            activity_data['rating'] = rating
        
        log_user_activity(user_id, 'add_watched', activity_data)
        
        return build_response(200, {'message': 'Movie added to watched list'})
    
    except Exception as e:
        print(f"Add watched movie error: {str(e)}")
        return build_response(500, {'error': 'Error adding watched movie'})

def handle_remove_watched(event):
    """
    Handle remove watched movie request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Extract movie ID from path
        path = event.get('path', '')
        path_parts = path.split('/')
        movie_id = path_parts[-1]
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        
        # Remove from watched table
        watched_table.delete_item(
            Key={
                'user_id': user_id,
                'movie_id': movie_id
            }
        )
        
        # Log activity
        log_user_activity(user_id, 'remove_watched', {'movie_id': movie_id})
        
        return build_response(200, {'message': 'Movie removed from watched list'})
    
    except Exception as e:
        print(f"Remove watched movie error: {str(e)}")
        return build_response(500, {'error': 'Error removing watched movie'})
    
def handle_toggle_watched(event):
    """
    Check if a movie is in the user's watched list
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Extract movie_id from path
        path = event.get('path', '')
        movie_id = path.split('/')[-1]
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        
        # Check if movie is already watched
        response = watched_table.get_item(
            Key={
                'user_id': user_id,
                'movie_id': movie_id
            }
        )
        
        is_watched = 'Item' in response
        
        return build_response(200, {
            'isWatched': is_watched
        })
    
    except Exception as e:
        print(f"Toggle watched error: {str(e)}")
        return build_response(500, {'error': 'Error toggling watched'})

def handle_delete_account(event):
    """
    Handle delete account request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        user_id = user.get('user_id')
        email = user.get('email')
        
        # Delete all user data from all tables
        try:
            # Delete from users table
            users_table.delete_item(
                Key={'email': email}
            )
            
            # Delete all favorites
            favorites = favorites_table.query(
                KeyConditionExpression=Key('user_id').eq(user_id)
            ).get('Items', [])
            
            for favorite in favorites:
                favorites_table.delete_item(
                    Key={
                        'user_id': user_id,
                        'movie_id': favorite.get('movie_id')
                    }
                )
            
            # Delete all watched movies
            watched_movies = watched_table.query(
                KeyConditionExpression=Key('user_id').eq(user_id)
            ).get('Items', [])
            
            for movie in watched_movies:
                watched_table.delete_item(
                    Key={
                        'user_id': user_id,
                        'movie_id': movie.get('movie_id')
                    }
                )
            
            # Delete activity log
            activity_records = activity_table.query(
                KeyConditionExpression=Key('user_id').eq(user_id)
            ).get('Items', [])
            
            for record in activity_records:
                activity_table.delete_item(
                    Key={
                        'user_id': user_id,
                        'timestamp': record.get('timestamp')
                    }
                )
            
            return build_response(200, {'message': 'Account successfully deleted'})
            
        except Exception as e:
            print(f"Error deleting account data: {str(e)}")
            return build_response(500, {'error': 'Error deleting account data'})
    
    except Exception as e:
        print(f"Delete account error: {str(e)}")
        return build_response(500, {'error': 'Error deleting account'})

def handle_get_activity(event):
    """
    Handle get user activity request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        user_id = user.get('user_id')
        
        # Query activity table for user's activities
        response = activity_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            ScanIndexForward=False  # Sort by timestamp descending
        )
        
        activity_items = response.get('Items', [])
        
        # Format response
        return build_response(200, {
            'activities': activity_items
        })
    
    except Exception as e:
        print(f"Get activity error: {str(e)}")
        return build_response(500, {'error': 'Error getting activity history'})

# Helper functions
def get_authenticated_user(event):
    """
    Get authenticated user from JWT token
    """
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        email = payload.get('email')
        
        if not email:
            return None
        
        # Get user from DynamoDB
        response = users_table.get_item(
            Key={'email': email}
        )
        
        return response.get('Item')
    except:
        return None

def log_user_activity(user_id, action, data=None):
    """
    Log user activity to activity table
    """
    timestamp = int(time.time() * 1000)  # Milliseconds for sorting
    
    item = {
        'user_id': user_id,
        'timestamp': timestamp,
        'action': action
    }
    
    if data:
        item['data'] = data
    
    try:
        activity_table.put_item(Item=item)
    except Exception as e:
        print(f"Error logging activity: {str(e)}")

def build_response(status_code, body):
    """
    Build API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        },
        'body': json.dumps(body)
    } 
    
def handle_add_review(event):
    """
    Handle add review request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Parse request body
        request_body = json.loads(event.get('body', '{}'))
        movie_id = request_body.get('movieId')
        rating = request_body.get('rating')
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        timestamp = int(time.time())

        # Add to reviews table
        reviews_table.put_item(
            Item={
                'user_id': user_id,
                'movie_id': movie_id,
                'rating': rating,
                'timestamp': timestamp
            }
        )
        
        # Log activity
        log_user_activity(user_id, 'add_review', {'movie_id': movie_id, 'rating': rating})

        return build_response(200, {'message': 'Review added successfully'})

    except Exception as e:
        print(f"Add review error: {str(e)}")
        return build_response(500, {'error': 'Error adding review'})

def handle_get_reviews(event):
    """
    Handle get reviews request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        user_id = user.get('user_id')

        # Query reviews table for user's reviews
        response = reviews_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        review_items = response.get('Items', [])

        # Format response
        return build_response(200, {
            'reviews': review_items
        })

    except Exception as e:
        print(f"Get reviews error: {str(e)}")
        return build_response(500, {'error': 'Error getting reviews'})