# Curl Test Scripts

Questa cartella contiene script batch per eseguire test automatizzati delle API del sistema di raccomandazione film.

## File disponibili

### `run_all_tests.bat`
Esegue tutti i 22 test in sequenza. Ogni test è preceduto da una descrizione e il comando curl è formattato su una singola linea.

**Utilizzo:**
```cmd
cd test\curl
run_all_tests.bat
```

## Configurazione

### JWT Token
Prima di eseguire i test che richiedono autenticazione (test 05-17, 19-22), è necessario:

1. Eseguire il test 02 (User Login) per ottenere un JWT token valido
2. Aggiornare la variabile `JWT_TOKEN` nel file batch con il token ottenuto

### URL Base
L'URL base è configurato come:
```
https://kzy0xi6gle.execute-api.us-east-1.amazonaws.com/deploy
```

Se il deployment è su un URL diverso, modificare la variabile `BASE_URL` nel file batch.

## Test disponibili

| Test | Descrizione | Endpoint | Metodo | Autenticazione |
|------|-------------|----------|---------|----------------|
| 01   | User Registration | `/auth/register` | POST | No |
| 02   | User Login | `/auth/login` | POST | No |
| 03   | Token Refresh | `/auth/refresh` | POST | Sì |
| 04   | Invalid Login | `/auth/login` | POST | No |
| 05   | Add Favorite | `/user-data/favorites` | POST | Sì |
| 06   | Get Favorites | `/user-data/favorites` | GET | Sì |
| 07   | Check Favorite Status | `/user-data/favorites/toggle/862` | GET | Sì |
| 08   | Remove Favorite | `/user-data/favorites/862` | DELETE | Sì |
| 09   | Add Review | `/user-data/reviews` | POST | Sì |
| 10   | Get Reviews | `/user-data/reviews` | GET | Sì |
| 10   | Remove Review | `/user-data/reviews/862` | DELETE | Sì |
| 11   | Get User Activity | `/user/activity` | GET | Sì |
| 12   | Semantic Search | `/search` | POST | No |
| 13   | Content Based Recommendations | `/content` | POST | No |
| 14   | Similar Movies | `/similar` | POST | No |
| 15   | Collaborative Filtering | `/collaborative` | POST | Sì |
| 16   | Unauthorized Access | `/user-data/favorites` | GET | No |
| 17   | Invalid JWT | `/user-data/favorites` | GET | No |
| 18   | Missing Request Body | `/auth/login` | POST | No |
| 19   | Invalid Endpoint | `/nonexistent/endpoint` | GET | Sì |
| 20   | Malformed JSON | `/user-data/favorites` | POST | Sì |
| 21   | Large Search Query | `/search` | POST | Sì |
| 22   | High Top K Recommendations | `/similar` | POST | Sì |

## Parametri dei test

### Content Based Recommendations (Test 13)
```json
{
  "movie_ids": [["862", 5.0], ["597", 4.5], ["680", 4.0]], 
  "top_k": 5
}
```
- `movie_ids`: Array di coppie `[movie_id, rating]` per i film valutati dall'utente
- `top_k`: Numero di raccomandazioni da restituire

### Similar Movies (Test 14)
```json
{
  "movie_id": "862", 
  "top_k": 10
}
```
- `movie_id`: ID del film di riferimento (singolo)
- `top_k`: Numero di film simili da restituire

### Collaborative Filtering (Test 15)
```json
{
  "top_k": 10
}
```
- `top_k`: Numero di raccomandazioni da restituire

### Semantic Search (Test 12, 21)
```json
{
  "query": "action movies with superheroes and adventure", 
  "top_k": 10
}
```
- `query`: Descrizione testuale del tipo di film cercato
- `top_k`: Numero di risultati da restituire

## Test di errore

I test 16-20 sono progettati per testare scenari di errore e dovrebbero restituire codici di errore appropriati:

- **Test 16**: Accesso non autorizzato (401) - manca Authorization header
- **Test 17**: JWT token non valido (401) - token malformato
- **Test 18**: Body della richiesta mancante (400) - POST senza body
- **Test 19**: Endpoint inesistente (404) - URL non valido
- **Test 20**: JSON malformato (400) - sintassi JSON non valida

## Differenze rispetto ai file JSON originali

I comandi curl nel batch file sono stati corretti rispetto ai file JSON nella cartella `test/` principale per riflettere gli endpoint e parametri effettivamente implementati nel sistema:

- **Endpoint raccomandazioni**: Usano path diretti (`/content`, `/similar`, `/collaborative`) invece di `/recommendations/*`
- **Check favorite status**: Usa `/user-data/favorites/toggle/{movieId}` per verificare stato
- **User activity**: Endpoint spostato da `/user-data/activity` a `/user/activity`
- **Parametri content-based**: Usa `movie_ids` array invece di singolo `movieId`
- **Parametri similar movies**: Usa `movie_id` invece di `movieId`
- **Test riordinati**: Add Favorite (05) e Get Favorites (06) scambiati di ordine
- **Nuovo test aggiunto**: Remove Review per completare le operazioni CRUD sulle recensioni
- **Nuovo file JSON creato**: `10_remove_review.json` per il test di rimozione recensioni

### File JSON corretti

I seguenti file JSON sono stati aggiornati per corrispondere al batch file corretto:

- `05_get_favorites.json` → Cambiato da GET a POST (Add Favorite)
- `06_add_favorite.json` → Cambiato da POST a GET (Get Favorites)  
- `13_content_based_recommendations.json` → Aggiunto Authorization header e corretto top_k
- `14_similar_movies.json` → Aggiunto Authorization header
- `22_high_top_k_recommendations.json` → Cambiato endpoint da `/content` a `/similar` e parametro da `movie_ids` a `movie_id`
- `10_remove_review.json` → Nuovo file creato per test DELETE recensioni

## Note

- Tutti i comandi curl sono formattati su una singola linea
- I test includono tutti gli header necessari (Content-Type, Authorization, Origin)
- I dati JSON nei body sono correttamente escaped per l'uso in batch Windows
- Il file include pause per permettere la visualizzazione dei risultati
- È stato aggiunto un test per la rimozione delle recensioni (Remove Review)
