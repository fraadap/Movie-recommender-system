# Movie Recommender System - AWS Deployment Guide

This guide provides step-by-step instructions for deploying the Movie Recommender System to AWS. The system features a **single Lambda function architecture** with centralized routing, ONNX optimization, and Lambda layers for dependency management.

### Enhanced Features
- **ONNX Models**: Pre-trained models converted to ONNX format for optimal performance
- **Embedding Storage**: Movie embeddings stored in .npz format in S3
- **Lambda Layers**: Two-layer dependency structure for efficient package management
- **Centralized Configuration**: Single config module for all environment variables
- **Improved Error Handling**: Consistent error responses across all endpoints

## Prerequisites

Before starting the deployment, ensure you have:

- **AWS CLI** installed and configured with appropriate credentials
- **Python 3.9 or higher** installed
- **pip** for Python package management
- **AWS Account** with sufficient permissions for:
  - DynamoDB (create tables, read/write operations)
  - Lambda (create functions, manage execution roles, manage layers)
  - S3 (create buckets, upload/download objects)
  - HTTP API Gateway (create APIs, configure integrations)
  - IAM (create and assign roles)
  - CloudWatch (access logs and metrics)

### Required AWS Permissions

Your AWS credentials should have the following permissions:
- `dynamodb:*`
- `lambda:*`
- `s3:*`
- `apigateway:*`
- `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:PassRole`
- `logs:*` (for CloudWatch)

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│  HTTP API       │    │  Single Lambda   │    │  DynamoDB       │
│  Gateway        │────▶│  Function        │────▶│  Tables         │
│                 │    │  (lambda_handler)│    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │                 │
                       │  Lambda Layers  │
                       │  (Dependencies) │
                       │                 │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │                 │
                       │  S3 Bucket      │
                       │  (ONNX Models & │
                       │   Embeddings)   │
                       └─────────────────┘
```

## Step 1: Set Up AWS Infrastructure

### 1.1 Create S3 Bucket for Embeddings and Models

Create an S3 bucket to store ONNX models and movie embeddings:

```bash
# Create bucket for embeddings and models (replace with your unique bucket name)
aws s3 mb s3://your-movie-embeddings-bucket --region us-east-1

# Verify bucket creation
aws s3 ls | grep movie-embeddings
```

**Note:** S3 bucket names must be globally unique. Choose a unique name and replace `your-movie-embeddings-bucket` throughout this guide.

### 1.2 Create DynamoDB Tables

The system requires 7 DynamoDB tables. Run the table creation script:

```bash
# Navigate to the initial_setup directory
cd initial_setup

# Create all required tables
python create_table.py
```

This creates the following tables:
- **Movies**: Main movie data (28MB, ~45,000 items)
- **Reviews**: User ratings (518MB, ~26M items) 
- **MovieRecommender_Users**: User profiles and authentication
- **MovieRecommender_Favorites**: User favorite movies
- **MovieRecommender_Watched**: User watch history  
- **MovieRecommender_Preferences**: User preferences and settings
- **MovieRecommender_Activity**: User activity tracking

### 1.3 Create IAM Role for Lambda Function

Create an IAM role with necessary permissions for the single Lambda function:

```bash
# Create role policy document
cat > lambda-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name MovieRecommenderLambdaRole \
  --assume-role-policy-document file://lambda-trust-policy.json

# Attach basic Lambda execution policy
aws iam attach-role-policy \
  --role-name MovieRecommenderLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create and attach custom policy for DynamoDB and S3 access
cat > lambda-permissions-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/Movies",
        "arn:aws:dynamodb:*:*:table/Reviews",
        "arn:aws:dynamodb:*:*:table/MovieRecommender_Users",
        "arn:aws:dynamodb:*:*:table/MovieRecommender_Favorites",
        "arn:aws:dynamodb:*:*:table/MovieRecommender_Activity"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::movieembeddings/*"
    }
  ]
}
EOF

# Create and attach the custom policy
aws iam create-policy \
  --policy-name MovieRecommenderLambdaPolicy \
  --policy-document file://lambda-permissions-policy.json

aws iam attach-role-policy \
  --role-name MovieRecommenderLambdaRole \
  --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/MovieRecommenderLambdaPolicy
```

## Step 2: Create Lambda Layers

### 2.1 Create Lambda Layer 1 (Core Dependencies)

```bash
# Create directory for layer 1
mkdir lambda-layer-1
cd lambda-layer-1
mkdir python

# Install core dependencies
pip install PyJWT bcrypt onnxruntime tokenizers -t python/

# Create layer zip
zip -r lambda-layer-1.zip python/

# Create the layer
aws lambda publish-layer-version \
  --layer-name MovieRecommenderLayer1 \
  --description "Core dependencies: PyJWT, bcrypt, onnxruntime, tokenizers" \
  --zip-file fileb://lambda-layer-1.zip \
  --compatible-runtimes python3.9

cd ..
```

### 2.2 Create Lambda Layer 2 (NumPy)

```bash
# Create directory for layer 2
mkdir lambda-layer-2
cd lambda-layer-2
mkdir python

# Install numpy with version constraint
pip install "numpy<1.27.0" -t python/

# Create layer zip
zip -r lambda-layer-2.zip python/

# Create the layer
aws lambda publish-layer-version \
  --layer-name MovieRecommenderLayer2 \
  --description "NumPy dependencies with version constraint" \
  --zip-file fileb://lambda-layer-2.zip \
  --compatible-runtimes python3.9

cd ..
```

## Step 3: Environment Variables Configuration

### 3.1 Configure Environment Variables

Set up the required environment variables for the Lambda function. The centralized configuration in `utils/config.py` manages all settings:

**Core Configuration:**
```bash
# JWT Configuration
export JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
export JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
export JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days

# DynamoDB Configuration
export DYNAMODB_REGION=us-east-1
export MOVIES_TABLE=Movies
export REVIEWS_TABLE=Reviews
export USERS_TABLE=MovieRecommender_Users
export FAVORITES_TABLE=MovieRecommender_Favorites
export ACTIVITY_TABLE=MovieRecommender_Activity

# S3 Configuration
export S3_BUCKET_NAME=movieembeddings
export S3_REGION=us-east-1
export ONNX_MODEL_KEY=sentence_transformer.onnx
export EMBEDDINGS_KEY=movie_embeddings.npz

# API Configuration
export DEFAULT_TOP_K=10
export MAX_TOP_K=100
```

### Configuration Benefits

The centralized configuration provides:
- **Single source of truth** for all environment variables
- **Automatic validation** of critical parameters  
- **Default values** for optional settings
- **Enhanced security** with consistent patterns
- **Simplified maintenance** across the single function

## Step 4: Deploy Single Lambda Function

### 4.1 Prepare Lambda Deployment Package

```bash
# Create deployment directory
mkdir lambda_deployment
cd lambda_deployment

# Copy the main handler and supporting modules
copy ..\lambda_handler.py .
copy ..\lambda_functions\*.py .
copy ..\utils\*.py .

# Create deployment package (layers handle dependencies)
zip -r movie_recommender_lambda.zip *.py

# Deploy the Lambda function
aws lambda create-function \
  --function-name MovieRecommenderFunction \
  --runtime python3.9 \
  --role arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/MovieRecommenderLambdaRole \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://movie_recommender_lambda.zip \
  --timeout 30 \
  --memory-size 512 \
  --layers \
    arn:aws:lambda:us-east-1:$(aws sts get-caller-identity --query Account --output text):layer:MovieRecommenderLayer1:1 \
    arn:aws:lambda:us-east-1:$(aws sts get-caller-identity --query Account --output text):layer:MovieRecommenderLayer2:1
```

### 4.2 Configure Environment Variables

```bash
# Set environment variables for the Lambda function
aws lambda update-function-configuration \
  --function-name MovieRecommenderFunction \
  --environment Variables='{
    "JWT_SECRET_KEY":"your-super-secret-jwt-key-change-this-in-production",
    "JWT_ACCESS_TOKEN_EXPIRES":"3600",
    "JWT_REFRESH_TOKEN_EXPIRES":"2592000",
    "DYNAMODB_REGION":"us-east-1",
    "MOVIES_TABLE":"Movies",
    "REVIEWS_TABLE":"Reviews", 
    "USERS_TABLE":"MovieRecommender_Users",
    "FAVORITES_TABLE":"MovieRecommender_Favorites",
    "ACTIVITY_TABLE":"MovieRecommender_Activity",
    "S3_BUCKET_NAME":"movieembeddings",
    "S3_REGION":"us-east-1",
    "ONNX_MODEL_KEY":"sentence_transformer.onnx",
    "EMBEDDINGS_KEY":"movie_embeddings.npz",
    "DEFAULT_TOP_K":"10",
    "MAX_TOP_K":"100"
  }'
```

## Step 5: Convert Models to ONNX and Upload to S3

### 5.1 Convert Sentence Transformer to ONNX

Use the provided conversion script:

```bash
# Run the ONNX conversion script
python initial_setup/convert_to_onnx.py
```

This will:
- Download the sentence-transformer model
- Convert it to ONNX format for optimized inference
- Upload the ONNX model to S3

### 5.2 Generate and Upload Embeddings

```bash
# Generate movie embeddings in .npz format
python initial_setup/generate_embeddings.py

# The script will automatically:
# - Generate embeddings for all movies
# - Save as .npz format (384 embeddings + 1 movie_id column)
# - Upload to S3 bucket
```

## Step 6: Set Up HTTP API Gateway

### 6.1 Create HTTP API

```bash
# Create HTTP API Gateway (not REST API)
aws apigatewayv2 create-api \
  --name MovieRecommenderAPI \
  --protocol-type HTTP \
  --description "Movie Recommender API with single Lambda function"
```

### 6.2 Create Lambda Integration

```bash
# Get the API ID from the previous command output
API_ID=your-api-id-here

# Create integration with the Lambda function
aws apigatewayv2 create-integration \
  --api-id $API_ID \
  --integration-type AWS_PROXY \
  --integration-uri arn:aws:lambda:us-east-1:$(aws sts get-caller-identity --query Account --output text):function:MovieRecommenderFunction \
  --payload-format-version 2.0
```

### 6.3 Create Routes

Since we have a single Lambda function with centralized routing, we create a catch-all route:

```bash
# Get integration ID from previous command
INTEGRATION_ID=your-integration-id-here

# Create catch-all route for all endpoints
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "ANY /{proxy+}" \
  --target integrations/$INTEGRATION_ID

# Create specific routes (optional, for better documentation)
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /auth/register" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /auth/login" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /auth/refresh" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /search" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /content" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /collaborative" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /similar" \
  --target integrations/$INTEGRATION_ID

# User data routes
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "GET /favorites" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /favorites" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "GET /favorites/{movie_id}" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "DELETE /favorites/{movie_id}" \
  --target integrations/$INTEGRATION_ID

# Review routes
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "GET /reviews" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "POST /reviews" \
  --target integrations/$INTEGRATION_ID

aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "DELETE /reviews/{review_id}" \
  --target integrations/$INTEGRATION_ID

# Activity route
aws apigatewayv2 create-route \
  --api-id $API_ID \
  --route-key "GET /activity" \
  --target integrations/$INTEGRATION_ID
```

### 6.4 Create Deployment Stage

```bash
# Create default stage
aws apigatewayv2 create-stage \
  --api-id $API_ID \
  --stage-name prod \
  --description "Production stage for Movie Recommender API"

# Get the API endpoint URL
aws apigatewayv2 get-api --api-id $API_ID --query 'ApiEndpoint'
```
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/Movies*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::your-movie-embeddings-bucket/*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name MovieRecommenderLambdaRole \
  --policy-name MovieRecommenderPolicy \
  --policy-document file://lambda-permissions-policy.json
```

## Step 2: Data Ingestion and Processing

### 2.1 Prepare Dataset

Download the required dataset files:

1. Download the **Movies Dataset** from Kaggle (requires Kaggle account)
2. Place the following files in the project root:
   - `movies_metadata.csv` (34MB)
   - `credits.csv` (9MB) 
   - `ratings.csv` (676MB)

### 2.2 Process and Load Movie Data

```bash
# Navigate to initial_setup directory
cd initial_setup

# Set environment variables for data processing
set DYNAMODB_TABLE=Movies
set REVIEWS_TABLE=Reviews

# Process and load movie data into DynamoDB
python data_processor.py
```

This script will:
- Process ~45,000 movies from `movies_metadata.csv`
- Extract cast and crew information from `credits.csv`
- Load ~26 million ratings from `ratings.csv`
- Store processed data in DynamoDB tables

**Expected processing time:** 2-3 hours depending on your internet connection and AWS region.

### 2.3 Generate and Upload Movie Embeddings

```bash
# Set environment variables for embeddings
set EMBEDDINGS_BUCKET=your-movie-embeddings-bucket
set EMBEDDINGS_OUTPUT_FILE=embeddings.jsonl
set EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Install sentence-transformers if not already installed
pip install sentence-transformers

# Generate embeddings (this will take 30-45 minutes)
python generate_embeddings.py
```

This script will:
- Generate 384-dimensional embeddings for each movie using the sentence-transformers model
- Combine title, overview, genres, cast, and crew into descriptive text
- Save embeddings to both local file and S3 bucket
- Create a 23MB `embeddings.jsonl` file

## Step 2.5: Configure Centralized Settings (NEW in)

The system now uses a centralized configuration module that simplifies deployment and maintenance. All environment variables are managed through the `Config` class in `utils/config.py`.

### Key Configuration Variables

Set these environment variables for all Lambda functions:

```bash
# Core Configuration (Required)
set JWT_SECRET=your-super-secret-jwt-key-here
set EMBEDDINGS_BUCKET=your-movie-embeddings-bucket

# DynamoDB Tables (Use defaults or customize)
set USERS_TABLE=MovieRecommender_Users
set FAVORITES_TABLE=MovieRecommender_Favorites
set REVIEWS_TABLE=Reviews
set MOVIES_TABLE=Movies
set ACTIVITY_TABLE=MovieRecommender_Activity

# ML Configuration (Optional - defaults provided)
set EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
set EMBEDDINGS_OUTPUT_FILE=embeddings.jsonl

# Development/Testing (Optional)
set DYNAMODB_ENDPOINT_URL=http://localhost:8000
set S3_ENDPOINT_URL=http://localhost:4566
```

### Configuration Benefits

The centralized configuration provides:
- **Single source of truth** for all environment variables
- **Automatic validation** of critical parameters
- **Default values** for optional settings
- **Enhanced security** with consistent patterns
- **Simplified maintenance** across all functions

## Step 3: Deploy Lambda Functions

### 3.1 Install Dependencies and Prepare Deployment Packages

**Note:** In, the deployment is simplified with centralized configuration and shared utilities.

```bash
# Create deployment directories
mkdir lambda_deployments
cd lambda_deployments

# Create unified deployment package (recommended approach)
mkdir unified_deployment
cd unified_deployment

# Install all dependencies
pip install -r ..\..\requirements.txt -t .

# Copy all Lambda function files and shared utilities
copy ..\..\lambda_functions\*.py .
copy ..\..\utils\*.py .

# Create single ZIP package for all functions
powershell Compress-Archive -Path * -DestinationPath ..\movie_recommender_lambda.zip
cd ..
```

**Alternative: Separate deployment packages (if needed for function-specific optimization)**

```bash
# Create deployment package for Search Lambda
mkdir search_deployment
cd search_deployment

pip install -r ..\..\requirements.txt -t .
copy ..\..\lambda_functions\search_lambda_router.py .
copy ..\..\lambda_functions\RecommendationFunctions.py .
copy ..\..\lambda_functions\handler.py .
copy ..\..\utils\*.py .

powershell Compress-Archive -Path * -DestinationPath ..\search_lambda.zip
cd ..

# Create deployment package for Auth Lambda  
mkdir auth_deployment
cd auth_deployment

pip install -r ..\..\requirements.txt -t .
copy ..\..\lambda_functions\MovieAuthFunction.py .
copy ..\..\lambda_functions\handler.py .
copy ..\..\utils\*.py .

powershell Compress-Archive -Path * -DestinationPath ..\auth_lambda.zip
cd ..

# Create deployment package for User Data Lambda
mkdir userdata_deployment  
cd userdata_deployment

pip install -r ..\..\requirements.txt -t .
copy ..\..\lambda_functions\MovieUserDataFunction.py .
copy ..\..\lambda_functions\handler.py .
copy ..\..\utils\*.py .

powershell Compress-Archive -Path * -DestinationPath ..\userdata_lambda.zip
cd ..
```

### 3.2 Deploy Lambda Functions to AWS

Get your AWS account ID and the ARN of the IAM role created earlier:

```bash
# Get AWS account ID
aws sts get-caller-identity --query Account --output text

# Set your account ID (replace with actual value)
set AWS_ACCOUNT_ID=123456789012
set LAMBDA_ROLE_ARN=arn:aws:iam::%AWS_ACCOUNT_ID%:role/MovieRecommenderLambdaRole
```

#### 3.2.1 Deploy Search Lambda Function

```bash
aws lambda create-function ^
  --function-name MovieSearchFunction ^
  --runtime python3.9 ^
  --role %LAMBDA_ROLE_ARN% ^
  --handler search_lambda_router.lambda_handler ^
  --timeout 30 ^
  --memory-size 512 ^
  --zip-file fileb://search_lambda.zip ^
  --environment Variables={^
    "EMBEDDINGS_BUCKET"="your-movie-embeddings-bucket",^
    "EMBEDDINGS_OUTPUT_FILE"="embeddings.jsonl",^
    "EMBEDDING_MODEL"="sentence-transformers/all-MiniLM-L6-v2",^
    "DYNAMODB_TABLE"="Movies",^
    "REVIEWS_TABLE"="Reviews"^
  }
```

#### 3.2.2 Deploy Auth Lambda Function

```bash
aws lambda create-function ^
  --function-name MovieAuthFunction ^
  --runtime python3.9 ^
  --role %LAMBDA_ROLE_ARN% ^
  --handler MovieAuthFunction.lambda_handler ^
  --timeout 30 ^
  --memory-size 256 ^
  --zip-file fileb://auth_lambda.zip ^
  --environment Variables={^
    "USERS_TABLE"="MovieRecommender_Users"^
  }
```

#### 3.2.3 Deploy User Data Lambda Function

```bash
aws lambda create-function ^
  --function-name MovieUserDataFunction ^
  --runtime python3.9 ^
  --role %LAMBDA_ROLE_ARN% ^
  --handler MovieUserDataFunction.lambda_handler ^
  --timeout 30 ^
  --memory-size 256 ^
  --zip-file fileb://userdata_lambda.zip ^
  --environment Variables={^
    "USERS_TABLE"="MovieRecommender_Users",^
    "FAVORITES_TABLE"="MovieRecommender_Favorites",^
    "WATCHED_TABLE"="MovieRecommender_Watched",^
    "PREFERENCES_TABLE"="MovieRecommender_Preferences",^
    "ACTIVITY_TABLE"="MovieRecommender_Activity"^
  }
```

### 3.3 Verify Lambda Function Deployment

```bash
# List deployed functions
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'Movie')].{Name:FunctionName,Runtime:Runtime,Status:State}" --output table

# Test search function
aws lambda invoke ^
  --function-name MovieSearchFunction ^
  --payload "{\"path\":\"/search\",\"httpMethod\":\"POST\",\"body\":\"{\\\"query\\\":\\\"action movies\\\",\\\"top_k\\\":5}\"}" ^
  test_response.json

# Check response
type test_response.json
```

## Step 4: Set Up API Gateway

### 4.1 Automated API Gateway Setup

Use the provided script to automatically create and configure the API Gateway:

```bash
# Navigate to initial_setup directory
cd initial_setup

# Run API Gateway setup script
python api_gateway_setup.py ^
  --region us-east-1 ^
  --search-lambda-name MovieSearchFunction ^
  --auth-lambda-name MovieAuthFunction ^
  --userdata-lambda-name MovieUserDataFunction
```

This script will:
1. Create a new REST API named "MovieRecommenderAPI"
2. Set up all required endpoints and methods
3. Configure Lambda integrations for each endpoint
4. Enable CORS for all endpoints  
5. Deploy the API to a 'prod' stage
6. Output the API Gateway URL for testing

### 4.2 Manual API Gateway Setup (Alternative)

If you prefer manual setup or need to troubleshoot:

#### 4.2.1 Create REST API

```bash
# Create REST API
aws apigateway create-rest-api --name MovieRecommenderAPI --region us-east-1

# Get the API ID from the response
set API_ID=your-api-id

# Get the root resource ID
aws apigateway get-resources --rest-api-id %API_ID% --region us-east-1
set ROOT_RESOURCE_ID=your-root-resource-id
```

#### 4.2.2 Create Resources and Methods

```bash
# Create /search resource
aws apigateway create-resource ^
  --rest-api-id %API_ID% ^
  --parent-id %ROOT_RESOURCE_ID% ^
  --path-part search ^
  --region us-east-1

# Create POST method for /search
aws apigateway put-method ^
  --rest-api-id %API_ID% ^
  --resource-id %SEARCH_RESOURCE_ID% ^
  --http-method POST ^
  --authorization-type NONE ^
  --region us-east-1

# Set up Lambda integration (repeat for all endpoints)
aws apigateway put-integration ^
  --rest-api-id %API_ID% ^
  --resource-id %SEARCH_RESOURCE_ID% ^
  --http-method POST ^
  --type AWS_PROXY ^
  --integration-http-method POST ^
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:%AWS_ACCOUNT_ID%:function:MovieSearchFunction/invocations ^
  --region us-east-1
```

#### 4.2.3 Deploy API

```bash
# Deploy API to prod stage
aws apigateway create-deployment ^
  --rest-api-id %API_ID% ^
  --stage-name prod ^
  --region us-east-1

# Get API endpoint URL
echo "API Gateway URL: https://%API_ID%.execute-api.us-east-1.amazonaws.com/prod"
```

### 4.3 Configure Lambda Permissions

Grant API Gateway permission to invoke Lambda functions:

```bash
# Allow API Gateway to invoke Search Lambda
aws lambda add-permission ^
  --function-name MovieSearchFunction ^
  --statement-id api-gateway-invoke ^
  --action lambda:InvokeFunction ^
  --principal apigateway.amazonaws.com ^
  --source-arn "arn:aws:execute-api:us-east-1:%AWS_ACCOUNT_ID%:%API_ID%/*/*"

# Allow API Gateway to invoke Auth Lambda  
aws lambda add-permission ^
  --function-name MovieAuthFunction ^
  --statement-id api-gateway-invoke ^
  --action lambda:InvokeFunction ^
  --principal apigateway.amazonaws.com ^
  --source-arn "arn:aws:execute-api:us-east-1:%AWS_ACCOUNT_ID%:%API_ID%/*/*"

# Allow API Gateway to invoke User Data Lambda
aws lambda add-permission ^
  --function-name MovieUserDataFunction ^
  --statement-id api-gateway-invoke ^
  --action lambda:InvokeFunction ^
  --principal apigateway.amazonaws.com ^
  --source-arn "arn:aws:execute-api:us-east-1:%AWS_ACCOUNT_ID%:%API_ID%/*/*"
```

## Step 5: Testing and Verification

### 5.1 Test API Endpoints

Once deployment is complete, test the API endpoints using curl or a tool like Postman.

Replace `YOUR_API_ID` with your actual API Gateway ID:

```bash
set API_BASE_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod
```

#### 5.1.1 Test Search Functionality

```bash
# Test semantic search
curl -X POST "%API_BASE_URL%/search" ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"action movies with superheroes\",\"top_k\":5}"

# Test content-based recommendations  
curl -X POST "%API_BASE_URL%/content" ^
  -H "Content-Type: application/json" ^
  -d "{\"movie_id\":\"862\",\"top_k\":5}"

# Test collaborative filtering
curl -X POST "%API_BASE_URL%/collaborative" ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"1\",\"top_k\":5}"

# Test similar movies
curl -X POST "%API_BASE_URL%/similar" ^
  -H "Content-Type: application/json" ^
  -d "{\"movie_id\":\"862\",\"top_k\":5}"
```

#### 5.1.2 Test Authentication Endpoints

```bash
# Test user registration
curl -X POST "%API_BASE_URL%/auth/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"TestPass123!\",\"name\":\"Test User\"}"

# Test user login
curl -X POST "%API_BASE_URL%/auth/login" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"TestPass123!\"}"

# Save the token from login response for authenticated requests
set AUTH_TOKEN=your-jwt-token-here

# Test token refresh
curl -X POST "%API_BASE_URL%/auth/refresh" ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer %AUTH_TOKEN%" ^
  -d "{}"
```

#### 5.1.3 Test User Data Endpoints

```bash
# Test get user favorites (requires authentication)
curl -X GET "%API_BASE_URL%/user-data/favorites" ^
  -H "Authorization: Bearer %AUTH_TOKEN%"

# Test add to favorites
curl -X POST "%API_BASE_URL%/user-data/favorites" ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer %AUTH_TOKEN%" ^
  -d "{\"movie_id\":\"862\"}"

# Test get user reviews
curl -X GET "%API_BASE_URL%/user-data/reviews" ^
  -H "Authorization: Bearer %AUTH_TOKEN%"

# Test add review
curl -X POST "%API_BASE_URL%/user-data/reviews" ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer %AUTH_TOKEN%" ^
  -d "{\"movie_id\":\"862\",\"rating\":4.5,\"comment\":\"Great movie!\"}"

# Test get user activity
curl -X GET "%API_BASE_URL%/user/activity" ^
  -H "Authorization: Bearer %AUTH_TOKEN%"

# Test get user account info
curl -X GET "%API_BASE_URL%/user/account" ^
  -H "Authorization: Bearer %AUTH_TOKEN%"
```

### 5.2 Monitor CloudWatch Logs

Monitor Lambda function execution and debug issues:

```bash
# View search lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/MovieSearchFunction"

# Get recent log events (replace LOG_GROUP_NAME with actual name)
aws logs filter-log-events ^
  --log-group-name "/aws/lambda/MovieSearchFunction" ^
  --start-time 1609459200000

# View auth lambda logs  
aws logs filter-log-events ^
  --log-group-name "/aws/lambda/MovieAuthFunction" ^
  --start-time 1609459200000

# View user data lambda logs
aws logs filter-log-events ^
  --log-group-name "/aws/lambda/MovieUserDataFunction" ^
  --start-time 1609459200000
```

### 5.3 Test Frontend Integration (Optional)

If you have a frontend application:

1. Update frontend configuration with your API Gateway URL
2. Test user registration and login flows
3. Test search and recommendation features
4. Verify user data management functionality

## Step 6: Production Considerations and Optimization

### 6.1 Security Best Practices

```bash
# Enable CloudTrail for API activity monitoring
aws cloudtrail create-trail ^
  --name MovieRecommenderTrail ^
  --s3-bucket-name your-cloudtrail-bucket

# Configure API Gateway throttling
aws apigateway put-method ^
  --rest-api-id %API_ID% ^
  --resource-id %RESOURCE_ID% ^
  --http-method POST ^
  --throttle-rate-limit 1000 ^
  --throttle-burst-limit 2000

# Enable detailed monitoring for Lambda functions
aws lambda put-provisioned-concurrency-config ^
  --function-name MovieSearchFunction ^
  --provisioned-concurrency-config ProvisionedConcurrencyConfig=5
```

#### Security Checklist:
- ✅ Use IAM roles with minimal required permissions
- ✅ Enable CloudTrail for audit logging
- ✅ Configure API Gateway throttling limits
- ✅ Use HTTPS only for all endpoints
- ✅ Implement proper input validation in Lambda functions
- ✅ Monitor suspicious access patterns

### 6.2 Performance Optimization

#### Lambda Function Optimization:
```bash
# Increase memory for search function (CPU scales with memory)
aws lambda update-function-configuration ^
  --function-name MovieSearchFunction ^
  --memory-size 1024

# Set reserved concurrency to prevent cold starts
aws lambda put-reserved-concurrency ^
  --function-name MovieSearchFunction ^
  --reserved-concurrency-amount 10
```

#### DynamoDB Optimization:
```bash
# Enable auto-scaling for DynamoDB tables
aws application-autoscaling register-scalable-target ^
  --service-namespace dynamodb ^
  --resource-id "table/Movies" ^
  --scalable-dimension "dynamodb:table:ReadCapacityUnits" ^
  --min-capacity 5 ^
  --max-capacity 40000

# Enable point-in-time recovery
aws dynamodb update-continuous-backups ^
  --table-name Movies ^
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

### 6.3 Monitoring and Alerting

#### CloudWatch Alarms:
```bash
# Create alarm for Lambda errors
aws cloudwatch put-metric-alarm ^
  --alarm-name "MovieSearchFunction-Errors" ^
  --alarm-description "Alert on Lambda function errors" ^
  --metric-name Errors ^
  --namespace AWS/Lambda ^
  --statistic Sum ^
  --period 300 ^
  --threshold 5 ^
  --comparison-operator GreaterThanThreshold ^
  --dimensions Name=FunctionName,Value=MovieSearchFunction ^
  --evaluation-periods 2

# Create alarm for API Gateway latency
aws cloudwatch put-metric-alarm ^
  --alarm-name "API-Gateway-Latency" ^
  --alarm-description "Alert on high API latency" ^
  --metric-name Latency ^
  --namespace AWS/ApiGateway ^
  --statistic Average ^
  --period 300 ^
  --threshold 5000 ^
  --comparison-operator GreaterThanThreshold ^
  --evaluation-periods 2

# Create alarm for DynamoDB throttling
aws cloudwatch put-metric-alarm ^
  --alarm-name "DynamoDB-Throttling" ^
  --alarm-description "Alert on DynamoDB throttling" ^
  --metric-name ThrottledRequests ^
  --namespace AWS/DynamoDB ^
  --statistic Sum ^
  --period 300 ^
  ## Step 7: Grant API Gateway Permissions

Grant API Gateway permission to invoke the Lambda function:

```bash
# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name MovieRecommenderFunction \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*"
```

## Step 8: Test the Deployment

### 8.1 API Endpoint Testing

```bash
# Get the API endpoint URL
API_ENDPOINT=$(aws apigatewayv2 get-api --api-id $API_ID --query 'ApiEndpoint' --output text)

# Test user registration
curl -X POST "$API_ENDPOINT/prod/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "securePassword123"
  }'

# Test semantic search
curl -X POST "$API_ENDPOINT/prod/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "action movies with explosions",
    "top_k": 5
  }'
```

### 8.2 Using Test Scripts

The project includes comprehensive test scripts:

```bash
# Run all endpoint tests
cd test
python lambda_endpoint_tests_v3.py

# Run specific curl tests
cd curl
run_all_tests.bat
```

## Step 9: Monitoring and Optimization

### 9.1 CloudWatch Monitoring

Set up monitoring for the single Lambda function:

```bash
# Create alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name "MovieRecommenderFunction-Errors" \
  --alarm-description "Alert on Lambda function errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=MovieRecommenderFunction \
  --evaluation-periods 2

# Create alarm for Lambda duration
aws cloudwatch put-metric-alarm \
  --alarm-name "MovieRecommenderFunction-Duration" \
  --alarm-description "Alert on high Lambda duration" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 25000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=MovieRecommenderFunction \
  --evaluation-periods 2

# Create alarm for API Gateway latency
aws cloudwatch put-metric-alarm \
  --alarm-name "API-Gateway-Latency" \
  --alarm-description "Alert on high API latency" \
  --metric-name Latency \
  --namespace AWS/ApiGateway \
  --statistic Average \
  --period 300 \
  --threshold 5000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### 9.2 Performance Optimization

#### Lambda Function Optimization:
- **Memory**: Start with 512MB and adjust based on performance metrics
- **Timeout**: 30 seconds should be sufficient for most operations
- **Concurrency**: Monitor and set reserved concurrency if needed

#### Layer Management:
```bash
# Update Layer 1 when dependencies change
aws lambda publish-layer-version \
  --layer-name MovieRecommenderLayer1 \
  --description "Updated core dependencies" \
  --zip-file fileb://lambda-layer-1.zip \
  --compatible-runtimes python3.9

# Update Lambda function to use new layer version
aws lambda update-function-configuration \
  --function-name MovieRecommenderFunction \
  --layers \
    arn:aws:lambda:us-east-1:$(aws sts get-caller-identity --query Account --output text):layer:MovieRecommenderLayer1:2 \
    arn:aws:lambda:us-east-1:$(aws sts get-caller-identity --query Account --output text):layer:MovieRecommenderLayer2:1
```

### 9.3 Cost Optimization

#### Cost Monitoring:
- **Lambda**: Monitor invocation count and duration
- **DynamoDB**: Track read/write capacity utilization
- **S3**: Monitor storage and data transfer costs
- **API Gateway**: Track API requests and data transfer

#### Optimization Strategies:
1. **Use DynamoDB On-Demand** for unpredictable traffic
2. **Enable Lambda function caching** for ONNX models
3. **Optimize Lambda memory allocation** based on performance testing
4. **Use S3 Intelligent Tiering** for embeddings storage
5. **Monitor and right-size** resources regularly

### 9.4 Backup and Disaster Recovery

```bash
# Enable DynamoDB point-in-time recovery for all tables
aws dynamodb update-continuous-backups \
  --table-name Movies \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb update-continuous-backups \
  --table-name Reviews \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb update-continuous-backups \
  --table-name MovieRecommender_Users \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb update-continuous-backups \
  --table-name MovieRecommender_Favorites \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb update-continuous-backups \
  --table-name MovieRecommender_Activity \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Enable S3 versioning for embeddings bucket
aws s3api put-bucket-versioning \
  --bucket movieembeddings \
  --versioning-configuration Status=Enabled

# Create cross-region backup (optional)
aws dynamodb create-backup \
  --table-name Movies \
  --backup-name Movies-Backup-$(date +%Y%m%d)
```

## Troubleshooting Guide

### Common Deployment Issues

#### 1. Lambda Function Timeouts
**Symptoms:** API requests timeout after 30 seconds
**Solutions:**
```bash
# Increase Lambda timeout
aws lambda update-function-configuration \
  --function-name MovieRecommenderFunction \
  --timeout 60

# Check CloudWatch logs for performance bottlenecks
aws logs filter-log-events \
  --log-group-name /aws/lambda/MovieRecommenderFunction \
  --start-time $(date -d '1 hour ago' +%s)000
```

#### 2. ONNX Model Loading Issues
**Symptoms:** Semantic search fails with model loading errors
**Solutions:**
```bash
# Verify ONNX model exists in S3
aws s3 ls s3://movieembeddings/sentence_transformer.onnx

# Check Lambda logs for specific error messages
aws logs describe-log-groups \
  --log-group-name-prefix /aws/lambda/MovieRecommenderFunction

# Increase Lambda memory if model loading fails
aws lambda update-function-configuration \
  --function-name MovieRecommenderFunction \
  --memory-size 1024
```

#### 3. Layer Dependency Issues
**Symptoms:** Import errors or missing modules
**Solutions:**
```bash
# Verify layers are attached to function
aws lambda get-function-configuration \
  --function-name MovieRecommenderFunction \
  --query 'Layers'

# Check layer contents
aws lambda get-layer-version \
  --layer-name MovieRecommenderLayer1 \
  --version-number 1

# Recreate layers if necessary
rm -rf lambda-layer-1
mkdir -p lambda-layer-1/python
pip install PyJWT bcrypt onnxruntime tokenizers -t lambda-layer-1/python/
cd lambda-layer-1 && zip -r ../lambda-layer-1.zip python/
```

#### 4. API Gateway Integration Issues
**Symptoms:** API returns 502 Bad Gateway or integration timeouts
**Solutions:**
```bash
# Check API Gateway integration configuration
aws apigatewayv2 get-integration \
  --api-id $API_ID \
  --integration-id $INTEGRATION_ID

# Verify Lambda function permissions
aws lambda get-policy \
  --function-name MovieRecommenderFunction

# Test Lambda function directly
aws lambda invoke \
  --function-name MovieRecommenderFunction \
  --payload '{"httpMethod": "GET", "path": "/health"}' \
  response.json
```

#### 5. DynamoDB Connection Issues
**Symptoms:** Database connection errors or timeouts
**Solutions:**
```bash
# Verify DynamoDB tables exist
aws dynamodb list-tables

# Check table status
aws dynamodb describe-table \
  --table-name Movies \
  --query 'Table.TableStatus'

# Test DynamoDB connectivity
aws dynamodb scan \
  --table-name Movies \
  --max-items 1
```

### Performance Troubleshooting

#### Lambda Cold Starts
- **Monitor**: CloudWatch Duration metrics
- **Solution**: Consider provisioned concurrency for high-traffic endpoints
- **Optimization**: Keep function warm with scheduled invocations

#### ONNX Model Performance
- **Monitor**: Model loading time in logs
- **Solution**: Increase Lambda memory allocation
- **Optimization**: Cache models in /tmp directory

#### DynamoDB Performance
- **Monitor**: CloudWatch ConsumedReadCapacityUnits/ConsumedWriteCapacityUnits
- **Solution**: Switch to On-Demand billing or increase provisioned capacity
- **Optimization**: Use DynamoDB Accelerator (DAX) for caching

### Log Analysis

```bash
# View recent Lambda logs
aws logs tail /aws/lambda/MovieRecommenderFunction --follow

# Search for specific errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/MovieRecommenderFunction \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# Export logs for analysis
aws logs create-export-task \
  --log-group-name /aws/lambda/MovieRecommenderFunction \
  --from $(date -d '1 day ago' +%s)000 \
  --to $(date +%s)000 \
  --destination movierecommender-logs
```

## Maintenance and Updates

### Regular Maintenance Tasks

1. **Monitor Performance Metrics**
   - Lambda duration and error rates
   - DynamoDB read/write capacity utilization
   - API Gateway request rates and latency

2. **Update Dependencies**
   - Recreate Lambda layers when dependencies need updates
   - Update ONNX models if sentence transformer versions change
   - Keep Python runtime updated

3. **Security Updates**
   - Rotate JWT secret keys periodically
   - Review IAM policies and permissions
   - Update Lambda function security groups if used

4. **Data Maintenance**
   - Monitor DynamoDB storage usage
   - Clean up old user activity records if needed
   - Update movie embeddings when dataset changes

### Updating the System

#### Function Code Updates:
```bash
# Update Lambda function code
zip -r movie_recommender_lambda_v2.zip *.py
aws lambda update-function-code \
  --function-name MovieRecommenderFunction \
  --zip-file fileb://movie_recommender_lambda_v2.zip
```

#### Environment Variable Updates:
```bash
# Update environment variables
aws lambda update-function-configuration \
  --function-name MovieRecommenderFunction \
  --environment Variables='{
    "JWT_SECRET_KEY":"new-secret-key",
    "S3_BUCKET_NAME":"movieembeddings",
    "ONNX_MODEL_KEY":"sentence_transformer_v2.onnx"
  }'
```

#### Layer Updates:
```bash
# Create new layer version
aws lambda publish-layer-version \
  --layer-name MovieRecommenderLayer1 \
  --description "Updated dependencies version 2" \
  --zip-file fileb://lambda-layer-1-v2.zip \
  --compatible-runtimes python3.9

# Update function to use new layer
aws lambda update-function-configuration \
  --function-name MovieRecommenderFunction \
  --layers \
    arn:aws:lambda:us-east-1:ACCOUNT_ID:layer:MovieRecommenderLayer1:2 \
    arn:aws:lambda:us-east-1:ACCOUNT_ID:layer:MovieRecommenderLayer2:1
```

## Conclusion

The Movie Recommender System provides a robust, scalable, and cost-effective serverless architecture with single Lambda function deployment, ONNX optimization, and Lambda layers for dependency management. The system is designed for:

- **High Performance**: ONNX models and efficient embedding storage
- **Cost Efficiency**: Single function architecture and layer optimization
- **Easy Maintenance**: Centralized configuration and simplified deployment
- **Scalability**: Serverless architecture with automatic scaling

For support and additional information, refer to:
- [README.md](README.md) - Complete system overview
- [api.yaml](api.yaml) - API specification
- [CHANGELOG_v2.0.md](CHANGELOG_v2.0.md) - Version 2.0 changes
- [Test scripts](../test/) - Comprehensive testing suite
  --timeout 60

# Increase memory allocation (improves CPU performance)
aws lambda update-function-configuration ^
  --function-name MovieSearchFunction ^
  --memory-size 1024
```

#### 2. DynamoDB Access Errors
**Symptoms:** "AccessDeniedException" in Lambda logs
**Solutions:**
```bash
# Verify IAM permissions
aws iam get-role-policy ^
  --role-name MovieRecommenderLambdaRole ^
  --policy-name MovieRecommenderPolicy

# Check table exists and region
aws dynamodb describe-table --table-name Movies --region us-east-1
```

#### 3. S3 Embeddings Not Found
**Symptoms:** "NoSuchKey" error when loading embeddings
**Solutions:**
```bash
# Verify embeddings file exists
aws s3 ls s3://your-movie-embeddings-bucket/

# Re-upload embeddings if missing
cd initial_setup
python generate_embeddings.py
```

#### 4. API Gateway 403 Errors
**Symptoms:** "Missing Authentication Token" errors
**Solutions:**
```bash
# Check API Gateway deployment
aws apigateway get-deployments --rest-api-id %API_ID%

# Verify Lambda permissions
aws lambda get-policy --function-name MovieSearchFunction

# Re-add permission if missing
aws lambda add-permission ^
  --function-name MovieSearchFunction ^
  --statement-id api-gateway-invoke ^
  --action lambda:InvokeFunction ^
  --principal apigateway.amazonaws.com
```

#### 5. CORS Issues
**Symptoms:** Browser blocks requests due to CORS policy
**Solutions:**
```bash
# Enable CORS for all methods
aws apigateway put-method-response ^
  --rest-api-id %API_ID% ^
  --resource-id %RESOURCE_ID% ^
  --http-method POST ^
  --status-code 200 ^
  --response-parameters method.response.header.Access-Control-Allow-Origin=true
```

### Performance Troubleshooting

#### 1. Slow Search Responses
**Diagnosis:**
```bash
# Check Lambda execution times in CloudWatch
aws logs filter-log-events ^
  --log-group-name "/aws/lambda/MovieSearchFunction" ^
  --filter-pattern "REPORT" ^
  --start-time 1609459200000
```

**Solutions:**
- Increase Lambda memory allocation
- Implement caching for embeddings
- Optimize similarity calculation algorithms

#### 2. DynamoDB Throttling
**Diagnosis:**
```bash
# Check for throttling metrics
aws cloudwatch get-metric-statistics ^
  --namespace AWS/DynamoDB ^
  --metric-name ThrottledRequests ^
  --dimensions Name=TableName,Value=Movies ^
  --start-time 2023-01-01T00:00:00Z ^
  --end-time 2023-01-02T00:00:00Z ^
  --period 3600 ^
  --statistics Sum
```

**Solutions:**
- Enable auto-scaling for DynamoDB tables
- Switch to on-demand billing mode
- Optimize query patterns

### Monitoring and Debugging

#### 1. Enable Detailed Logging
```bash
# Set Lambda log level to DEBUG
aws lambda update-function-configuration ^
  --function-name MovieSearchFunction ^
  --environment Variables={LOG_LEVEL=DEBUG}
```

#### 2. Enable X-Ray Tracing
```bash
# Enable tracing for Lambda function
aws lambda update-function-configuration ^
  --function-name MovieSearchFunction ^
  --tracing-config Mode=Active
```

#### 3. Monitor Key Metrics
- **Lambda Duration**: Average execution time
- **Lambda Errors**: Error rate and types
- **API Gateway Latency**: Request/response times  
- **DynamoDB Consumed Capacity**: Read/write utilization
- **S3 Request Metrics**: Access patterns and errors

### Recovery Procedures

#### 1. Restore from Backup
```bash
# List available backups
aws dynamodb list-backups --table-name Movies

# Restore from backup
aws dynamodb restore-table-from-backup ^
  --target-table-name Movies-Restored ^
  --backup-arn arn:aws:dynamodb:us-east-1:123456789012:table/Movies/backup/01234567890123-12345678
```

#### 2. Redeploy Lambda Functions
```bash
# Update function code
aws lambda update-function-code ^
  --function-name MovieSearchFunction ^
  --zip-file fileb://search_lambda.zip

# Update environment variables
aws lambda update-function-configuration ^
  --function-name MovieSearchFunction ^
  --environment Variables={EMBEDDINGS_BUCKET=your-bucket-name}
```

## Maintenance and Operations

### Regular Maintenance Tasks

#### 1. Monthly Cost Review
```bash
# Generate cost report
aws ce get-cost-and-usage ^
  --time-period Start=2023-01-01,End=2023-02-01 ^
  --granularity MONTHLY ^
  --metrics "BlendedCost,UnblendedCost,UsageQuantity" ^
  --group-by Type=DIMENSION,Key=SERVICE

# Review top cost centers:
# - DynamoDB: Monitor read/write capacity
# - Lambda: Check invocation count and duration  
# - S3: Monitor storage and transfer costs
# - API Gateway: Track request volume
```

#### 2. Performance Monitoring
```bash
# Weekly performance review
aws cloudwatch get-metric-statistics ^
  --namespace AWS/Lambda ^
  --metric-name Duration ^
  --dimensions Name=FunctionName,Value=MovieSearchFunction ^
  --start-time 2023-01-01T00:00:00Z ^
  --end-time 2023-01-07T00:00:00Z ^
  --period 86400 ^
  --statistics Average,Maximum

# Check error rates
aws cloudwatch get-metric-statistics ^
  --namespace AWS/Lambda ^
  --metric-name Errors ^
  --dimensions Name=FunctionName,Value=MovieSearchFunction ^
  --start-time 2023-01-01T00:00:00Z ^
  --end-time 2023-01-07T00:00:00Z ^
  --period 86400 ^
  --statistics Sum
```

#### 3. Security Updates
```bash
# Update Lambda runtime (when new versions are available)
aws lambda update-function-configuration ^
  --function-name MovieSearchFunction ^
  --runtime python3.11

# Review and update IAM policies quarterly
aws iam list-attached-role-policies --role-name MovieRecommenderLambdaRole

# Update dependencies
pip list --outdated
pip install --upgrade sentence-transformers boto3
```

#### 4. Data Backup Verification
```bash
# Verify point-in-time recovery is enabled
aws dynamodb describe-continuous-backups --table-name Movies

# Test backup restoration procedure (quarterly)
aws dynamodb restore-table-from-backup ^
  --target-table-name Movies-Test-Restore ^
  --backup-arn arn:aws:dynamodb:us-east-1:123456789012:table/Movies/backup/latest
```

### Scaling Considerations

#### 1. Auto-Scaling Setup
```bash
# Enable DynamoDB auto-scaling
aws application-autoscaling register-scalable-target ^
  --service-namespace dynamodb ^
  --resource-id "table/Movies" ^
  --scalable-dimension "dynamodb:table:ReadCapacityUnits" ^
  --min-capacity 5 ^
  --max-capacity 1000

aws application-autoscaling put-scaling-policy ^
  --policy-name "Movies-ReadCapacity-ScalingPolicy" ^
  --service-namespace dynamodb ^
  --resource-id "table/Movies" ^
  --scalable-dimension "dynamodb:table:ReadCapacityUnits" ^
  --policy-type "TargetTrackingScaling" ^
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

#### 2. Lambda Concurrency Management
```bash
# Monitor concurrency usage
aws lambda get-account-settings

# Set reserved concurrency for critical functions
aws lambda put-reserved-concurrency ^
  --function-name MovieSearchFunction ^
  --reserved-concurrency-amount 50
```

### Disaster Recovery Plan

#### 1. Multi-Region Setup (Optional)
```bash
# Replicate DynamoDB tables to secondary region
aws dynamodb create-global-table ^
  --global-table-name Movies ^
  --replication-group RegionName=us-east-1 RegionName=us-west-2

# Replicate S3 bucket
aws s3api put-bucket-replication ^
  --bucket your-movie-embeddings-bucket ^
  --replication-configuration file://replication-config.json
```

#### 2. Recovery Time Objectives (RTO)
- **API Availability**: < 5 minutes (API Gateway + Lambda)
- **Data Recovery**: < 30 minutes (DynamoDB point-in-time recovery)
- **Full System Recovery**: < 2 hours (complete redeployment)

#### 3. Recovery Procedures
1. **Service Outage**: Redeploy Lambda functions and API Gateway
2. **Data Corruption**: Restore from DynamoDB backup
3. **Region Failure**: Failover to secondary region (if configured)
4. **Complete System Loss**: Redeploy from source code and backups

### Upgrade Procedures

#### 1. Lambda Function Updates
```bash
# Test updates in staging environment first
aws lambda create-alias ^
  --function-name MovieSearchFunction ^
  --name STAGING ^
  --function-version 1

# Blue/green deployment using aliases
aws lambda update-alias ^
  --function-name MovieSearchFunction ^
  --name PROD ^
  --function-version 2
```

#### 2. Database Schema Updates
```bash
# Add new attributes to existing items
aws dynamodb update-item ^
  --table-name Movies ^
  --key '{"movie_id":{"S":"862"}}' ^
  --update-expression "SET new_attribute = :val" ^
  --expression-attribute-values '{":val":{"S":"new_value"}}'

# Create new GSI for new query patterns
aws dynamodb update-table ^
  --table-name Movies ^
  --attribute-definitions AttributeName=new_attribute,AttributeType=S ^
  --global-secondary-index-updates '[{
    "Create": {
      "IndexName": "NewAttributeIndex",
      "KeySchema": [{"AttributeName": "new_attribute", "KeyType": "HASH"}],
      "Projection": {"ProjectionType": "ALL"}
    }
  }]'
```

---

## Conclusion

This deployment guide provides comprehensive instructions for setting up the Movie Recommender System on AWS. The system is designed to be cost-effective, scalable, and maintainable.

### Key Success Metrics:
- **Deployment Time**: 2-4 hours (including data processing)
- **Monthly Cost**: $10-30 (depending on usage)
- **API Response Time**: < 2 seconds (average)
- **System Availability**: > 99.9%

### Next Steps:
1. Complete the deployment following this guide
2. Set up monitoring and alerting
3. Test all endpoints thoroughly
4. Implement frontend integration
5. Configure production security measures
6. Establish maintenance procedures

For additional support, refer to the main README.md file or check the CloudWatch logs for detailed error information.
