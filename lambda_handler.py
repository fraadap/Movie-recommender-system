import lambda_functions.MovieAuthFunction as maf
import lambda_functions.MovieUserDataFunction as mudf
import lambda_functions.RecommendationFunctions as rf
from utils.config import Config
from utils.utils_function import build_response


def lambda_handler(event, context):
    """
    Main entry point for the User Data Lambda function
    """
    try:
        # Extract path and HTTP method

        path = event.get("requestContext", {}).get("http", {}).get("path", "")
        http_method = event.get("requestContext", {}).get("http", {}).get("method", "")
        if not http_method:
            path = event.get('path', '')
            http_method = event.get('httpMethod', '')


        # Route request to appropriate handler
        if path.endswith('/user-data/favorites') and http_method == 'GET':
            return mudf.handle_get_favorites(event)
        elif path.endswith('/user-data/favorites') and http_method == 'POST':
            return mudf.handle_add_favorite(event)
        elif '/user-data/favorites/' in path and http_method == 'DELETE':
            return mudf.handle_remove_favorite(event)
        elif '/user-data/favorites/toggle/' in path and http_method == 'GET':
            return mudf.handle_toggle_favorite(event)
        elif path.endswith('/user/account') and http_method == 'DELETE':
            return mudf.handle_delete_account(event)
        elif path.endswith('/user/activity') and http_method == 'GET':
            return mudf.handle_get_activity(event)
        elif path.endswith('/user-data/reviews') and http_method == 'POST':
            return mudf.handle_add_review(event)
        elif path.endswith('/user-data/reviews') and http_method == 'GET':
            return mudf.handle_get_reviews(event)
        elif '/user-data/reviews/toggle/' in path and http_method == 'GET':
            return mudf.handle_toggle_reviewed(event)
        elif '/user-data/reviews/' in path and http_method == 'DELETE':
            return mudf.handle_remove_review(event)
        elif path.endswith('/auth/login') and http_method == 'POST':
            return maf.handle_login(event)
        elif path.endswith('/auth/register') and http_method == 'POST':
            return maf.handle_register(event)
        elif path.endswith('/auth/refresh') and http_method == 'POST':
            return maf.handle_refresh(event)
        elif path.endswith('/search') and http_method == 'POST':
            return rf.handle_semantic_search(event)
        elif path.endswith('/content') and http_method == 'POST':
            return rf.handle_content_based_search(event)
        elif path.endswith('/collaborative') and http_method == 'POST':
            return rf.handle_collaborative_search(event)        
        elif path.endswith('/similar') and http_method == 'POST':
            return rf.handle_similar_search(event)
        elif path.endswith('/'):
            return build_response(200, {'message': 'Hi, welcome to this API'})
        else:
            return build_response(404, {'error': 'Path not found '+ path})
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return build_response(500, {'error': 'Internal server error ' + str(e)})

        