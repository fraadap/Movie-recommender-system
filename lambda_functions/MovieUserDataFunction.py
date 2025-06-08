import json
import time
from decimal import Decimal
from boto3.dynamodb.conditions import Key

from utils.config import Config
from utils.utils_function import get_authenticated_user, build_response, sanitize_input, log_user_activity, get_item_converted
import utils.database as db

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
        response = db.favorites_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        
        favorite_items = response.get('Items', [])
        results = []
        for item in favorite_items:
            mid = item.get('movie_id')
            resp = db.movies_table.get_item(Key={'movie_id': str(mid)})
            movie = resp.get('Item')
            if movie:
                results.append(movie)

        results = get_item_converted(results)
        # Format response
        return build_response(200, {
            'movies': results
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
        movie_id = sanitize_input(request_body.get('movieId'))
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        timestamp = int(time.time())
        
        # Add to favorites table
        db.favorites_table.put_item(
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
        return build_response(500, {'error': 'Error adding favorite '+ str(e)})

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
        path = event.get('rawPath', '')
        path_parts = path.split('/')
        movie_id = path_parts[-1]
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        
        # Remove from favorites table
        db.favorites_table.delete_item(
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
        
        path = event.get('rawPath', '')
        movie_id = path.split('/')[-1]
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        
        # Check if movie is already a favorite
        response = db.favorites_table.get_item(
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

def handle_remove_review(event):
    """
    Handle remove review request
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Extract movie ID from path
        path = event.get('rawPath', '')
        path_parts = path.split('/')
        movie_id = path_parts[-1]
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        
        # Remove from reviews table
        db.reviews_table.delete_item(
            Key={
                'user_id': user_id,
                'movie_id': movie_id
            }
        )
        
        # Log activity
        log_user_activity(user_id, 'remove_review', {'movie_id': movie_id})

        return build_response(200, {'message': 'Movie removed from reviews'})
    
    except Exception as e:
        print(f"Remove reviewed movie error: {str(e)}")
        return build_response(500, {'error': 'Error removing reviewed movie'})
    
def handle_toggle_reviewed(event):
    """
    Check if a movie is in the user's reviewed list
    """
    try:
        # Verify JWT token
        user = get_authenticated_user(event)
        if not user:
            return build_response(401, {'error': 'Authentication required'})
        
        # Extract movie_id from path
        path = event.get('rawPath', '')
        movie_id = path.split('/')[-1]
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        
        # Check if movie is already reviewed
        response = db.reviews_table.get_item(
            Key={
                'user_id': user_id,
                'movie_id': movie_id
            }
        )
        
        is_reviewed = 'Item' in response
        
        return build_response(200, {
            'isReviewed': is_reviewed
        })
    
    except Exception as e:
        print(f"Toggle reviewed error: {str(e)}")
        return build_response(500, {'error': 'Error toggling reviewed'})

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
            db.users_table.delete_item(
                Key={'email': email}
            )
            
            # Delete all favorites
            favorites = db.favorites_table.query(
                KeyConditionExpression=Key('user_id').eq(user_id)
            ).get('Items', [])
            
            for favorite in favorites:
                db.favorites_table.delete_item(
                    Key={
                        'user_id': user_id,
                        'movie_id': favorite.get('movie_id')
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
        response = db.activity_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            ScanIndexForward=False  # Sort by timestamp descending
        )
        
        activity_items = response.get('Items', [])
        activity_items = get_item_converted(activity_items)
        # Format response
        return build_response(200, {
            'activities': activity_items
        })
    
    except Exception as e:
        print(f"Get activity error: {str(e)}")
        return build_response(500, {'error': 'Error getting activity history'})

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
        db.activity_table.put_item(Item=item)
    except Exception as e:
        print(f"Error logging activity: {str(e)}")
    
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
        rating = Decimal(str(request_body.get('rating', 0)))

        if not movie_id:
            return build_response(400, {'error': 'Movie ID is required'})
        
        user_id = user.get('user_id')
        timestamp = int(time.time())

        # Add to reviews table
        db.reviews_table.put_item(
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
        response = db.reviews_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )

        review_items = response.get('Items', [])

        results = []
        for item in review_items:
            mid = item.get('movie_id')
            score = item.get('rating')
            resp = db.movies_table.get_item(Key={'movie_id': str(mid)})
            movie = resp.get('Item')
            if movie:
                movie['rating'] = score
                results.append(movie)
                
        results = get_item_converted(results)
        # Format response
        return build_response(200, {
            'movies': results
        })

    except Exception as e:
        print(f"Get reviews error: {str(e)}")
        return build_response(500, {'error': 'Error getting reviews'})