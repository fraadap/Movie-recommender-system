# Movie Recommender System

A serverless movie recommendation system built on AWS, featuring semantic search with ONNX models, collaborative filtering, and comprehensive user management capabilities.

## Features

- **Semantic Search**: Natural language movie search using ONNX-optimized embeddings stored in S3
- **Collaborative Filtering**: Personalized recommendations based on user ratings and behavior
- **Content-Based Filtering**: Recommendations based on movie similarity using weighted embeddings
- **User Management**: JWT authentication, favorites, reviews, and activity tracking
- **Scalable Architecture**: Single Lambda function with centralized routing and configuration
- **ONNX Model Support**: Optimized inference without heavy ML dependencies

## Architecture Overview

The system uses a **single Lambda function** architecture with:
- **Single Entry Point**: `lambda_handler.py` routes all API requests
- **Centralized Configuration**: `utils/config.py` manages all environment variables
- **DynamoDB**: 5 tables for users, movies, reviews, favorites, and activity
- **S3 Storage**: Movie embeddings (.npz format) and ONNX models
- **HTTP API Gateway**: AWS HTTP API (not REST) for endpoint management
- **Lambda Layers**: Optimized dependency management

### Lambda Layers Structure
- **Layer 1**: `PyJWT==2.8.0`, `bcrypt==4.1.2`, `onnxruntime`, `tokenizers`
- **Layer 2**: `numpy<1.27.0`

## Quick Start

1. **Setup AWS Infrastructure**
   ```cmd
   cd initial_setup
   python create_table.py
   ```

2. **Deploy Single Lambda Function**
   ```cmd
   REM Package entire application
   powershell Compress-Archive -Path lambda_handler.py,lambda_functions,utils,requirements.txt -DestinationPath movie-recommender.zip
   aws lambda create-function --function-name Movie_recommender_system --runtime python3.9 --zip-file fileb://movie-recommender.zip
   ```

3. **Configure Environment Variables**
   ```cmd
   set JWT_SECRET=your-secret-key
   set EMBEDDINGS_BUCKET=movieembeddings
   set MODEL_BUCKET=movieembeddings
   ```

4. **Setup API Gateway**
   ```cmd
   cd initial_setup
   python api_gateway_setup.py
   ```

## API Endpoints

All endpoints are routed through a single Lambda function via HTTP API Gateway:

### Authentication
- `POST /auth/register` - User registration with email/password
- `POST /auth/login` - User login returning JWT token
- `POST /auth/refresh` - Refresh JWT token

### Search & Recommendations
- `POST /search` - Semantic search using ONNX model inference
- `POST /content` - Content-based recommendations from movie IDs with ratings
- `POST /collaborative` - Collaborative filtering (requires authentication)
- `POST /similar` - Find similar movies to a given movie

### User Data Management
- `GET /user-data/favorites` - Get user's favorite movies
- `POST /user-data/favorites` - Add movie to favorites
- `DELETE /user-data/favorites/{movieId}` - Remove from favorites
- `GET /user-data/favorites/toggle/{movieId}` - Check if movie is favorited
- `POST /user-data/reviews` - Add movie review with rating
- `GET /user-data/reviews` - Get user's reviews
- `DELETE /user-data/reviews/{movieId}` - Remove review
- `GET /user-data/reviews/toggle/{movieId}` - Check if movie is reviewed
- `GET /user/activity` - Get user activity history
- `DELETE /user/account` - Delete user account

## Data Format

### Embeddings
- **Format**: `.npz` (NumPy compressed archive)
- **Structure**: 385 columns (384 float embeddings + 1 string movie_id)
- **Storage**: S3 bucket `movieembeddings`

### ONNX Models
- **Model Files**: `config.json`, `model.onnx`, `tokenizer.json`, `vocab.txt`
- **Storage**: S3 bucket `movieembeddings/model_onnx/`
- **Purpose**: Optimized inference without sentence-transformers dependency

## Database Schema

### Tables (DynamoDB)
1. **Movies** - Movie metadata (title, overview, genres, etc.)
2. **Reviews** - User ratings and reviews (user_id, movie_id, rating, timestamp)
3. **MovieRecommender_Users** - User authentication (email, username, password_hash, salt)
4. **MovieRecommender_Favorites** - User favorites (user_id, movie_id, created_at)
5. **MovieRecommender_Activity** - User activity logs (user_id, timestamp, action, data)## Development

For detailed setup instructions, see:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment walkthrough
- [API Reference](api.yaml) - OpenAPI 3.0 specification
- [System Architecture](files.txt) - Detailed component overview

## Configuration

All environment variables are managed centrally in `utils/config.py`:

```python
# Required
JWT_SECRET = "your-jwt-secret"
EMBEDDINGS_BUCKET = "movieembeddings"

# Optional (with defaults)
JWT_EXPIRY = 7200  # 2 hours
MAX_RESULTS = 100
DEFAULT_TOP_K = 10
```

## Dataset

Download the following CSV files from Kaggle and place them in the `initial_setup` directory:
- `movies_metadata.csv`
- `credits.csv`
- `ratings_small.csv` (or `ratings.csv` for full dataset)

Kaggle dataset: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset

## Dependencies

The system uses Lambda Layers for optimized dependency management:

### Layer 1 Dependencies
```
PyJWT==2.8.0
bcrypt==4.1.2
onnxruntime
tokenizers
```

### Layer 2 Dependencies
```
numpy<1.27.0
```

### Application Dependencies (requirements.txt)
```
PyJWT==2.8.0
bcrypt==4.1.2
numpy<1.27.0
onnxruntime
tokenizers
```
## Testing
All the endopoints are tested on AWS lambda using JSON files in the `tests` directory. Each test file corresponds to a specific endpoint and includes sample requests and expected responses.

They are also tested using `curl` commands for remote testing. For example:

```bash
curl -X POST http://localhost:3000/auth/login -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "password"}'
curl -X POST http://localhost:3000/search -H "Content-Type: application/json" -d '{"query": "An action movie with a female superhero"}'
curl -X GET http://localhost:3000/user-data/favorites -H "Authorization: Bearer <token>"
```

## License

MIT License