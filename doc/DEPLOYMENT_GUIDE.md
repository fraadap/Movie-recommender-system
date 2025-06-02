# Movie Recommender System - AWS Deployment Guide v2.0

This guide provides step-by-step instructions for deploying the Movie Recommender System v2.0 to AWS. The system features **centralized configuration management** and enhanced security, consisting of Lambda functions, DynamoDB tables, S3 storage, and API Gateway endpoints.

## What's New in v2.0

### Centralized Configuration Management
- **Single Config module** (`utils/config.py`) manages all environment variables
- **Automatic validation** of critical configuration parameters
- **Enhanced security** with consistent JWT and authentication handling
- **Simplified deployment** with reduced configuration complexity

### Enhanced Architecture
- **Shared utility functions** across all Lambda functions
- **Improved error handling** and response consistency
- **Better security** with input sanitization and activity logging
- **Simplified maintenance** with centralized code patterns

## Prerequisites

Before starting the deployment, ensure you have:

- **AWS CLI** installed and configured with appropriate credentials
- **Python 3.9 or higher** installed
- **pip** for Python package management
- **AWS Account** with sufficient permissions for:
  - DynamoDB (create tables, read/write operations)
  - Lambda (create functions, manage execution roles)
  - S3 (create buckets, upload/download objects)
  - API Gateway (create REST APIs, configure integrations)
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

## Step 1: Set Up AWS Infrastructure

### 1.1 Create S3 Bucket for Embeddings

Create an S3 bucket to store movie embeddings:

```bash
# Create bucket for embeddings (replace with your unique bucket name)
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

### 1.3 Create IAM Role for Lambda Functions

Create an IAM role with necessary permissions:

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

## Step 2.5: Configure Centralized Settings (NEW in v2.0)

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

**Note:** In v2.0, the deployment is simplified with centralized configuration and shared utilities.

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
  --threshold 0 ^
  --comparison-operator GreaterThanThreshold ^
  --evaluation-periods 1
```

#### Custom Monitoring Dashboard:
```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard ^
  --dashboard-name "MovieRecommenderDashboard" ^
  --dashboard-body file://dashboard-config.json
```

### 6.4 Cost Optimization

#### Cost Monitoring:
- **Lambda**: Monitor invocation count and duration
- **DynamoDB**: Track read/write capacity utilization  
- **S3**: Monitor storage and data transfer costs
- **API Gateway**: Track API requests and data transfer

#### Optimization Strategies:
1. **Use DynamoDB On-Demand** for unpredictable traffic
2. **Implement caching** in Lambda functions for frequently accessed data
3. **Optimize Lambda memory allocation** based on performance testing
4. **Use S3 Intelligent Tiering** for embeddings storage
5. **Monitor and right-size** resources regularly

### 6.5 Backup and Disaster Recovery

```bash
# Enable DynamoDB point-in-time recovery for all tables
aws dynamodb update-continuous-backups ^
  --table-name Movies ^
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb update-continuous-backups ^
  --table-name Reviews ^
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

aws dynamodb update-continuous-backups ^
  --table-name MovieRecommender_Users ^
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Enable S3 versioning for embeddings bucket
aws s3api put-bucket-versioning ^
  --bucket your-movie-embeddings-bucket ^
  --versioning-configuration Status=Enabled

# Create cross-region backup (optional)
aws dynamodb create-backup ^
  --table-name Movies ^
  --backup-name Movies-Backup-$(date +%Y%m%d)
```

## Troubleshooting Guide

### Common Deployment Issues

#### 1. Lambda Function Timeouts
**Symptoms:** API requests timeout after 30 seconds
**Solutions:**
```bash
# Increase Lambda timeout
aws lambda update-function-configuration ^
  --function-name MovieSearchFunction ^
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
