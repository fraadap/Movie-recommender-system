# Movie Recommender Data Ingestion

## Overview
This module contains scripts to create the DynamoDB table and to process and upload movie metadata and credits into the table.

## Prerequisites
- Python 3.9+
- AWS credentials configured (e.g., via `~/.aws/credentials` or environment variables)
- Installed dependencies: `pip install -r requirements.txt`

## Dataset
Download the following CSV files from Kaggle and place them in this directory:
- `movies_metadata.csv`
- `credits.csv`

Kaggle dataset: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset

## Setup DynamoDB Table
Run the script to create the `Movies` table in DynamoDB:

```
python create_table.py
```

No additional configuration needed; the table uses on-demand billing.

## Data Processing and Upload
Once the table is created and the CSV files are present, run:

```
python data_processor.py
```

This will:
1. Parse `credits.csv` and extract top 5 actors and director(s).
2. Parse `movies_metadata.csv`, enrich with year, genres, budget, poster path.
3. Upload each movie item to the DynamoDB `Movies` table.

## DynamoDB Schema
- **Partition Key**: `movie_id` (string)
- **Attributes**:
  - `title` (string)
  - `overview` (string)
  - `release_year` (number)
  - `genres` (list of strings)
  - `actors` (list of strings)
  - `directors` (list of strings)
  - `vote_average` (number)
  - `vote_count` (number)
  - `budget` (number)
  - `poster_path` (string)

## Embedding Generation
After ingesting movies and reviews into DynamoDB, you can generate semantic embeddings for each movie and optionally upload them to S3.

### Prerequisites
- Ensure dependencies are installed: `pip install -r requirements.txt`
- The script uses `sentence-transformers/all-MiniLM-L6-v2` by default, customize with `EMBEDDING_MODEL`.
- If uploading to S3, you must have a bucket created and permissions configured.

### Environment Variables
- `MOVIES_CSV`: path to `movies_metadata.csv` (default: `movies_metadata.csv`)
- `CREDITS_CSV`: path to `credits.csv` (default: `credits.csv`)
- `EMBEDDINGS_OUTPUT_FILE`: file name for local JSONL output (default: `embeddings.jsonl`)
- `EMBEDDING_MODEL`: name of the SentenceTransformer model (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `EMBEDDINGS_BUCKET`: name of the S3 bucket to upload embeddings (optional)
- `S3_ENDPOINT_URL`: custom S3 endpoint (for local testing/minio, optional)

### Usage
```bash
# Generate embeddings locally (writes to embeddings.jsonl)
python generate_embeddings.py

# Upload to S3 (set EMBEDDINGS_BUCKET)
export EMBEDDINGS_BUCKET=<your-bucket-name>
python generate_embeddings.py
```

## Next Steps
- Generate embeddings for each movie and upload to S3.
- Implement AWS Lambda functions for semantic search and recommendation.

## Local Testing without AWS Costs
To avoid AWS charges, you can run DynamoDB locally or use a mock library:

### Using DynamoDB Local (CLI/Java or Docker)
- Download the [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html) jar or run the Docker image:
  ```bash
  # Docker
  docker run -d -p 8000:8000 --name dynamodb_local amazon/dynamodb-local
  ```
- Set the endpoint URL environment variable:
  ```bash
  # Linux/Mac
  export DYNAMODB_ENDPOINT_URL=http://localhost:8000
  # Windows (PowerShell)
  $Env:DYNAMODB_ENDPOINT_URL = "http://localhost:8000"
  ```
- Create tables and upload data locally:
  ```bash
  python create_table.py         # Creates Movies and Reviews tables on local DynamoDB
  python data_processor.py      # Uploads movies, credits, and ratings to local DynamoDB
  ```

### Using a Mock Library (Moto)
- Install **moto**: `pip install moto`
- Wrap your tests or scripts to use the moto server:
  ```python
  from moto import mock_dynamodb
  @mock_dynamodb
  def test_local_upload():
      # initialize tables and run data_processor.py logic here
      pass
  ```

Either approach lets you fully test ingestion and basic queries without incurring AWS costs.

## Dataset Updates
Also include `ratings.csv` (user reviews) in this directory before running `data_processor.py`. The script now:
1. Processes `ratings.csv` and uploads to the `Reviews` table.
2. Handles `movies_metadata.csv` and `credits.csv` as before.

## Lambda: Search & Recommendations
A Lambda function (`search_lambda.py`) supports three operations via the `operation` field in the event:

- **Semantic Search** (`operation="search"`):
  ```json
  {
    "operation": "search",
    "query": "Sci-fi adventure",
    "top_k": 10
  }
  ```
- **Content‑Based Filtering** (`operation="content"`):
  ```json
  {
    "operation": "content",
    "movie_ids": ["1", "2"],
    "top_k": 10
  }
  ```
- **Collaborative Filtering** (`operation="collaborative"`):
  ```json
  {
    "operation": "collaborative",
    "user_id": "42",
    "top_k": 10
  }
  ```

All responses return HTTP 200 and a JSON array of movie items enriched with a `score` field.

### Lambda Environment Variables
- `EMBEDDINGS_BUCKET`: S3 bucket name storing `embeddings.jsonl`
- `EMBEDDINGS_OUTPUT_FILE`: embeddings file in S3 (default: `embeddings.jsonl`)
- `EMBEDDING_MODEL`: SentenceTransformer model name (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `DYNAMODB_TABLE`: DynamoDB table for movies (default: `Movies`)
- `REVIEWS_TABLE`: DynamoDB table for reviews (default: `Reviews`)
- `DYNAMODB_ENDPOINT_URL`: (optional) custom DynamoDB endpoint (for local testing)
- `S3_ENDPOINT_URL`: (optional) custom S3 endpoint (for local testing)

## API Gateway Setup

The system uses API Gateway to expose endpoints for frontend communication. The `api_gateway_setup.py` script automates the creation of a properly configured API Gateway:

```bash
# Deploy API Gateway with endpoints for search, content-based, and collaborative filtering
python api_gateway_setup.py --region us-east-1 --lambda-name MovieSearchFunction
```

The script creates:
- `/search` endpoint for semantic search
- `/content` endpoint for content-based filtering
- `/collaborative` endpoint for collaborative filtering
- `/recommend` generic endpoint that routes based on the `operation` parameter

### CORS Configuration

All endpoints are configured with CORS support to allow requests from web browsers. For development, CORS is set to allow requests from any origin (`*`), but in production, it should be limited to specific domains.

### Throttling Settings

The API is configured with the following throttling limits:
- Rate limit: 100 requests per second
- Burst limit: 200 requests

You can modify these limits in the `api_gateway_setup.py` script.

## Lambda Router

The `search_lambda_router.py` script serves as a router for the Lambda function, handling requests from different API Gateway endpoints:

```
API Gateway → Lambda Router → Appropriate Search/Recommendation Function
```

The router:
1. Extracts operation type (search/content/collaborative) from the path or request body
2. Validates and transforms input parameters
3. Calls the appropriate function in `search_lambda.py`
4. Returns a properly formatted response with CORS headers

### JSON Request Formats

**For semantic search:**
```json
{
  "query": "avventura nello spazio",
  "top_k": 5
}
```

**For content-based filtering:**
```json
{
  "movie_ids": ["123", "456", "789"],
  "top_k": 10
}
```

**For collaborative filtering:**
```json
{
  "user_id": "42",
  "top_k": 8
}
```

### Response Format

```json
{
  "statusCode": 200,
  "headers": {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json"
  },
  "body": [
    {
      "movie_id": "123",
      "title": "Interstellar",
      "score": 0.87,
      "release_year": 2014,
      "genres": ["Adventure", "Drama", "Science Fiction"]
    },
    // more movies...
  ]
}
```

## Frontend Integration

To integrate with the API from a frontend application:

```javascript
// Example from a React application
async function searchMovies(query) {
  try {
    const response = await fetch('https://your-api-id.execute-api.region.amazonaws.com/prod/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        top_k: 10
      })
    });
    
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    
    const movies = await response.json();
    return movies;
  } catch (error) {
    console.error('Error searching movies:', error);
    return [];
  }
}
```

After API Gateway deployment, the endpoint URLs will be saved to `api_info.json` for reference.

## Deployment su AWS

Di seguito i passaggi per far girare l'intero sistema in AWS, inclusi DynamoDB, S3, Lambda e API Gateway.

### Prerequisiti AWS
- AWS CLI configurato:
  ```bash
  aws configure
  ```
- IAM Role con permessi:
  - DynamoDB: `CreateTable`, `DescribeTable`, `PutItem`, `GetItem`, `Query`
  - S3: `CreateBucket`, `PutObject`, `GetObject`
  - Lambda: `CreateFunction`, `UpdateFunctionCode`, `InvokeFunction`
  - IAM: `PassRole`
  - API Gateway: `CreateRestApi`, `CreateResource`, `PutMethod`, `Deploy`
- Docker (opzionale, per packaging)

### 1. Creazione delle Risorse AWS

1. **S3** – Crea il bucket per le embedding:
   ```bash
   aws s3 mb s3://<EMBEDDINGS_BUCKET> --region <your-region>
   ```

2. **DynamoDB** – Esegui lo script per creare le tabelle:
   ```bash
   # Usa il profilo AWS configurato
   python3 create_table.py
   ```
   Verranno create le tabelle `Movies` e `Reviews` in on‑demand mode.

3. **Upload Dati** – Ingestione metadati, review ed embedding:
   ```bash
   # Metadati e reviews
   python3 data_processor.py

   # Genera embedding e upload su S3
   export EMBEDDINGS_BUCKET=<EMBEDDINGS_BUCKET>
   python3 generate_embeddings.py
   ```

### 2. Packaging e Creazione della Lambda

#### 2.1 Creazione del package per Lambda
```bash
# Crea cartella di lavoro
mkdir package && cd package
# Installa dipendenze
pip install -r ../requirements.txt -t .
# Copia il codice della Lambda
cp ../search_lambda.py .
# Comprimi il package
zip -r ../search_lambda.zip .
cd ..
```

#### 2.2 Deploy della funzione Lambda
```bash
aws lambda create-function \
  --function-name MovieSearchFunction \
  --runtime python3.9 \
  --role arn:aws:iam::<ACCOUNT_ID>:role/<LAMBDA_EXEC_ROLE> \
  --handler search_lambda.lambda_handler \
  --timeout 30 \
  --memory-size 512 \
  --zip-file fileb://search_lambda.zip \
  --environment Variables='{ \
      "EMBEDDINGS_BUCKET":"<EMBEDDINGS_BUCKET>", \
      "EMBEDDINGS_OUTPUT_FILE":"embeddings.jsonl", \
      "EMBEDDING_MODEL":"sentence-transformers/all-MiniLM-L6-v2", \
      "DYNAMODB_TABLE":"Movies", \
      "REVIEWS_TABLE":"Reviews" \
  }'
```

### 3. Configurazione API Gateway

1. **Crea REST API**:
   ```bash
   aws apigateway create-rest-api --name "MovieRecommenderAPI"
   ```
2. **Recupera l'ID della root resource** e crea la resource `/recommend`:
   ```bash
   aws apigateway get-resources --rest-api-id <api-id>
   aws apigateway create-resource --rest-api-id <api-id> --parent-id <root-id> --path-part recommend
   ```
3. **Imposta metodo POST** e integrazione con Lambda:
   ```bash
   aws apigateway put-method --rest-api-id <api-id> --resource-id <rec-id> --http-method POST --authorization-type NONE
   aws apigateway put-integration --rest-api-id <api-id> --resource-id <rec-id> --http-method POST --type AWS_PROXY --integration-http-method POST --uri arn:aws:apigateway:<region>:lambda:path/2015-03-31/functions/arn:aws:lambda:<region>:<account-id>:function:MovieSearchFunction/invocations
   ```
4. **Permetti a API Gateway di invocare la Lambda**:
   ```bash
   aws lambda add-permission --function-name MovieSearchFunction --statement-id apigateway-access --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn arn:aws:execute-api:<region>:<account-id>:<api-id>/*/POST/recommend
   ```
5. **Deploy** l'API:
   ```bash
   aws apigateway create-deployment --rest-api-id <api-id> --stage-name prod
   ```

### 4. Test dell'Endpoint

Esegui una richiesta HTTP POST:
```bash
curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/prod/recommend \
  -H "Content-Type: application/json" \
  -d '{"operation":"search","query":"Inception","top_k":5}'
```

### Variabili d'ambiente della Lambda
- `EMBEDDINGS_BUCKET` – bucket S3 per gli embedding
- `EMBEDDINGS_OUTPUT_FILE` – file di embedding (`embeddings.jsonl`)
- `EMBEDDING_MODEL` – modello per generare query embedding
- `DYNAMODB_TABLE` – tabella DynamoDB per i film
- `REVIEWS_TABLE` – tabella DynamoDB per le recensioni
- `DYNAMODB_ENDPOINT_URL` – (opzionale, per testing locale)
- `S3_ENDPOINT_URL` – (opzionale, per testing locale) 