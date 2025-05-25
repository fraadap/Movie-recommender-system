# Movie Recommender System - AWS Deployment Guide

## Prerequisites

- AWS CLI installed and configured with appropriate credentials
- Python 3.9 or higher
- Node.js 14 or higher
- Docker (for local testing)
- AWS Account with permissions for:
  - DynamoDB
  - Lambda
  - S3
  - API Gateway
  - Cognito
  - CloudWatch

## Step 1: Set Up AWS Infrastructure

### 1.1 Create S3 Buckets

```bash
# Create bucket for embeddings (DONE)
aws s3 mb s3://your-movie-embeddings-bucket --region your-region

# Create bucket for frontend hosting
aws s3 mb s3://your-movie-recommender-frontend --region your-region
```

### 1.2 Create DynamoDB Tables (DONE)

```bash
# Run the table creation script
python create_table.py
```

This will create all required tables:
- Movies
- Reviews
- MovieRecommender_Users
- MovieRecommender_Favorites
- MovieRecommender_Watched
- MovieRecommender_Preferences
- MovieRecommender_Activity

### 1.3 Set Up Cognito User Pool

1. Create a User Pool in AWS Console
2. Note down the Pool ID and App Client ID
3. Configure the following attributes:
   - email (required)
   - name
   - custom:preferences

## Step 2: Data Ingestion

### 2.1 Process Movie Data

```bash
# Set environment variables
set DYNAMODB_TABLE=Movies
set REVIEWS_TABLE=Reviews

# Run data processor
python data_processor.py
```

### 2.2 Generate and Upload Embeddings

```bash
# Set environment variables
set EMBEDDINGS_BUCKET=your-movie-embeddings-bucket
set EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Generate embeddings
python generate_embeddings.py
```

## Step 3: Deploy Lambda Functions

### 3.1 Create Lambda Package

```bash
# Create deployment package directory
mkdir deployment && cd deployment

# Install dependencies
pip install -r ../requirements.txt -t .

# Copy Lambda functions
copy ..\search_lambda.py .
copy ..\search_lambda_router.py .
copy ..\database.py .
copy ..\recommender.py .
copy ..\error_handler.py .
copy ..\cache.py .
copy ..\config.py .

# Create ZIP file
powershell Compress-Archive -Path * -DestinationPath ..\search_lambda.zip
cd ..

# Repeat for auth and user data functions
mkdir auth_deployment && cd auth_deployment
pip install -r ../requirements.txt -t .
copy ..\lambda_functions\MovieAuthFunction.py .
powershell Compress-Archive -Path * -DestinationPath ..\auth_lambda.zip
cd ..

mkdir userdata_deployment && cd userdata_deployment
pip install -r ../requirements.txt -t .
copy ..\lambda_functions\MovieUserDataFunction.py .
powershell Compress-Archive -Path * -DestinationPath ..\userdata_lambda.zip
cd ..
```

### 3.2 Create Lambda Functions

```bash
# Create search function
aws lambda create-function ^
  --function-name MovieSearchFunction ^
  --runtime python3.9 ^
  --role arn:aws:iam::your-account-id:role/lambda-role ^
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

# Create auth function
aws lambda create-function ^
  --function-name MovieAuthFunction ^
  --runtime python3.9 ^
  --role arn:aws:iam::your-account-id:role/lambda-role ^
  --handler MovieAuthFunction.lambda_handler ^
  --timeout 30 ^
  --memory-size 256 ^
  --zip-file fileb://auth_lambda.zip ^
  --environment Variables={^
    "USERS_TABLE"="MovieRecommender_Users",^
    "COGNITO_USER_POOL_ID"="your-user-pool-id",^
    "COGNITO_APP_CLIENT_ID"="your-app-client-id"^
  }

# Create user data function
aws lambda create-function ^
  --function-name MovieUserDataFunction ^
  --runtime python3.9 ^
  --role arn:aws:iam::your-account-id:role/lambda-role ^
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

## Step 4: Set Up API Gateway

```bash
# Create and configure API Gateway
python api_gateway_setup.py ^
  --region your-region ^
  --lambda-name MovieSearchFunction ^
  --auth-lambda-name MovieAuthFunction ^
  --user-lambda-name MovieUserDataFunction
```

This will:
1. Create a new REST API
2. Set up routes for all endpoints
3. Configure CORS
4. Create and configure Lambda integrations
5. Deploy the API to a 'prod' stage

## Step 5: Deploy Frontend

### 5.1 Configure Frontend Environment

Create `.env.production`:

```env
VUE_APP_API_GATEWAY_URL=https://your-api-id.execute-api.your-region.amazonaws.com/prod
VUE_APP_COGNITO_USER_POOL_ID=your-user-pool-id
VUE_APP_COGNITO_APP_CLIENT_ID=your-app-client-id
```

### 5.2 Build and Deploy Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Deploy to S3
aws s3 sync dist/ s3://your-movie-recommender-frontend
```

### 5.3 Configure S3 for Static Website Hosting

1. Enable static website hosting in S3 bucket properties
2. Configure bucket policy for public read access
3. Configure CloudFront distribution (optional, recommended)

## Step 6: Testing and Verification

### 6.1 Test API Endpoints

```bash
# Test search endpoint
curl -X POST ^
  https://your-api-id.execute-api.your-region.amazonaws.com/prod/search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"action movies\",\"top_k\":5}"

# Test auth endpoint (get token)
curl -X POST ^
  https://your-api-id.execute-api.your-region.amazonaws.com/prod/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"password123\"}"
```

### 6.2 Monitor CloudWatch Logs

1. Check Lambda function logs
2. Monitor API Gateway metrics
3. Set up CloudWatch alarms for errors and latency

## Step 7: Production Considerations

### 7.1 Security

- Enable AWS WAF for API Gateway
- Configure appropriate CORS settings
- Use AWS Secrets Manager for sensitive values
- Enable CloudTrail for API activity monitoring

### 7.2 Performance

- Configure Lambda concurrency limits
- Set up DynamoDB auto-scaling
- Configure CloudFront caching rules
- Monitor and adjust Lambda memory settings

### 7.3 Monitoring

- Set up CloudWatch dashboards
- Configure alarms for critical metrics
- Enable X-Ray tracing
- Set up error reporting

## Troubleshooting

### Common Issues

1. **Lambda Timeouts**
   - Increase memory allocation
   - Optimize code
   - Consider splitting into smaller functions

2. **DynamoDB Throttling**
   - Enable auto-scaling
   - Optimize query patterns
   - Consider read/write capacity units

3. **API Gateway Issues**
   - Check CORS configuration
   - Verify Lambda permissions
   - Check CloudWatch logss

4. **Authentication Problems**
   - Verify Cognito configuration
   - Check JWT token settings
   - Validate API Gateway authorizers

## Maintenance

### Regular Tasks

1. **Monitor Costs**
   - Review AWS Cost Explorer
   - Check resource utilization
   - Optimize where needed

2. **Updates**
   - Keep dependencies updated
   - Apply security patches
   - Update Lambda runtimes

3. **Backups**
   - Enable DynamoDB point-in-time recovery
   - Configure S3 versioning
   - Implement backup procedures

4. **Scaling**
   - Monitor usage patterns
   - Adjust resources as needed
   - Optimize performance
