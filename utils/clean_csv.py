import pandas as pd
import tqdm

try:
    movies_path = 'movies_metadata.csv'
    movies_df = pd.read_csv(movies_path)
    to_delete = []
    to_delete_str = []
    # print number of rows in movies_df
    print(f"Number of rows in movies_df: {len(movies_df)}")
    for idx, row in tqdm.tqdm(movies_df.iterrows(), total=len(movies_df), desc="Processing movies"):

        movie_id = str(row['id'])
        if pd.isna(row['title']) and not pd.isna(row['original_title']):
            movies_df.at[idx, 'title'] = row['original_title']
            
        if pd.isna(row['title']) or pd.isna(row['overview']) or pd.isna(row['id']):
            to_delete.append(movie_id)
            
    # remove from movies_df movies id with id in to_delete
    movies_df = movies_df[~movies_df['id'].isin(to_delete)]
    to_delete_str = [str(x) for x in to_delete]
    
    # print number of rows in movies_df
    print(f"Number of rows in movies_df after removing empty rows: {len(movies_df)}")
    # save movies_df to movies_clean.csv


    # open reviews.csv, remove rows with empty userId, movieId, or rating and removes all the rows with movieId in to_delete
    reviews_df = pd.read_csv('ratings_small.csv')
    print(f"Number of rows in reviews_df: {len(reviews_df)}")

    # Remove rows with empty values and movies that were deleted
    reviews_df['movieId'] = reviews_df['movieId'].astype(str)
    reviews_df = reviews_df.dropna(subset=['userId', 'movieId', 'rating'])
    reviews_df = reviews_df[~reviews_df['movieId'].isin(to_delete_str)]

    print(f"Number of rows in reviews_df after cleaning: {len(reviews_df)}")


    # do the same for credits.csv, if id is in to_delete, remove the row
    credits_df = pd.read_csv('credits.csv')
    print(f"Number of rows in credits_df: {len(credits_df)}")

    # Remove rows with empty values and movies that were deleted
    credits_df = credits_df.dropna(subset=['id'])
    credits_df['id'] = credits_df['id'].astype(str)
    credits_df = credits_df[~credits_df['id'].isin(to_delete_str)]
    print(f"Number of rows in credits_df after cleaning: {len(credits_df)}")
    
    movies_df.to_csv('movies.csv', index=False)
    reviews_df.to_csv('ratings_small.csv', index=False)
    credits_df.to_csv('credits.csv', index=False)
except Exception as e:
    print(f"Error occurred: {e}")

# saving

