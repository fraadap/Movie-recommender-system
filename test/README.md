# AWS Lambda Test Files - Movie Recommender System v2.0

## Descrizione
Questa cartella contiene 22 file JSON separati per testare tutte le funzioni Lambda del sistema di raccomandazione film. Ogni file contiene una richiesta HTTP completa che può essere copiata direttamente nella console AWS Lambda per il testing.

## Struttura dei Test

### Test di Autenticazione (MovieAuthFunction.py)
- **01_user_registration.json** - Registrazione nuovo utente
- **02_user_login.json** - Login utente esistente
- **03_token_refresh.json** - Refresh del token JWT
- **04_invalid_login.json** - Test credenziali non valide

### Test Dati Utente (MovieUserDataFunction.py)
- **05_get_favorites.json** - Ottieni film preferiti
- **06_add_favorite.json** - Aggiungi film ai preferiti
- **07_check_favorite_status.json** - Controlla stato preferito
- **08_remove_favorite.json** - Rimuovi dai preferiti
- **09_add_review.json** - Aggiungi recensione film
- **10_get_reviews.json** - Ottieni recensioni utente
- **11_get_user_activity.json** - Ottieni cronologia attività

### Test Ricerca e Raccomandazioni (search_lambda_router.py)
- **12_semantic_search.json** - Ricerca semantica con AI
- **13_content_based_recommendations.json** - Raccomandazioni basate su contenuto
- **14_similar_movies.json** - Film simili
- **15_collaborative_filtering.json** - Filtering collaborativo

### Test Gestione Errori
- **16_unauthorized_access.json** - Accesso non autorizzato
- **17_invalid_jwt.json** - Token JWT non valido
- **18_missing_request_body.json** - Body richiesta mancante
- **19_invalid_endpoint.json** - Endpoint inesistente
- **20_malformed_json.json** - JSON malformato

### Test Performance
- **21_large_search_query.json** - Query di ricerca lunga
- **22_high_top_k_recommendations.json** - Raccomandazioni con top_k alto

## Come Usare i Test

### 1. Nella Console AWS Lambda:
1. Vai alla console AWS Lambda
2. Seleziona la funzione Lambda da testare
3. Vai alla tab "Test"
4. Clicca "Create new test event"
5. Copia il contenuto del file JSON
6. Incolla nella finestra di test
7. Clicca "Test"

### 2. Ordine di Esecuzione Consigliato:
1. **Prima**: Test di autenticazione (01-04)
2. **Seconda**: Salva il JWT token dalla risposta del login
3. **Terza**: Sostituisci "YOUR_JWT_TOKEN_HERE" con il token reale
4. **Quarta**: Esegui test dati utente (05-11)
5. **Quinta**: Esegui test ricerca (12-15)
6. **Sesta**: Test errori e performance (16-22)

### 3. Sostituzione Valori:
- Sostituisci `YOUR_JWT_TOKEN_HERE` con token JWT reale ottenuto dal login
- Sostituisci `862` con ID film reali dal tuo database DynamoDB
- Modifica `testuser@example.com` con email di test diverse se necessario

## Note Importanti

### Compatibilità Lambda Handler:
Questi file JSON sono strutturati per essere compatibili direttamente con i Lambda function handlers che usano:
```python
def lambda_handler(event, context):
    path = event.get("path")
    method = event.get("httpMethod")
    headers = event.get("headers", {})
    body = event.get("body")
```

### Gestione Errori Attesi:
- **401**: Per test senza autenticazione o token non validi
- **400**: Per richieste malformate o dati mancanti
- **404**: Per endpoint inesistenti
- **200/201**: Per richieste valide successful

### Debug:
Se un test fallisce, controlla:
1. CloudWatch Logs: `/aws/lambda/YOUR_FUNCTION_NAME`
2. Variabili ambiente nel Config
3. Permessi IAM per DynamoDB e S3
4. Tabelle DynamoDB esistenti e configurate

## Struttura Risposta Attesa

### Test Auth (200/201):
```json
{
  "statusCode": 200,
  "body": "{\"token\": \"jwt_token_here\", \"user\": {...}}"
}
```

### Test Ricerca (200):
```json
{
  "statusCode": 200,
  "body": "{\"results\": [{\"movie_id\": \"123\", \"score\": 0.95}]}"
}
```

### Test Errori (4xx):
```json
{
  "statusCode": 401,
  "body": "{\"error\": \"Authentication required\"}"
}
```
