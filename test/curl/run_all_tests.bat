@echo off
echo ========================================
echo AWS Lambda Movie Recommender System Tests
echo ========================================
echo.

REM Set base URL and JWT Token
set BASE_URL=https://kzy0xi6gle.execute-api.us-east-1.amazonaws.com/deploy
set JWT_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiOWRiN2FmYTItNmJkOC00ZTYwLTk4Y2MtMWQ1ZjYxMDdlOTQ5IiwiZW1haWwiOiJkYXByaWxlLmZyYW5jZXNjbzAyQGdtYWlsLmNvbSIsIm5hbWUiOiJmcmFhLmRhcCIsImlhdCI6MTc0OTEzMTUwNywiZXhwIjoxMTc0OTEzMTUwNn0.gmnOqH-cm-0BXmmGYG97B0X80AlThniWV-pa5hdvXvE

echo ===========================================
echo TEST 01: User Registration
echo ===========================================
curl -X POST %BASE_URL%/auth/register -H "Content-Type: application/json" -H "Origin: http://localhost:3000" -d "{\"name\": \"Test User\", \"email\": \"testuser@example.com\", \"password\": \"TestPassword123!\"}"
echo.
echo.

echo ===========================================
echo TEST 02: User Login
echo ===========================================
curl -X POST %BASE_URL%/auth/login -H "Content-Type: application/json" -H "Origin: http://localhost:3000" -d "{\"email\": \"testuser@example.com\", \"password\": \"TestPassword123!\"}"
echo.
echo.

echo ===========================================
echo TEST 03: Token Refresh
echo ===========================================
curl -X POST %BASE_URL%/auth/refresh -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{}"
echo.
echo.

echo ===========================================
echo TEST 04: Invalid Login
echo ===========================================
curl -X POST %BASE_URL%/auth/login -H "Content-Type: application/json" -H "Origin: http://localhost:3000" -d "{\"email\": \"nonexistent@example.com\", \"password\": \"wrongpassword\"}"
echo.
echo.

echo ===========================================
echo TEST 05: Add Favorite
echo ===========================================
curl -X POST %BASE_URL%/user-data/favorites -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{\"movieId\": \"862\"}"
echo.
echo.

echo ===========================================
echo TEST 06: Get Favorites
echo ===========================================
curl -X GET %BASE_URL%/user-data/favorites -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000"
echo.
echo.

echo ===========================================
echo TEST 07: Check Favorite Status
echo ===========================================
curl -X GET %BASE_URL%/user-data/favorites/toggle/862 -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000"
echo.
echo.

echo ===========================================
echo TEST 08: Remove Favorite
echo ===========================================
curl -X DELETE %BASE_URL%/user-data/favorites/862 -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000"
echo.
echo.

echo ===========================================
echo TEST 09: Add Review
echo ===========================================
curl -X POST %BASE_URL%/user-data/reviews -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{\"movieId\": \"862\", \"rating\": 4.5, \"review\": \"Great movie! Really enjoyed it.\"}"
echo.
echo.

echo ===========================================
echo TEST 10: Get Reviews
echo ===========================================
curl -X GET %BASE_URL%/user-data/reviews -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000"
echo.
echo.

echo ===========================================
echo TEST 10: Remove Review
echo ===========================================
curl -X DELETE %BASE_URL%/user-data/reviews/862 -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000"
echo.
echo.


echo ===========================================
echo TEST 11: Get User Activity
echo ===========================================
curl -X GET %BASE_URL%/user/activity -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000"
echo.
echo.

echo ===========================================
echo TEST 12: Semantic Search
echo ===========================================
curl -X POST %BASE_URL%/search -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{\"query\": \"action movies with superheroes and adventure\", \"top_k\": 10}"
echo.
echo.

echo ===========================================
echo TEST 13: Content Based Recommendations
echo ===========================================
curl -X POST %BASE_URL%/content -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{\"movie_ids\": [[\"862\", 5.0], [\"597\", 4.5], [\"680\", 4.0]], \"top_k\": 5}"
echo.
echo.

echo ===========================================
echo TEST 14: Similar Movies
echo ===========================================
curl -X POST %BASE_URL%/similar -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{\"movie_id\": \"862\", \"top_k\": 10}"
echo.
echo.

echo ===========================================
echo TEST 15: Collaborative Filtering
echo ===========================================
curl -X POST %BASE_URL%/collaborative -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{\"top_k\": 10}"
echo.
echo.

echo ===========================================
echo TEST 16: Unauthorized Access
echo ===========================================
curl -X GET %BASE_URL%/user-data/favorites -H "Content-Type: application/json" -H "Origin: http://localhost:3000"
echo.
echo.

echo ===========================================
echo TEST 17: Invalid JWT
echo ===========================================
curl -X GET %BASE_URL%/user-data/favorites -H "Content-Type: application/json" -H "Authorization: Bearer invalid_jwt_token_here" -H "Origin: http://localhost:3000"
echo.
echo.

echo ===========================================
echo TEST 18: Missing Request Body
echo ===========================================
curl -X POST %BASE_URL%/auth/login -H "Content-Type: application/json" -H "Origin: http://localhost:3000"
echo.
echo.

echo ===========================================
echo TEST 19: Invalid Endpoint
echo ===========================================
curl -X GET %BASE_URL%/nonexistent/endpoint -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000"
echo.
echo.

echo ===========================================
echo TEST 20: Malformed JSON
echo ===========================================
curl -X POST %BASE_URL%/user-data/favorites -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{\"movieId\": \"862\", \"invalid\": malformed_json}"
echo.
echo.

echo ===========================================
echo TEST 21: Large Search Query
echo ===========================================
curl -X POST %BASE_URL%/search -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{\"query\": \"I am looking for a very long detailed complex movie recommendation with specific criteria including excellent cinematography, outstanding acting performances, compelling storytelling, and award-winning direction that would appeal to sophisticated audiences\", \"top_k\": 15}"
echo.
echo.

echo ===========================================
echo TEST 22: High Top K Recommendations
echo ===========================================
curl -X POST %BASE_URL%/similar -H "Content-Type: application/json" -H "Authorization: Bearer %JWT_TOKEN%" -H "Origin: http://localhost:3000" -d "{\"movieId\": \"862\", \"top_k\": 50}"
echo.
echo.

echo ========================================
echo All tests completed!
echo ========================================
echo.
echo NOTE: Update the JWT_TOKEN variable at the top of this file with a valid token from the login response
echo.
pause
