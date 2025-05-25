import boto3
import json
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApiGatewaySetup:
    def __init__(self, region='eu-west-1', lambda_name='MovieSearchFunction', auth_lambda_name='MovieAuthFunction', user_lambda_name='MovieUserDataFunction'):
        self.region = region
        self.lambda_name = lambda_name
        self.auth_lambda_name = auth_lambda_name
        self.user_lambda_name = user_lambda_name
        self.apigw = boto3.client('apigateway', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.account_id = boto3.client('sts').get_caller_identity().get('Account')
    
    def create_api(self, api_name='MovieRecommenderAPI'):
        """Create a new API Gateway REST API"""
        logger.info(f"Creating API Gateway: {api_name}")
        response = self.apigw.create_rest_api(
            name=api_name,
            description='API for Movie Recommender System',
            endpointConfiguration={'types': ['REGIONAL']},
            corsConfiguration={
                'allowOrigins': ['*'],  # For development; restrict in production
                'allowMethods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                'allowHeaders': ['Content-Type', 'Authorization'],
                'maxAge': 3600
            }
        )
        api_id = response['id']
        logger.info(f"API created with ID: {api_id}")
        return api_id
    
    def get_root_resource(self, api_id):
        """Get the root resource ID of the API"""
        resources = self.apigw.get_resources(restApiId=api_id)
        for resource in resources['items']:
            if resource['path'] == '/':
                return resource['id']
        return None
    
    def create_resource(self, api_id, parent_id, path_part):
        """Create a resource under the parent"""
        logger.info(f"Creating resource: {path_part}")
        response = self.apigw.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        return response['id']
    
    def setup_cors(self, api_id, resource_id):
        """Set up CORS for the resource"""
        logger.info("Setting up CORS")
        self.apigw.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        self.apigw.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            integrationHttpMethod='OPTIONS',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        self.apigw.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': True,
                'method.response.header.Access-Control-Allow-Methods': True,
                'method.response.header.Access-Control-Allow-Headers': True
            }
        )
        
        self.apigw.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': "'*'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,Authorization'"
            }
        )
    
    def create_method(self, api_id, resource_id, http_method='POST', lambda_function=None):
        """Create a method for the resource"""
        logger.info(f"Creating {http_method} method")
        self.apigw.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            authorizationType='NONE',  # Change to 'COGNITO_USER_POOLS' for production
            apiKeyRequired=False
        )
        
        # Set up Lambda integration
        if lambda_function is None:
            lambda_function = self.lambda_name
            
        lambda_arn = f"arn:aws:lambda:{self.region}:{self.account_id}:function:{lambda_function}"
        self.apigw.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        )
        
        # Add method response
        self.apigw.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': True
            },
            responseModels={
                'application/json': 'Empty'
            }
        )
    
    def add_lambda_permission(self, api_id, lambda_function=None):
        """Add permission for API Gateway to invoke the Lambda function"""
        if lambda_function is None:
            lambda_function = self.lambda_name
            
        logger.info(f"Adding Lambda permission for {lambda_function}")
        source_arn = f"arn:aws:execute-api:{self.region}:{self.account_id}:{api_id}/*/*"
        try:
            self.lambda_client.add_permission(
                FunctionName=lambda_function,
                StatementId=f'apigateway-invoke-{api_id}-{lambda_function}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )
        except self.lambda_client.exceptions.ResourceConflictException:
            logger.info("Permission already exists")
    
    def deploy_api(self, api_id, stage_name='prod'):
        """Deploy the API to a stage"""
        logger.info(f"Deploying API to stage: {stage_name}")
        response = self.apigw.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            description=f'Deployment to {stage_name}'
        )
        
        # Set up stage variables if needed
        self.apigw.update_stage(
            restApiId=api_id,
            stageName=stage_name,
            patchOperations=[
                {
                    'op': 'replace',
                    'path': '/*/*/throttling/rateLimit',
                    'value': '100'  # Limit to 100 requests per second
                },
                {
                    'op': 'replace',
                    'path': '/*/*/throttling/burstLimit',
                    'value': '200'  # Allow bursts up to 200 requests
                }
            ]
        )
        
        api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/{stage_name}"
        logger.info(f"API deployed successfully. Endpoint: {api_url}")
        return api_url
    
    def create_endpoints(self):
        """Set up complete API with all required endpoints"""
        # Create API
        api_id = self.create_api()
        root_id = self.get_root_resource(api_id)
        
        # Create original endpoints
        recommend_id = self.create_resource(api_id, root_id, 'recommend')
        self.setup_cors(api_id, recommend_id)
        self.create_method(api_id, recommend_id)
        
        search_id = self.create_resource(api_id, root_id, 'search')
        self.setup_cors(api_id, search_id)
        self.create_method(api_id, search_id)
        
        content_id = self.create_resource(api_id, root_id, 'content')
        self.setup_cors(api_id, content_id)
        self.create_method(api_id, content_id)
        
        collab_id = self.create_resource(api_id, root_id, 'collaborative')
        self.setup_cors(api_id, collab_id)
        self.create_method(api_id, collab_id)
        
        # Create new auth endpoints
        auth_id = self.create_resource(api_id, root_id, 'auth')
        self.setup_cors(api_id, auth_id)
        
        login_id = self.create_resource(api_id, auth_id, 'login')
        self.setup_cors(api_id, login_id)
        self.create_method(api_id, login_id, lambda_function=self.auth_lambda_name)
        
        register_id = self.create_resource(api_id, auth_id, 'register')
        self.setup_cors(api_id, register_id)
        self.create_method(api_id, register_id, lambda_function=self.auth_lambda_name)
        
        refresh_id = self.create_resource(api_id, auth_id, 'refresh')
        self.setup_cors(api_id, refresh_id)
        self.create_method(api_id, refresh_id, lambda_function=self.auth_lambda_name)
        
        password_id = self.create_resource(api_id, auth_id, 'password')
        self.setup_cors(api_id, password_id)
        self.create_method(api_id, password_id, http_method='PUT', lambda_function=self.auth_lambda_name)
        
        profile_id = self.create_resource(api_id, auth_id, 'profile')
        self.setup_cors(api_id, profile_id)
        self.create_method(api_id, profile_id, http_method='PUT', lambda_function=self.auth_lambda_name)
        
        # Create user-data endpoints
        user_data_id = self.create_resource(api_id, root_id, 'user-data')
        self.setup_cors(api_id, user_data_id)
        
        # Watched movies endpoints
        watched_id = self.create_resource(api_id, user_data_id, 'watched')
        self.setup_cors(api_id, watched_id)
        self.create_method(api_id, watched_id, http_method='GET', lambda_function=self.user_lambda_name)
        self.create_method(api_id, watched_id, http_method='POST', lambda_function=self.user_lambda_name)
        
        # Favorites endpoints
        favorites_id = self.create_resource(api_id, user_data_id, 'favorites')
        self.setup_cors(api_id, favorites_id)
        self.create_method(api_id, favorites_id, http_method='GET', lambda_function=self.user_lambda_name)
        self.create_method(api_id, favorites_id, http_method='POST', lambda_function=self.user_lambda_name)
        
        favorites_toggle_id = self.create_resource(api_id, favorites_id, 'toggle')
        self.setup_cors(api_id, favorites_toggle_id)
        self.create_method(api_id, favorites_toggle_id, lambda_function=self.user_lambda_name)
        
        # Create user preferences endpoints
        user_id = self.create_resource(api_id, root_id, 'user')
        self.setup_cors(api_id, user_id)
        
        preferences_id = self.create_resource(api_id, user_id, 'preferences')
        self.setup_cors(api_id, preferences_id)
        self.create_method(api_id, preferences_id, http_method='GET', lambda_function=self.user_lambda_name)
        self.create_method(api_id, preferences_id, http_method='PUT', lambda_function=self.user_lambda_name)
        
        account_id = self.create_resource(api_id, user_id, 'account')
        self.setup_cors(api_id, account_id)
        self.create_method(api_id, account_id, http_method='DELETE', lambda_function=self.user_lambda_name)
        
        activity_id = self.create_resource(api_id, user_id, 'activity')
        self.setup_cors(api_id, activity_id)
        self.create_method(api_id, activity_id, http_method='GET', lambda_function=self.user_lambda_name)
        
        # Add Lambda permissions
        self.add_lambda_permission(api_id)
        self.add_lambda_permission(api_id, lambda_function=self.auth_lambda_name)
        self.add_lambda_permission(api_id, lambda_function=self.user_lambda_name)
        
        # Deploy API
        api_url = self.deploy_api(api_id)
        
        # Save API info
        api_info = {
            'api_id': api_id,
            'endpoints': {
                # Original endpoints
                'recommend': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/recommend",
                'search': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/search",
                'content': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/content",
                'collaborative': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/collaborative",
                
                # Auth endpoints
                'auth': {
                    'login': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/auth/login",
                    'register': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/auth/register",
                    'refresh': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/auth/refresh",
                    'password': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/auth/password",
                    'profile': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/auth/profile"
                },
                
                # User data endpoints
                'user-data': {
                    'watched': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/user-data/watched",
                    'favorites': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/user-data/favorites",
                    'favorites-toggle': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/user-data/favorites/toggle"
                },
                
                # User preferences endpoints
                'user': {
                    'preferences': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/user/preferences",
                    'account': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/user/account",
                    'activity': f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/user/activity"
                }
            }
        }
        
        with open('api_info.json', 'w') as f:
            json.dump(api_info, f, indent=2)
        
        logger.info(f"API setup complete. Information saved to api_info.json")
        return api_info

def main():
    parser = argparse.ArgumentParser(description='Set up API Gateway for Movie Recommender')
    parser.add_argument('--region', default='eu-west-1', help='AWS region')
    parser.add_argument('--lambda-name', default='MovieSearchFunction', help='Main Lambda function name')
    parser.add_argument('--auth-lambda-name', default='MovieAuthFunction', help='Auth Lambda function name')
    parser.add_argument('--user-lambda-name', default='MovieUserDataFunction', help='User data Lambda function name')
    
    args = parser.parse_args()
    
    api_setup = ApiGatewaySetup(
        region=args.region, 
        lambda_name=args.lambda_name, 
        auth_lambda_name=args.auth_lambda_name,
        user_lambda_name=args.user_lambda_name
    )
    api_setup.create_endpoints()

if __name__ == '__main__':
    main() 