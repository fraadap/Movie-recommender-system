from sentence_transformers import SentenceTransformer
import os
import boto3
from utils.config import Config
from transformers import AutoTokenizer, AutoModel
import torch
from pathlib import Path

def convert_and_optimize_model():
    """Convert sentence-transformer model to ONNX and optimize it"""
    
    print(f"Starting conversion of {Config.EMBEDDING_MODEL} to ONNX...")
    
    # Create output directory
    output_dir = "model_onnx"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:        # Load the model
        model = SentenceTransformer(Config.EMBEDDING_MODEL)
        base_model = model._first_module()
        
        # Get the underlying transformer model and tokenizer
        tokenizer = base_model.tokenizer
        transformer = base_model.auto_model
        
        # Create dummy input for ONNX export
        inputs = tokenizer("This is a test sentence", return_tensors="pt", padding=True, truncation=True)
        
        # Export to ONNX
        torch.onnx.export(
            transformer,
            (inputs['input_ids'], inputs['attention_mask']),
            f"{output_dir}/model.onnx",
            input_names=['input_ids', 'attention_mask'],
            output_names=['last_hidden_state'],
            dynamic_axes={
                'input_ids': {0: 'batch', 1: 'sequence'},
                'attention_mask': {0: 'batch', 1: 'sequence'},
                'last_hidden_state': {0: 'batch', 1: 'sequence'}
            },
            opset_version=14
        )
        
        print("Model converted to ONNX format")
        
        # Save tokenizer and configs
        tokenizer.save_pretrained(output_dir)
        transformer.config.save_pretrained(output_dir)
        print("Tokenizer and configs saved")
        
        # Upload to S3
        if Config.EMBEDDINGS_BUCKET:
            s3_client = boto3.client('s3')
            
            # Upload all files in the directory
            for root, _, files in os.walk(output_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    s3_key = os.path.join('model_onnx', file)
                    print(f"Uploading {local_path} to s3://{Config.EMBEDDINGS_BUCKET}/{s3_key}")
                    s3_client.upload_file(local_path, Config.EMBEDDINGS_BUCKET, s3_key)
            
            print("Model uploaded to S3 successfully")
    
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        raise

if __name__ == "__main__":
    convert_and_optimize_model()
