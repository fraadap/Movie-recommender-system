#!/usr/bin/env python3
"""
Lambda Function Endpoint Testing Script
Tests all endpoints for Movie Recommender System Lambda functions
"""

import boto3
import json
import time
from typing import Dict, Any, List

class LambdaEndpointTester:
    def __init__(self, region_name='us-east-1'):
        """Initialize the Lambda client and test configuration"""
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.jwt_token = None
        self.test_user_email = "test_user@example.com"
        self.test_user_password = "TestPassword123"
        
        # Configure your Lambda function names here
        self.function_names = {
            'auth': 'MovieAuthFunction',  # Update with your actual function name
            'userdata': 'MovieUserDataFunction',  # Update with your actual function name
            'search': 'SearchLambdaRouter',  # Update with your actual function name
            'handler': 'MainHandler'  # Update if using centralized handler
        }
    
    def invoke_lambda(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a Lambda function with the given payload"""
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            return result
        except Exception as e:
            print(f"❌ Error invoking {function_name}: {str(e)}")
            return {"error": str(e)}
    
    def test_auth_endpoints(self) -> bool:
        """Test authentication endpoints"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Test 1: User Registration
        print("1. Testing user registration...")
        register_payload = {
            "httpMethod": "POST",
            "path": "/auth/register",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "name": "Test User",
                "email": self.test_user_email,
                "password": self.test_user_password
            })
        }
        
        result = self.invoke_lambda(self.function_names['auth'], register_payload)
        if 'statusCode' in result and result['statusCode'] in [200, 201, 409]:
            print("✅ Registration test passed")
        else:
            print(f"❌ Registration test failed: {result}")
            return False
        
        # Test 2: User Login
        print("2. Testing user login...")
        login_payload = {
            "httpMethod": "POST",
            "path": "/auth/login",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "email": self.test_user_email,
                "password": self.test_user_password
            })
        }
        
        result = self.invoke_lambda(self.function_names['auth'], login_payload)
        if 'statusCode' in result and result['statusCode'] == 200:
            # Extract JWT token for subsequent tests
            body = json.loads(result['body'])
            self.jwt_token = body.get('token')
            print("✅ Login test passed, JWT token extracted")
        else:
            print(f"❌ Login test failed: {result}")
            return False
        
        # Test 3: Token Refresh
        if self.jwt_token:
            print("3. Testing token refresh...")
            refresh_payload = {
                "httpMethod": "POST",
                "path": "/auth/refresh",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.jwt_token}"
                },
                "body": "{}"
            }
            
            result = self.invoke_lambda(self.function_names['auth'], refresh_payload)
            if 'statusCode' in result and result['statusCode'] == 200:
                print("✅ Token refresh test passed")
            else:
                print(f"❌ Token refresh test failed: {result}")
        
        return True
    
    def test_userdata_endpoints(self) -> bool:
        """Test user data management endpoints"""
        if not self.jwt_token:
            print("❌ No JWT token available for user data tests")
            return False
        
        print("\n👤 Testing User Data Endpoints...")
        
        # Test 1: Get Favorites
        print("1. Testing get favorites...")
        favorites_payload = {
            "httpMethod": "GET",
            "path": "/user-data/favorites",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            }
        }
        
        result = self.invoke_lambda(self.function_names['userdata'], favorites_payload)
        if 'statusCode' in result and result['statusCode'] == 200:
            print("✅ Get favorites test passed")
        else:
            print(f"❌ Get favorites test failed: {result}")
        
        # Test 2: Add to Favorites
        print("2. Testing add to favorites...")
        add_favorite_payload = {
            "httpMethod": "POST",
            "path": "/user-data/favorites",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            },
            "body": json.dumps({"movieId": "12345"})
        }
        
        result = self.invoke_lambda(self.function_names['userdata'], add_favorite_payload)
        if 'statusCode' in result and result['statusCode'] == 200:
            print("✅ Add to favorites test passed")
        else:
            print(f"❌ Add to favorites test failed: {result}")
        
        # Test 3: Get User Activity
        print("3. Testing get user activity...")
        activity_payload = {
            "httpMethod": "GET",
            "path": "/user/activity",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            }
        }
        
        result = self.invoke_lambda(self.function_names['userdata'], activity_payload)
        if 'statusCode' in result and result['statusCode'] == 200:
            print("✅ Get user activity test passed")
        else:
            print(f"❌ Get user activity test failed: {result}")
        
        return True
    
    def test_search_endpoints(self) -> bool:
        """Test search and recommendation endpoints"""
        print("\n🔍 Testing Search Endpoints...")
        
        # Test 1: Semantic Search
        print("1. Testing semantic search...")
        search_payload = {
            "httpMethod": "POST",
            "path": "/search",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "query": "action movies with superheroes",
                "top_k": 5
            })
        }
        
        result = self.invoke_lambda(self.function_names['search'], search_payload)
        if 'statusCode' in result and result['statusCode'] == 200:
            print("✅ Semantic search test passed")
        else:
            print(f"❌ Semantic search test failed: {result}")
        
        # Test 2: Content-Based Recommendations
        print("2. Testing content-based recommendations...")
        content_payload = {
            "httpMethod": "POST",
            "path": "/content",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "movie_ids": [["12345", 5.0], ["67890", 4.0]],
                "top_k": 5
            })
        }
        
        result = self.invoke_lambda(self.function_names['search'], content_payload)
        if 'statusCode' in result and result['statusCode'] == 200:
            print("✅ Content-based recommendations test passed")
        else:
            print(f"❌ Content-based recommendations test failed: {result}")
        
        # Test 3: Similar Movies
        print("3. Testing similar movies...")
        similar_payload = {
            "httpMethod": "POST",
            "path": "/similar",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "movie_id": "12345",
                "top_k": 5
            })
        }
        
        result = self.invoke_lambda(self.function_names['search'], similar_payload)
        if 'statusCode' in result and result['statusCode'] == 200:
            print("✅ Similar movies test passed")
        else:
            print(f"❌ Similar movies test failed: {result}")
        
        # Test 4: Collaborative Filtering (requires authentication)
        if self.jwt_token:
            print("4. Testing collaborative filtering...")
            collab_payload = {
                "httpMethod": "POST",
                "path": "/collaborative",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.jwt_token}"
                },
                "body": json.dumps({"top_k": 5})
            }
            
            result = self.invoke_lambda(self.function_names['search'], collab_payload)
            if 'statusCode' in result and result['statusCode'] == 200:
                print("✅ Collaborative filtering test passed")
            else:
                print(f"❌ Collaborative filtering test failed: {result}")
        
        return True
    
    def run_all_tests(self):
        """Run all endpoint tests"""
        print("🚀 Starting Lambda Function Endpoint Tests...")
        print("=" * 50)
        
        # Test authentication first (needed for other tests)
        auth_success = self.test_auth_endpoints()
        
        # Test user data endpoints
        userdata_success = self.test_userdata_endpoints()
        
        # Test search endpoints
        search_success = self.test_search_endpoints()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        print(f"Authentication Tests: {'✅ PASSED' if auth_success else '❌ FAILED'}")
        print(f"User Data Tests: {'✅ PASSED' if userdata_success else '❌ FAILED'}")
        print(f"Search Tests: {'✅ PASSED' if search_success else '❌ FAILED'}")
        
        overall_success = auth_success and userdata_success and search_success
        print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '⚠️  SOME TESTS FAILED'}")
        
        return overall_success

def main():
    """Main function to run the tests"""
    # Update these with your actual Lambda function names
    tester = LambdaEndpointTester(region_name='us-east-1')  # Update with your region
    
    print("Lambda Function Endpoint Tester")
    print("Make sure your Lambda functions are deployed and configured correctly.")
    print("\nCurrent function configuration:")
    for key, name in tester.function_names.items():
        print(f"  {key}: {name}")
    
    input("\nPress Enter to start testing...")
    
    # Run all tests
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("💡 Tips:")
        print("   - Verify Lambda function names in the script")
        print("   - Check CloudWatch logs for detailed error information")
        print("   - Ensure DynamoDB tables and S3 buckets are properly configured")
        print("   - Verify environment variables are set correctly")

if __name__ == "__main__":
    main()
