import pandas as pd
import json
import boto3
from datetime import datetime
from decimal import Decimal
import os
from typing import Dict, List, Any
import tqdm
import zipfile
import sys
import re  # aggiungi questo import all'inizio del file
import time

class MovieDataProcessor:
    def __init__(self):
        # Initialize DynamoDB resource, support local endpoint for testing
        endpoint_url = os.getenv('DYNAMODB_ENDPOINT_URL')
        if endpoint_url:
            self.dynamodb = boto3.resource('dynamodb', endpoint_url=endpoint_url)
        else:
            self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('Movies')
        self.reviews_table = self.dynamodb.Table('Reviews')

    def clean_json_string(self, json_str: str) -> str:
        """Clean and fix common JSON string issues."""
        try:
            if isinstance(json_str, float) and pd.isna(json_str):
                return "[]"
            
            # Rimuovi eventuali caratteri di controllo
            json_str = ''.join(char for char in json_str if ord(char) >= 32)
            
            # Fix per le virgole mancanti tra oggetti
            json_str = re.sub(r'}\s*{', '},{', json_str)
            
            # Fix per i valori None/null
            json_str = json_str.replace('None', 'null')
            
            # Fix per le virgole extra alla fine degli oggetti
            json_str = re.sub(r',\s*}', '}', json_str)
            
            # Fix per le doppie quotes nei valori
            json_str = re.sub(r'(?<!\\)"(?=.*".*})', '\\"', json_str)
            
            return json_str
        except Exception as e:
            print(f"Error cleaning JSON string: {str(e)}")
            return "[]"

    def update_csv_file(self, df: pd.DataFrame, file_path: str):
        """Update CSV file after successful processing."""
        df.to_csv(file_path, index=False)

    def update_csv_after_row(self, df: pd.DataFrame, idx: int, file_path: str):
        """Remove a processed row and update the CSV file immediately."""
        df.drop(idx, inplace=True)
        df.to_csv(file_path, index=False)
        return df

    def process_credits(self, credits_path: str) -> Dict[str, Dict[str, List[str]]]:
        """Process credits.csv to extract cast and crew information."""
        credits_df = pd.read_csv(credits_path)
        credits_dict = {}
        
        for idx, row in credits_df.iterrows():
            try:
                movie_id = str(row['id'])
                
                # Pulizia e parsing del cast
                try:
                    cast_data = eval(row['cast']) if isinstance(row['cast'], str) else []
                    cast = [item for item in cast_data if isinstance(item, dict)]
                except:
                    print(f"Cast parsing error for movie {movie_id}")
                    cast = []
                
                # Pulizia e parsing del crew
                try:
                    crew_data = eval(row['crew']) if isinstance(row['crew'], str) else []
                    crew = [item for item in crew_data if isinstance(item, dict)]
                except:
                    print(f"Crew parsing error for movie {movie_id}")
                    crew = []
                
                # Get top actors (first 5)
                actors = [person['name'] for person in cast[:5] if 'name' in person]
                
                # Get directors
                directors = [person['name'] for person in crew if person.get('job') == 'Director' and 'name' in person]
                
                credits_dict[movie_id] = {
                    'actors': actors,
                    'directors': directors
                }
                
            except Exception as e:
                print(f"Error processing credits for movie {movie_id}: {str(e)}")
                credits_dict[movie_id] = {'actors': [], 'directors': []}
                continue
    
        return credits_dict

    def process_movies(self, movies_path: str, credits_dict: Dict[str, Dict[str, List[str]]]):
        """Process movies_metadata.csv and prepare items for DynamoDB."""
        print(f"\nStarting processing of movies from {movies_path}")
        movies_df = pd.read_csv(movies_path)
        
        processed_count = 0
        error_count = 0
        
        for idx, row in tqdm.tqdm(movies_df.iterrows(), total=len(movies_df), desc="Processing movies"):
           
            try:
                movie_id = str(row['id'])
                if movie_id == "0":
                    continue
                if pd.isna(row['title']) and not pd.isna(row['original_title']):
                    movies_df.at[idx, 'title'] = row['original_title']
                    
                # Skip if we don't have valid basic data
                if pd.isna(row['title']) or pd.isna(row['overview']) or pd.isna(row['id']):
                    print(f"Skipping movie {movie_id} due to missing title or overview.")
                    continue
                
                # Extract year from release date
                try:
                    release_date = datetime.strptime(row['release_date'], '%Y-%m-%d')
                    year = release_date.year
                except (ValueError, TypeError):
                    year = None
                
                # Get credits info
                credits_info = credits_dict.get(movie_id, {'actors': [], 'directors': []})
                # Prepare genres
                genres = []
                if not pd.isna(row['genres']):
                    try:
                        genres_data = eval(row['genres']) if isinstance(row['genres'], str) else []
                        genres = [g['name'] for g in genres_data if isinstance(g, dict) and 'name' in g]
                    except:
                        print(f"Genres parsing error for movie {movie_id}")
                
                # Convert adult string to boolean
                is_adult = str(row['adult']).lower() == 'true' if not pd.isna(row['adult']) else False
                
                # Prepare item for DynamoDB
                item = {
                    'movie_id': movie_id,
                    'title': row['title'],
                    'overview': row['overview'],
                    'genres': genres,
                    'actors': credits_info['actors'],
                    'directors': credits_info['directors'],
                    'vote_average': Decimal(str(row['vote_average'])) if not pd.isna(row['vote_average']) else Decimal('0'),
                    'vote_count': int(row['vote_count']) if not pd.isna(row['vote_count']) else 0,
                    'adult': is_adult,
                    'popularity': Decimal(str(row['popularity'])) if not pd.isna(row['popularity']) else Decimal('0')
                }
                
                if year:
                    item['release_year'] = year
                
                if not pd.isna(row['budget']):
                    item['budget'] = int(row['budget'])
                
                if not pd.isna(row['poster_path']):
                    item['poster_path'] = row['poster_path']
                
                # Upload to DynamoDB
                self.upload_to_dynamodb(item)
                
                # Update CSV immediately after successful processing
                movies_df.at[idx, 'id'] = 0
                
                if processed_count%1000 == 0:
                    movies_df.to_csv(movies_path, index=False)
                processed_count += 1
            except Exception as e:
                print(f"Error processing movie {movie_id}: {str(e)}")
                error_count += 1
                continue

        print(f"Finished processing movies. Processed: {processed_count}, Errors: {error_count}")

    def upload_to_dynamodb(self, item: Dict[str, Any]):
        """Upload a single item to DynamoDB."""
        try:
            self.table.put_item(Item=item)
        except Exception as e:
            print(f"Error uploading movie {item['movie_id']}: {str(e)}")

    def process_reviews(self, ratings_file: str):
        print(f"\nStarting processing of ratings from {ratings_file}")

        processed_count = 0
        error_count = 0
    
        ratings_df = pd.read_csv(ratings_file)

        for idx, row in tqdm.tqdm(ratings_df.iterrows(), total=len(ratings_df), desc="Processing ratings"):
            try:
                item = {
                    'user_id': str(int(row['userId'])),
                    'movie_id': str(int(row['movieId'])),
                    'rating': Decimal(str(row['rating'])),
                    'timestamp': int(row['timestamp'])
                }
                
                if ratings_df.at[idx, 'userId'] == 0:
                    continue
                
                self.upload_review(item)
                # Update CSV immediately after successful processing
                ratings_df.at[idx, 'userId'] = 0
                
                processed_count += 1
                if processed_count % 1000 == 0:
                    ratings_df.to_csv(ratings_file, index=False)
            except Exception as e:
                print(f"Error processing review {row.get('userId')}-{row.get('movieId')}: {e}")
                error_count += 1
        
        # Remove temporary file
        print(f"Finished processing ratings. Processed: {processed_count}, Errors: {error_count}")

    def upload_review(self, item: Dict[str, Any]):
        """Upload a single review item to DynamoDB."""
        try:
            self.reviews_table.put_item(Item=item)
        except Exception as e:
            print(f"Error uploading review {item.get('user_id')}-{item.get('movie_id')}: {e}")

def main():
    processor = MovieDataProcessor()
    
    # Process credits first
    credits_dict = processor.process_credits('credits.csv')
    # number of movies in credits_dict
    print(f"Number of movies in credits_dict: {len(credits_dict)}")
    
    # Process movies and upload to DynamoDB
    processor.process_movies('movies_metadata.csv', credits_dict)
    # Process user reviews from zip file and upload to DynamoDB
    processor.process_reviews('ratings_small.csv')

if __name__ == "__main__":
    main()
    
    
    
