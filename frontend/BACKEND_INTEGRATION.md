# Integrazione Frontend-Backend per Movie Recommender

Questo documento descrive in dettaglio come il frontend si integra con il backend AWS, i formati delle richieste e delle risposte, e i passi necessari per impostare correttamente l'ambiente.

## Architettura dell'integrazione

```
Frontend Vue.js <---> API Gateway <---> Lambda Functions <---> DynamoDB
```

Il frontend comunica con il backend tramite richieste REST all'API Gateway, che le inoltra alle Lambda Functions appropriate, le quali interagiscono con le tabelle DynamoDB.

## Configurazione dell'ambiente

### 1. Configurazione del Backend

#### 1.1 Creazione tabelle DynamoDB

Eseguire lo script `create_table.py` per creare le seguenti tabelle:
- `Movies` - Contiene i dati dei film
- `Reviews` - Contiene le recensioni degli utenti
- `MovieRecommender_Users` - Contiene i dati degli utenti
- `MovieRecommender_Favorites` - Contiene i film preferiti degli utenti
- `MovieRecommender_Watched` - Contiene i film visti dagli utenti
- `MovieRecommender_Preferences` - Contiene le preferenze degli utenti
- `MovieRecommender_Activity` - Contiene il log delle attività degli utenti

#### 1.2 Configurazione API Gateway

Eseguire lo script `api_gateway_setup.py` per configurare l'API Gateway con i seguenti endpoint:
- `/search` - Per la ricerca di film
- `/recommend` - Per le raccomandazioni di film
- `/content` - Per i dettagli di un film
- `/collaborative` - Per film simili basati su raccomandazioni collaborative
- `/auth/*` - Per autenticazione e gestione profilo
- `/user-data/*` - Per gestione preferiti e film visti
- `/user/*` - Per gestione preferenze e attività

#### 1.3 Configurazione Lambda Functions

Caricare le seguenti Lambda Functions:
- `search_lambda_router.py` - Per routing delle richieste di ricerca e raccomandazione
- `MovieAuthFunction.py` - Per autenticazione e gestione profilo
- `MovieUserDataFunction.py` - Per gestione dati utente

### 2. Configurazione del Frontend

Copiare il file `.env.example` in `.env` e modificare i seguenti valori:
```
VUE_APP_API_GATEWAY_URL=https://your-api-gateway-id.execute-api.eu-west-1.amazonaws.com/prod
VUE_APP_TMDB_API_KEY=your_tmdb_api_key
```

## Endpoint API e formati delle richieste/risposte

### Ricerca e raccomandazioni di film

#### 1. Ricerca film (`POST /search`)

**Richiesta:**
```json
{
  "query": "action movies with Tom Cruise",
  "top_k": 10
}
```

**Risposta:**
```json
[
  {
    "movie_id": "123",
    "title": "Mission: Impossible",
    "overview": "An American agent...",
    "vote_average": 7.5,
    "release_year": 1996,
    "poster_path": "/path/to/poster.jpg",
    "score": 0.95
  },
  // altri film...
]
```

#### 2. Raccomandazioni film (`POST /recommend`)

**Richiesta:**
```json
{
  "top_k": 10,
  "user_id": "user123" // opzionale
}
```

**Risposta:** Formato identico alla ricerca.

#### 3. Dettagli film (`POST /content`)

**Richiesta:**
```json
{
  "movie_ids": ["123"],
  "top_k": 1
}
```

**Risposta:** Formato identico alla ricerca.

#### 4. Film simili (`POST /collaborative`)

**Richiesta:**
```json
{
  "movie_id": "123",
  "top_k": 10
}
```

**Risposta:** Formato identico alla ricerca.

### Autenticazione

#### 1. Login (`POST /auth/login`)

**Richiesta:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Risposta:**
```json
{
  "token": "jwt-token-here",
  "user": {
    "id": "user123",
    "name": "John Doe",
    "email": "user@example.com",
    "created_at": 1620000000
  }
}
```

#### 2. Registrazione (`POST /auth/register`)

**Richiesta:**
```json
{
  "name": "John Doe",
  "email": "user@example.com",
  "password": "password123"
}
```

**Risposta:** Formato identico al login.

### Dati utente

#### 1. Ottieni preferiti (`GET /user-data/favorites`)

**Risposta:**
```json
{
  "movies": [
    {
      "user_id": "user123",
      "movie_id": "123",
      "created_at": 1620000000
    },
    // altri film...
  ]
}
```

#### 2. Aggiungi ai preferiti (`POST /user-data/favorites`)

**Richiesta:**
```json
{
  "movieId": "123"
}
```

**Risposta:**
```json
{
  "message": "Movie added to favorites"
}
```

#### 3. Toggle preferiti (`POST /user-data/favorites/toggle`)

**Richiesta:**
```json
{
  "movieId": "123"
}
```

**Risposta:**
```json
{
  "isFavorite": true/false,
  "message": "Movie added/removed from favorites"
}
```

## Autenticazione e Autorizzazione

Tutte le richieste che accedono a dati utente devono includere un token JWT nell'header di autorizzazione:

```
Authorization: Bearer <token>
```

Il token JWT viene generato durante il login o la registrazione e ha una validità di 24 ore.

## Risoluzione dei problemi comuni

### 1. Errore di CORS
Se si verifica un errore di CORS, verificare che l'API Gateway sia configurato per accettare richieste dal dominio frontend.

### 2. Errore di autenticazione
Se si verifica un errore di autenticazione, verificare che il token JWT sia valido e non sia scaduto.

### 3. Errore di connessione
Se si verifica un errore di connessione, verificare che l'URL dell'API Gateway sia corretto nel file `.env`.

## Tabelle DynamoDB e Schema

### MovieRecommender_Users
- Chiave primaria: `email` (String)
- GSI: `UserIdIndex` con chiave primaria `user_id` (String)
- Altri attributi: `name`, `password_hash`, `salt`, `created_at`, `updated_at`

### MovieRecommender_Favorites
- Chiave primaria: `user_id` (String), `movie_id` (String)
- GSI: `MovieFavoritesIndex` con chiave primaria `movie_id` (String)
- Altri attributi: `created_at`

### MovieRecommender_Watched
- Chiave primaria: `user_id` (String), `movie_id` (String)
- GSI: `MovieWatchedIndex` con chiave primaria `movie_id` (String)
- Altri attributi: `watched_at`, `rating` 