# Movie Recommender Frontend

Frontend per l'applicazione di raccomandazione film, integrato con AWS API Gateway e DynamoDB.

## Tecnologie utilizzate

- Vue.js 3 (Composition API)
- Vuex per state management
- Vue Router per routing
- Axios per chiamate API

## Struttura dell'integrazione backend

Il frontend si connette a DynamoDB attraverso i seguenti componenti AWS:

1. **API Gateway** - Punto di ingresso REST per tutte le richieste
2. **Lambda Functions** - Elaborano le richieste e interagiscono con DynamoDB
3. **DynamoDB** - Database NoSQL per la persistenza dei dati

### Endpoint API utilizzati

Il frontend utilizza i seguenti endpoint:

#### Ricerca e raccomandazioni di film
- `POST /search` - Ricerca semantica di film
- `POST /recommend` - Ottiene raccomandazioni personalizzate
- `POST /content` - Ottiene dettagli di un film specifico
- `POST /collaborative` - Ottiene film simili basati su raccomandazioni collaborative

#### Autenticazione utente
- `POST /auth/login` - Login utente
- `POST /auth/register` - Registrazione nuovo utente
- `POST /auth/refresh` - Aggiornamento token JWT
- `PUT /auth/password` - Cambio password
- `PUT /auth/profile` - Aggiornamento profilo utente

#### Dati utente
- `GET/POST /user-data/favorites` - Gestione film preferiti
- `DELETE /user-data/favorites/{movie_id}` - Rimozione dai preferiti
- `POST /user-data/favorites/toggle` - Toggle preferiti
- `GET/POST /user-data/watched` - Gestione film visualizzati
- `DELETE /user-data/watched/{movie_id}` - Rimozione dai visualizzati

#### Preferenze utente
- `GET/PUT /user/preferences` - Gestione preferenze utente
- `DELETE /user/account` - Eliminazione account
- `GET /user/activity` - Cronologia attività

## Configurazione frontend

1. Copia il file `.env.example` in `.env`
2. Aggiorna `VUE_APP_API_GATEWAY_URL` con l'URL del tuo API Gateway
3. Aggiungi la tua chiave TMDB API in `VUE_APP_TMDB_API_KEY` (opzionale, usata per immagini poster di fallback)

## Installazione e avvio

```bash
# Installazione dipendenze
npm install

# Avvio server di sviluppo
npm run serve

# Compilazione per produzione
npm run build
```

## Flusso di integrazione dati

1. L'utente effettua l'autenticazione tramite `/auth/login` o `/auth/register`
2. Il backend genera un token JWT che viene salvato nello store Vuex
3. Le richieste successive includono il token nell'header Authorization
4. I dati utente (preferiti, film visti, ecc.) vengono sincronizzati tra frontend e DynamoDB

### Sincronizzazione dati

Il componente `UserDataLoader` gestisce la sincronizzazione periodica dei dati:
- Al login utente
- Periodicamente ogni 30 minuti
- Su richiesta esplicita dell'utente

## Schema delle tabelle DynamoDB

Il frontend interagisce con le seguenti tabelle DynamoDB:

1. **MovieRecommender_Users** - Informazioni utente e credenziali
   - Chiave primaria: `email` (String)
   - Attributi: `user_id`, `name`, `password_hash`, `salt`, `created_at`, `updated_at`

2. **MovieRecommender_Favorites** - Film preferiti degli utenti
   - Chiave primaria: `user_id` (String), `movie_id` (String)
   - Attributi: `created_at`

3. **MovieRecommender_Watched** - Film visti dagli utenti
   - Chiave primaria: `user_id` (String), `movie_id` (String)
   - Attributi: `watched_at`, `rating`

4. **MovieRecommender_Preferences** - Preferenze utente
   - Chiave primaria: `user_id` (String)
   - Attributi: `email_notifications`, `auto_recommendations`, `dark_mode`, `updated_at`

5. **MovieRecommender_Activity** - Log attività utente
   - Chiave primaria: `user_id` (String), `timestamp` (Number)
   - Attributi: `action`, `data` 