import store from '@/store';

/**
 * Mappa degli errori comuni per fornire messaggi più user-friendly
 */
const ERROR_MESSAGES = {
  // Auth errors
  'invalid_credentials': 'Email o password non corrette',
  'email_already_exists': 'Questa email è già registrata',
  'weak_password': 'La password non soddisfa i requisiti minimi di sicurezza',
  'unauthorized': 'Sessione scaduta. Effettua nuovamente il login',
  'forbidden': 'Non hai i permessi per eseguire questa operazione',
  
  // API errors
  'not_found': 'La risorsa richiesta non è stata trovata',
  'bad_request': 'Richiesta non valida',
  'method_not_allowed': 'Operazione non consentita',
  'request_timeout': 'La richiesta ha impiegato troppo tempo. Riprova più tardi',
  
  // Network errors
  'network_error': 'Impossibile connettersi al server. Verifica la tua connessione',
  'server_error': 'Si è verificato un errore nel server. Riprova più tardi',
  
  // Default error
  'default': 'Si è verificato un errore. Riprova più tardi'
};

/**
 * Estrae il codice di errore dalla risposta API
 * @param {Object} error - L'oggetto errore di Axios
 * @returns {String} Il codice di errore o 'default'
 */
const getErrorCode = (error) => {
  if (error.response && error.response.data && error.response.data.code) {
    return error.response.data.code;
  }
  
  if (!error.response) {
    return 'network_error';
  }
  
  // Mappa gli status HTTP a codici di errore
  const statusMap = {
    400: 'bad_request',
    401: 'unauthorized',
    403: 'forbidden',
    404: 'not_found',
    405: 'method_not_allowed',
    408: 'request_timeout',
    500: 'server_error'
  };
  
  return statusMap[error.response.status] || 'default';
};

/**
 * Ottiene il messaggio di errore user-friendly in base al codice
 * @param {String} code - Il codice di errore
 * @returns {String} Messaggio di errore user-friendly
 */
const getErrorMessage = (code) => {
  return ERROR_MESSAGES[code] || ERROR_MESSAGES.default;
};

/**
 * Analizza un errore API e mostra un messaggio appropriato
 * @param {Object} error - L'oggetto errore di Axios
 * @param {String} customMessage - Messaggio personalizzato da mostrare invece di quello predefinito
 * @returns {Object} L'oggetto errore originale per facilitare il chaining
 */
export const handleApiError = (error, customMessage = null) => {
  const errorCode = getErrorCode(error);
  const message = customMessage || getErrorMessage(errorCode);
  
  // Log dell'errore in console per debugging
  console.error('API Error:', errorCode, error);
  
  // Ritorna l'errore originale per facilitare il chaining
  return error;
};

/**
 * Wrapper di try/catch per operazioni asincrone che utilizza handleApiError
 * @param {Function} asyncFn - Funzione asincrona da eseguire
 * @param {String} errorMessage - Messaggio di errore personalizzato
 * @returns {Promise} Una promise che risolve con il risultato o rigetta con l'errore gestito
 */
export const safeAsync = async (asyncFn, errorMessage = null) => {
  try {
    return await asyncFn();
  } catch (error) {
    handleApiError(error, errorMessage);
    throw error;
  }
};

/**
 * Centralizzazione della gestione degli errori nell'applicazione
 */
export default {
  /**
   * Gestisce gli errori API e mostra un messaggio appropriato
   * @param {Error} error - L'errore da gestire
   * @param {string} fallbackMessage - Messaggio di fallback se non si riesce a estrarre un messaggio dall'errore
   * @return {string} Il messaggio di errore estratto
   */
  handleApiError(error, fallbackMessage = 'Si è verificato un errore') {
    // Estrae il messaggio di errore
    const errorMessage = this.extractErrorMessage(error, fallbackMessage);
    
    // Registra l'errore nella console per debugging
    console.error('API Error:', error);
    
    return errorMessage;
  },
  
  /**
   * Estrae il messaggio di errore da un oggetto error
   * @param {Error} error - L'errore da cui estrarre il messaggio
   * @param {string} fallbackMessage - Messaggio di fallback
   * @return {string} Il messaggio di errore
   */
  extractErrorMessage(error, fallbackMessage) {
    if (!error) return fallbackMessage;
    
    // Cerca nelle varie posizioni possibili dei messaggi di errore
    return error.response?.data?.message || 
           error.response?.data?.error || 
           error.message || 
           fallbackMessage;
  },
  
  /**
   * Gestisce gli errori di validazione e restituisce gli errori in formato strutturato
   * @param {Error} error - L'errore di validazione
   * @param {Object} formErrors - L'oggetto degli errori del form da popolare
   * @return {Object} L'oggetto degli errori del form aggiornato
   */
  handleValidationErrors(error, formErrors = {}) {
    const validationErrors = error.response?.data?.errors || {};
    
    // Popola l'oggetto degli errori del form
    Object.keys(validationErrors).forEach(field => {
      formErrors[field] = validationErrors[field];
    });
    
    return formErrors;
  },
  
  /**
   * Gestisce errori generici nell'applicazione
   * @param {Error} error - L'errore da gestire
   * @param {string} context - Il contesto in cui si è verificato l'errore
   */
  handleAppError(error, context = 'App') {
    console.error(`${context} Error:`, error);
  }
}; 