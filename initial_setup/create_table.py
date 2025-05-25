import boto3

def create_movies_table():
    dynamodb = boto3.resource('dynamodb')
    
    # Create the DynamoDB table
    table = dynamodb.create_table(
        TableName='Movies',
        KeySchema=[
            {
                'AttributeName': 'movie_id',
                'KeyType': 'HASH'  # Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'movie_id',
                'AttributeType': 'S'  # String
            }
        ],
        BillingMode='PAY_PER_REQUEST'  # On-demand capacity mode
    )

    # Wait until the table exists
    table.meta.client.get_waiter('table_exists').wait(TableName='Movies')
    print("Movies table created successfully!")

def create_reviews_table():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(
        TableName='Reviews',
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'movie_id', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'movie_id', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'MovieIndex',
                'KeySchema': [
                    {'AttributeName': 'movie_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'user_id', 'KeyType': 'RANGE'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.meta.client.get_waiter('table_exists').wait(TableName='Reviews')
    print("Reviews table created successfully!")

def create_users_table():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(
        TableName='MovieRecommender_Users',
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'UserIdIndex',
                'KeySchema': [
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.meta.client.get_waiter('table_exists').wait(TableName='MovieRecommender_Users')
    print("Users table created successfully!")

def create_favorites_table():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(
        TableName='MovieRecommender_Favorites',
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'movie_id', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'movie_id', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'MovieFavoritesIndex',
                'KeySchema': [
                    {'AttributeName': 'movie_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.meta.client.get_waiter('table_exists').wait(TableName='MovieRecommender_Favorites')
    print("Favorites table created successfully!")

def create_watched_table():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(
        TableName='MovieRecommender_Watched',
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'movie_id', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'movie_id', 'AttributeType': 'S'}
        ],
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'MovieWatchedIndex',
                'KeySchema': [
                    {'AttributeName': 'movie_id', 'KeyType': 'HASH'}
                ],
                'Projection': {'ProjectionType': 'ALL'}
            }
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.meta.client.get_waiter('table_exists').wait(TableName='MovieRecommender_Watched')
    print("Watched table created successfully!")

def create_preferences_table():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(
        TableName='MovieRecommender_Preferences',
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.meta.client.get_waiter('table_exists').wait(TableName='MovieRecommender_Preferences')
    print("Preferences table created successfully!")

def create_activity_table():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.create_table(
        TableName='MovieRecommender_Activity',
        KeySchema=[
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'N'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    table.meta.client.get_waiter('table_exists').wait(TableName='MovieRecommender_Activity')
    print("Activity table created successfully!")

if __name__ == "__main__":
    create_movies_table()
    create_reviews_table()
    create_users_table()
    create_favorites_table()
    create_watched_table()
    create_preferences_table()
    create_activity_table() 