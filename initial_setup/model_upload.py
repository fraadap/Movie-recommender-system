# upload_model_to_s3.py
import boto3
import os
from sentence_transformers import SentenceTransformer

def upload_model_to_s3():
    """Upload sentence-transformers model to S3"""
    
    # Download model locally
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)
    
    # Save model to local directory
    local_model_path = "./model"
    model.save(local_model_path)
    print(f"Model downloaded and saved to {local_model_path}")
if __name__ == "__main__":
    upload_model_to_s3()