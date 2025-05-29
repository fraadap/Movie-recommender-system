# Movie Recommender System

## Overview
A comprehensive cloud-based movie recommendation system built on AWS, featuring semantic search, content-based filtering, collaborative filtering, and user management capabilities. The system provides personalized movie recommendations through advanced AI embeddings and machine learning algorithms.

## Architecture
- **Backend**: AWS Lambda functions for serverless computing
- **Database**: DynamoDB for scalable data storage
- **Search**: Semantic search using SentenceTransformers embeddings stored in S3
- **API**: API Gateway for RESTful endpoints
- **Frontend**: Vue.js web application
- **Authentication**: JWT-based user authentication

## Prerequisites
- Python 3.9+
- Node.js 14+ (for frontend)
- AWS CLI configured with appropriate credentials
- AWS account with permissions for DynamoDB, Lambda, S3, and API Gateway
- Install dependencies: `pip install -r requirements.txt`

## Dataset
Download the following CSV files from Kaggle and place them in the `initial_setup` directory:
- `movies_metadata.csv`
- `credits.csv`
- `ratings_small.csv` (or `ratings.csv` for full dataset)

Kaggle dataset: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset

## Quick Start Guide

### 1. Initial Setup

Navigate to the `initial_setup` directory and create DynamoDB tables:

```cmd
cd initial_setup
python create_table.py
```

This creates the following tables:
- `Movies` - Movie metadata and details
- `Reviews` - User ratings and reviews
- `MovieRecommender_Users` - User accounts
- `MovieRecommender_Favorites` - User favorite movies
- `MovieRecommender_Activity` - User activity logs

### 2. Data Processing and Upload

Process and upload movie data to DynamoDB:

```cmd
python data_processor.py
```

This will:
1. Parse `credits.csv` and extract top 5 actors and directors
2. Parse `movies_metadata.csv`, enrich with genres, budget, and poster paths
3. Process `ratings_small.csv` for user reviews
4. Upload all data to respective DynamoDB tables

### 3. Generate and Upload Embeddings

Generate semantic embeddings for movies and upload to S3:

```cmd
set EMBEDDINGS_BUCKET=your-movie-embeddings-bucket
python generate_embeddings.py
```

This creates embeddings using `sentence-transformers/all-MiniLM-L6-v2` model.

### 4. Deploy Lambda Functions

Package and deploy the Lambda functions (see DEPLOYMENT_GUIDE.md for detailed steps):

```cmd
REM Create packages for each Lambda function
python api_gateway_setup.py --region your-region
```

### 5. Access the API

Once deployed, you can access the API endpoints for:
- Semantic movie search
- Content-based recommendations
- Collaborative filtering recommendations
- User authentication and management

## Database Schema

### Movies Table
- **Partition Key**: `movie_id` (string)
- **Attributes**:
  - `title` (string) - Movie title
  - `overview` (string) - Movie description
  - `release_year` (number) - Year of release
  - `genres` (list) - List of genre strings
  - `actors` (list) - Top 5 actors
  - `directors` (list) - Director names
  - `vote_average` (number) - Average rating
  - `vote_count` (number) - Number of votes
  - `budget` (number) - Movie budget
  - `poster_path` (string) - Poster image path
  - `adult` (boolean) - Adult content flag
  - `popularity` (number) - Popularity score

### Reviews Table
- **Partition Key**: `user_id` (string)
- **Sort Key**: `movie_id` (string)
- **Global Secondary Index**: `MovieIndex` (movie_id as partition key)
- **Attributes**:
  - `rating` (number) - User rating (1-5)
  - `timestamp` (number) - Unix timestamp

### User Tables
- **MovieRecommender_Users**: User account information
- **MovieRecommender_Favorites**: User favorite movies
- **MovieRecommender_Activity**: User activity logs

## API Endpoints

The system provides several Lambda functions accessible through API Gateway:

### Search and Recommendations (`search_lambda_router.py`)
- **POST /search** - Semantic search using AI embeddings
- **POST /content** - Content-based recommendations
- **POST /collaborative** - Collaborative filtering (requires authentication)
- **POST /similar** - Find similar movies

### Authentication (`MovieAuthFunction.py`)
- **POST /auth/login** - User login
- **POST /auth/register** - User registration
- **POST /auth/refresh** - Refresh JWT token

### User Data Management (`MovieUserDataFunction.py`)
- **GET /user-data/favorites** - Get user's favorite movies
- **POST /user-data/favorites** - Add movie to favorites
- **DELETE /user-data/favorites/{movieId}** - Remove from favorites
- **GET /user-data/favorites/toggle/{movieId}** - Check favorite status
- **GET /user-data/reviews** - Get user's reviews
- **POST /user-data/reviews** - Add movie review
- **DELETE /user-data/reviews/{movieId}** - Remove review
- **GET /user-data/reviews/toggle/{movieId}** - Check review status
- **GET /user/activity** - Get user activity history
- **DELETE /user/account** - Delete user account

See `api.yaml` for complete API documentation.

## Environment Variables

### Lambda Environment Variables
Set these in your Lambda function configurations:

#### Search Lambda
- `EMBEDDINGS_BUCKET`: S3 bucket storing embeddings
- `EMBEDDINGS_OUTPUT_FILE`: Embeddings file name (default: `embeddings.jsonl`)
- `EMBEDDING_MODEL`: SentenceTransformer model (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `DYNAMODB_TABLE`: Movies table name (default: `Movies`)
- `REVIEWS_TABLE`: Reviews table name (default: `Reviews`)

#### Auth Lambda
- `JWT_SECRET`: Secret key for JWT tokens
- `USERS_TABLE`: Users table name (default: `MovieRecommender_Users`)

#### User Data Lambda
- `JWT_SECRET`: Secret key for JWT tokens
- `USERS_TABLE`: Users table name
- `FAVORITES_TABLE`: Favorites table name
- `REVIEWS_TABLE`: Reviews table name
- `ACTIVITY_TABLE`: Activity table name

### Local Development Variables
- `DYNAMODB_ENDPOINT_URL`: Custom DynamoDB endpoint (for local testing)
- `S3_ENDPOINT_URL`: Custom S3 endpoint (for local testing)

## Local Testing without AWS Costs

You can test the system locally without incurring AWS charges:

### Using DynamoDB Local
```cmd
REM Download and run DynamoDB Local using Docker
docker run -d -p 8000:8000 --name dynamodb_local amazon/dynamodb-local

REM Set environment variable for local endpoint
set DYNAMODB_ENDPOINT_URL=http://localhost:8000

REM Create tables and upload data locally
python create_table.py
python data_processor.py
```

### Using LocalStack for S3
```cmd
REM Run LocalStack for S3 simulation
docker run -d -p 4566:4566 --name localstack localstack/localstack

REM Set environment variables
set S3_ENDPOINT_URL=http://localhost:4566
set EMBEDDINGS_BUCKET=local-embeddings

REM Generate embeddings locally
python generate_embeddings.py
```

## Project Structure

```
Cloud-Computing/
├── requirements.txt          # Python dependencies
├── doc/                     # Documentation
│   ├── README.md           # This file
│   ├── DEPLOYMENT_GUIDE.md # Detailed deployment instructions
│   └── api.yaml           # OpenAPI specification
├── initial_setup/          # Setup and data processing scripts
│   ├── create_table.py     # DynamoDB table creation
│   ├── data_processor.py   # Data ingestion and processing
│   ├── generate_embeddings.py # Generate AI embeddings
│   ├── api_gateway_setup.py # API Gateway configuration
│   └── config.py          # Configuration settings
├── lambda_functions/       # AWS Lambda function code
│   ├── search_lambda.py    # Core recommendation algorithms
│   ├── search_lambda_router.py # API routing for search
│   ├── MovieAuthFunction.py # User authentication
│   └── MovieUserDataFunction.py # User data management
├── utils/                  # Utility functions
│   ├── database.py         # Database connections
│   └── utils_function.py   # Common utilities
└── frontend/               # Vue.js web application
    ├── src/               # Source code
    ├── components/        # Vue components
    └── services/          # API services
```

## Deployment

For complete deployment instructions, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

For API documentation, see [api.yaml](api.yaml).

## Support

This system is designed for educational purposes as part of a Cloud Computing course. For issues or questions, refer to the documentation files in the `doc` directory.