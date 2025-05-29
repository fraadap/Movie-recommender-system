import os
import boto3

dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'MovieRecommender_Users'))
favorites_table = dynamodb.Table(os.environ.get('FAVORITES_TABLE', 'MovieRecommender_Favorites'))
activity_table = dynamodb.Table(os.environ.get('ACTIVITY_TABLE', 'MovieRecommender_Activity'))
reviews_table = dynamodb.Table(os.environ.get('REVIEWS_TABLE', 'Reviews'))
movies_table = dynamodb.Table(os.environ.get('MOVIES_TABLE', 'Movies'))