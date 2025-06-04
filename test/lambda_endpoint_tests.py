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
        self.function_name = 'Movie_recommender_system'  # Nome della tua funzione Lambda
    
    def invoke_lambda(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the Lambda function with the given payload"""
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            return result
        except Exception as e:
            print(f"❌ Error invoking {self.function_name}: {str(e)}")
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
        result = self.invoke_lambda(register_payload)
        registration_success = 'statusCode' in result and result['statusCode'] in [200, 201, 409]
        if registration_success:
            print("✅ Registration test passed")
        else:
            print(f"❌ Registration test failed: {result}")
        
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
        result = self.invoke_lambda(login_payload)
        login_success = False
        if 'statusCode' in result and result['statusCode'] == 200:
            body = json.loads(result['body'])
            self.jwt_token = body.get('token')
            login_success = True
            print("✅ Login test passed, JWT token extracted")
        else:
            print(f"❌ Login test failed: {result}")
        
        # Test 3: Token Refresh
        print("3. Testing token refresh...")
        refresh_payload = {
            "httpMethod": "POST",
            "path": "/auth/refresh",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            }
        }
        result = self.invoke_lambda(refresh_payload)
        refresh_success = False
        if 'statusCode' in result and result['statusCode'] == 200:
            body = json.loads(result['body'])
            self.jwt_token = body.get('token')  # Update token with refreshed one
            refresh_success = True
            print("✅ Token refresh test passed")
        else:
            print(f"❌ Token refresh test failed: {result}")
        
        return registration_success and login_success and refresh_success
    
    def test_userdata_endpoints(self) -> bool:
        """Test user data management endpoints"""
        
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
        
        result = self.invoke_lambda(favorites_payload)
        get_favorites_success = 'statusCode' in result and result['statusCode'] == 200
        if get_favorites_success:
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
        
        result = self.invoke_lambda(add_favorite_payload)
        add_favorite_success = 'statusCode' in result and result['statusCode'] == 200
        if add_favorite_success:
            print("✅ Add to favorites test passed")
        else:
            print(f"❌ Add to favorites test failed: {result}")
        
        # Test 3: Check Favorite Status
        print("3. Testing check favorite status...")
        check_favorite_payload = {
            "httpMethod": "GET",
            "path": "/user-data/favorites/toggle/12345",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            }
        }
        
        result = self.invoke_lambda(check_favorite_payload)
        check_favorite_success = 'statusCode' in result and result['statusCode'] == 200
        if check_favorite_success:
            print("✅ Check favorite status test passed")
        else:
            print(f"❌ Check favorite status test failed: {result}")

        # Test 4: Remove from Favorites
        print("4. Testing remove from favorites...")
        remove_favorite_payload = {
            "httpMethod": "DELETE",
            "path": "/user-data/favorites/12345",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            }
        }
        
        result = self.invoke_lambda(remove_favorite_payload)
        remove_favorite_success = 'statusCode' in result and result['statusCode'] == 200
        if remove_favorite_success:
            print("✅ Remove from favorites test passed")
        else:
            print(f"❌ Remove from favorites test failed: {result}")

        # Test 5: Add Review
        print("5. Testing add review...")
        add_review_payload = {
            "httpMethod": "POST",
            "path": "/user-data/reviews",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            },
            "body": json.dumps({
                "movieId": "12345",
                "rating": 4.5,
                "comment": "Great movie!"
            })
        }
        
        result = self.invoke_lambda(add_review_payload)
        add_review_success = 'statusCode' in result and result['statusCode'] == 200
        if add_review_success:
            print("✅ Add review test passed")
        else:
            print(f"❌ Add review test failed: {result}")

        # Test 6: Get Reviews
        print("6. Testing get reviews...")
        get_reviews_payload = {
            "httpMethod": "GET",
            "path": "/user-data/reviews",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            }
        }
        
        result = self.invoke_lambda(get_reviews_payload)
        get_reviews_success = 'statusCode' in result and result['statusCode'] == 200
        if get_reviews_success:
            print("✅ Get reviews test passed")
        else:
            print(f"❌ Get reviews test failed: {result}")

        # Test 7: Get User Activity
        print("7. Testing get user activity...")
        activity_payload = {
            "httpMethod": "GET",
            "path": "/user/activity",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt_token}"
            }
        }
        
        result = self.invoke_lambda(activity_payload)
        activity_success = 'statusCode' in result and result['statusCode'] == 200
        if activity_success:
            print("✅ Get user activity test passed")
        else:
            print(f"❌ Get user activity test failed: {result}")
        
        return (get_favorites_success and add_favorite_success and 
                check_favorite_success and remove_favorite_success and
                add_review_success and get_reviews_success and activity_success)
    
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
        
        result = self.invoke_lambda(search_payload)
        semantic_search_success = 'statusCode' in result and result['statusCode'] == 200
        if semantic_search_success:
            print("✅ Semantic search test passed")
        else:
            print(f"❌ Semantic search test failed: {result}")
        
        # Test 2: Collaborative Filtering (requires authentication)
        collab_success = True  # Default to True if we can't test it
        if self.jwt_token:
            print("2. Testing collaborative filtering...")
            collab_payload = {
                "httpMethod": "POST",
                "path": "/collaborative",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.jwt_token}"
                },
                "body": json.dumps({"top_k": 5})
            }
            
            result = self.invoke_lambda(collab_payload)
            collab_success = 'statusCode' in result and result['statusCode'] == 200
            if collab_success:
                print("✅ Collaborative filtering test passed")
            else:
                print(f"❌ Collaborative filtering test failed: {result}")
        
        # Test 3: Similar Movies
        print("3. Testing similar movies...")
        similar_payload = {
            "httpMethod": "GET",
            "path": "/movies/12345/similar",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"top_k": 5})
        }
        
        result = self.invoke_lambda(similar_payload)
        similar_movies_success = 'statusCode' in result and result['statusCode'] == 200
        if similar_movies_success:
            print("✅ Similar movies test passed")
        else:
            print(f"❌ Similar movies test failed: {result}")

        # Test 4: Content-based Recommendations
        print("4. Testing content-based recommendations...")
        content_based_payload = {
            "httpMethod": "POST",
            "path": "/recommendations/content-based",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "movie_ids": ["12345", "67890"],
                "top_k": 5
            })
        }
        
        result = self.invoke_lambda(content_based_payload)
        content_based_success = 'statusCode' in result and result['statusCode'] == 200
        if content_based_success:
            print("✅ Content-based recommendations test passed")
        else:
            print(f"❌ Content-based recommendations test failed: {result}")
        
        return semantic_search_success and collab_success and similar_movies_success and content_based_success
    
    def test_error_cases(self) -> bool:
        """Test various error cases and edge conditions"""
        print("\n⚠️ Testing Error Cases...")
        
        # Test 1: Invalid JWT
        print("1. Testing invalid JWT...")
        invalid_jwt_payload = {
            "httpMethod": "GET",
            "path": "/user-data/favorites",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid.token.here"
            }
        }
        
        result = self.invoke_lambda(invalid_jwt_payload)
        invalid_jwt_success = 'statusCode' in result and result['statusCode'] == 401
        if invalid_jwt_success:
            print("✅ Invalid JWT test passed")
        else:
            print(f"❌ Invalid JWT test failed: {result}")

        # Test 2: Missing Request Body
        print("2. Testing missing request body...")
        missing_body_payload = {
            "httpMethod": "POST",
            "path": "/search",
            "headers": {"Content-Type": "application/json"}
        }
        
        result = self.invoke_lambda(missing_body_payload)
        missing_body_success = 'statusCode' in result and result['statusCode'] == 400
        if missing_body_success:
            print("✅ Missing request body test passed")
        else:
            print(f"❌ Missing request body test failed: {result}")

        # Test 3: Invalid Endpoint
        print("3. Testing invalid endpoint...")
        invalid_endpoint_payload = {
            "httpMethod": "GET",
            "path": "/nonexistent/endpoint",
            "headers": {"Content-Type": "application/json"}
        }
        
        result = self.invoke_lambda(invalid_endpoint_payload)
        invalid_endpoint_success = 'statusCode' in result and result['statusCode'] == 404
        if invalid_endpoint_success:
            print("✅ Invalid endpoint test passed")
        else:
            print(f"❌ Invalid endpoint test failed: {result}")

        # Test 4: Malformed JSON
        print("4. Testing malformed JSON...")
        malformed_json_payload = {
            "httpMethod": "POST",
            "path": "/search",
            "headers": {"Content-Type": "application/json"},
            "body": "{invalid json}"
        }
        
        result = self.invoke_lambda(malformed_json_payload)
        malformed_json_success = 'statusCode' in result and result['statusCode'] == 400
        if malformed_json_success:
            print("✅ Malformed JSON test passed")
        else:
            print(f"❌ Malformed JSON test failed: {result}")

        return (invalid_jwt_success and missing_body_success and 
                invalid_endpoint_success and malformed_json_success)
    
    def test_edge_cases(self) -> bool:
        """Test edge cases with large queries and high top-k values"""
        print("\n🔍 Testing Edge Cases...")
        
        # Test 1: Large Search Query
        print("1. Testing large search query...")
        large_query = "This is a very long search query that includes detailed movie preferences " + \
                     "such as: action movies with complex plot, great character development, " + \
                     "amazing special effects, directed by renowned directors, featuring award-winning " + \
                     "actors, with high production values and compelling storylines that keep " + \
                     "viewers engaged throughout the entire duration of the film"
        
        large_query_payload = {
            "httpMethod": "POST",
            "path": "/search",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "query": large_query,
                "top_k": 5
            })
        }
        
        result = self.invoke_lambda(large_query_payload)
        large_query_success = 'statusCode' in result and result['statusCode'] == 200
        if large_query_success:
            print("✅ Large search query test passed")
        else:
            print(f"❌ Large search query test failed: {result}")

        # Test 2: High Top-K Recommendations
        print("2. Testing high top-k recommendations...")
        high_top_k_payload = {
            "httpMethod": "POST",
            "path": "/recommendations/content-based",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "movie_ids": ["12345"],
                "top_k": 100  # Requesting a large number of recommendations
            })
        }
        
        result = self.invoke_lambda(high_top_k_payload)
        high_top_k_success = 'statusCode' in result and result['statusCode'] == 200
        if high_top_k_success:
            print("✅ High top-k recommendations test passed")
        else:
            print(f"❌ High top-k recommendations test failed: {result}")

        return large_query_success and high_top_k_success

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
        
        # Test error cases
        error_success = self.test_error_cases()

        # Test edge cases
        edge_success = self.test_edge_cases()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        print(f"Authentication Tests: {'✅ PASSED' if auth_success else '❌ FAILED'}")
        print(f"User Data Tests: {'✅ PASSED' if userdata_success else '❌ FAILED'}")
        print(f"Search Tests: {'✅ PASSED' if search_success else '❌ FAILED'}")
        print(f"Error Case Tests: {'✅ PASSED' if error_success else '❌ FAILED'}")
        print(f"Edge Case Tests: {'✅ PASSED' if edge_success else '❌ FAILED'}")
        
        overall_success = auth_success and userdata_success and search_success and error_success and edge_success
        print(f"\nOverall Result: {'🎉 ALL TESTS PASSED' if overall_success else '⚠️  SOME TESTS FAILED'}")
        
        return overall_success

def main():
    """Main function to run the tests"""
    tester = LambdaEndpointTester(region_name='us-east-1')
    
    print("Lambda Function Endpoint Tester")
    print("Make sure your Lambda function is deployed and configured correctly.")
    print(f"\nTesting Lambda function: {tester.function_name}")
    
    input("\nPress Enter to start testing...")
    
    # Run all tests
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("💡 Tips:")
        print("   - Check CloudWatch logs for detailed error information")
        print("   - Ensure DynamoDB tables and S3 buckets are properly configured")
        print("   - Verify environment variables are set correctly")
        print("   - Make sure IAM role has necessary permissions")

if __name__ == "__main__":
    main()
