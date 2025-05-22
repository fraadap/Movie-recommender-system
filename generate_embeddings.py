import os
import pandas as pd
import json
import boto3
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


def load_data(movies_path: str, credits_path: str):
    """Load movies metadata and credits dataframes."""
    movies_df = pd.read_csv(movies_path)
    credits_df = pd.read_csv(credits_path)
    credits_df.set_index('id', inplace=True)
    return movies_df, credits_df


def build_text(movie_row: pd.Series, credits_row: pd.Series) -> str:
    """Combine movie metadata and credits into a single text for embedding."""
    parts = []
    title = movie_row.get('title', '') or ''
    overview = movie_row.get('overview', '') or ''
    if title:
        parts.append(title)
    if overview:
        parts.append(overview)
    # genres
    try:
        genres = [g['name'] for g in json.loads(movie_row['genres'])] if pd.notna(movie_row['genres']) else []
    except:
        genres = []
    if genres:
        parts.append("Genres: " + ", ".join(genres))
    # actors
    actors = credits_row.get('actors', [])
    if actors:
        parts.append("Actors: " + ", ".join(actors))
    # directors
    directors = credits_row.get('directors', [])
    if directors:
        parts.append("Directors: " + ", ".join(directors))
    return ". ".join(parts)


def main():
    # Paths and config
    movies_path = os.getenv('MOVIES_CSV', 'movies_metadata.csv')
    credits_path = os.getenv('CREDITS_CSV', 'credits.csv')
    output_file = os.getenv('EMBEDDINGS_OUTPUT_FILE', 'embeddings.jsonl')
    model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')

    # S3 configuration
    s3_bucket = os.getenv('EMBEDDINGS_BUCKET')
    s3_endpoint = os.getenv('S3_ENDPOINT_URL')
    if s3_endpoint:
        s3_client = boto3.client('s3', endpoint_url=s3_endpoint)
    else:
        s3_client = boto3.client('s3')

    # Load model
    print(f"Loading model {model_name}...")
    model = SentenceTransformer(model_name)

    # Load data
    print("Loading data...")
    movies_df, credits_df = load_data(movies_path, credits_path)

    # Prepare output
    with open(output_file, 'w', encoding='utf-8') as f_out:
        # Generate embeddings
        print("Generating embeddings...")
        for _, row in tqdm(movies_df.iterrows(), total=len(movies_df)):
            movie_id = str(row['id'])
            if int(movie_id) not in credits_df.index:
                continue
            text = build_text(row, credits_df.loc[int(movie_id)])
            if not text.strip():
                continue
            embedding = model.encode(text).tolist()
            record = {'movie_id': movie_id, 'embedding': embedding}
            f_out.write(json.dumps(record) + "\n")

    # Upload to S3 if configured
    if s3_bucket:
        print(f"Uploading embeddings to s3://{s3_bucket}/{output_file} ...")
        s3_client.upload_file(output_file, s3_bucket, output_file)
        print("Upload complete.")

if __name__ == "__main__":
    main() 