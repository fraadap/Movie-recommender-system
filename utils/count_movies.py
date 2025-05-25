import boto3

def count_movies():
    # Inizializza il client DynamoDB con endpoint locale
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Movies')
    
    # Esegui la scansione della tabella
    response = table.scan(Select='COUNT')
    count = response['Count']
    
    # Se ci sono più pagine, continua la scansione
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            Select='COUNT',
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        count += response['Count']
    
    print(f"Total movies in DynamoDB: {count}")
    return count

if __name__ == "__main__":
    count_movies()