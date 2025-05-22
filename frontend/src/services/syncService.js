import api from './api';
import store from '@/store';

/**
 * Service for synchronizing user data between frontend and backend
 */
const syncService = {
  /**
   * Synchronize favorites with the backend
   * @param {Array} favorites - List of movie IDs to sync
   */
  async syncFavorites(favorites) {
    try {
      // First get current favorites from backend
      const response = await api.getFavorites();
      const backendFavorites = response.data.movies || [];
      const backendIds = backendFavorites.map(m => m.movie_id);
      
      // Find new favorites to add (local but not on backend)
      const favoriteIds = favorites.map(m => m.movie_id);
      const toAdd = favoriteIds.filter(id => !backendIds.includes(id));
      
      // Find favorites to remove (on backend but not local)
      const toRemove = backendIds.filter(id => !favoriteIds.includes(id));
      
      // Perform additions
      for (const id of toAdd) {
        await api.addToFavorites(id);
      }
      
      // Perform removals
      for (const id of toRemove) {
        await api.removeFromFavorites(id);
      }
      
      return { added: toAdd.length, removed: toRemove.length };
    } catch (error) {
      console.error('Error syncing favorites:', error);
      return { error };
    }
  },
  
  /**
   * Synchronize watched movies with the backend
   * @param {Array} watched - List of watched movies to sync
   */
  async syncWatchedMovies(watched) {
    try {
      // First get current watched movies from backend
      const response = await api.getWatchedMovies();
      const backendWatched = response.data.movies || [];
      const backendIds = backendWatched.map(m => m.movie_id);
      
      // Find new watched movies to add (local but not on backend)
      const watchedIds = watched.map(m => m.movie_id);
      const toAdd = watchedIds.filter(id => !backendIds.includes(id));
      
      // Find watched movies to remove (on backend but not local)
      const toRemove = backendIds.filter(id => !watchedIds.includes(id));
      
      // Perform additions
      for (const id of toAdd) {
        await api.addToWatched(id);
      }
      
      // Perform removals
      for (const id of toRemove) {
        await api.removeFromWatched(id);
      }
      
      return { added: toAdd.length, removed: toRemove.length };
    } catch (error) {
      console.error('Error syncing watched movies:', error);
      return { error };
    }
  },
  
  /**
   * Load all user data from backend
   */
  async loadUserData() {
    const userId = store.getters['auth/userId'];
    if (!userId) return Promise.reject(new Error('Utente non autenticato'));

    try {
      // Caricamento parallelo dei dati
      await Promise.all([
        this.loadUserProfile(),
        this.loadFavoriteMovies(),
        this.loadWatchedMovies(),
        this.loadRecommendations()
      ]);
      
      return true;
    } catch (error) {
      console.error('Errore durante il caricamento dei dati utente:', error);
      throw error;
    }
  },
  
  /**
   * Carica il profilo utente dal backend
   */
  async loadUserProfile() {
    try {
      const userId = store.getters['auth/userId'];
      const response = await api.get(`/users/${userId}/profile`);
      
      // Aggiorna lo store con i dati del profilo
      if (response.data) {
        store.commit('auth/SET_USER_PROFILE', response.data);
      }
      
      return response.data;
    } catch (error) {
      console.error('Errore durante il caricamento del profilo:', error);
      throw error;
    }
  },
  
  /**
   * Carica i film preferiti dell'utente
   */
  async loadFavoriteMovies() {
    try {
      const userId = store.getters['auth/userId'];
      const response = await api.get(`/users/${userId}/favorites`);
      
      // Aggiorna lo store con i film preferiti
      if (response.data && Array.isArray(response.data.movies)) {
        store.commit('movies/SET_FAVORITES', response.data.movies);
      }
      
      return response.data;
    } catch (error) {
      console.error('Errore durante il caricamento dei preferiti:', error);
      throw error;
    }
  },
  
  /**
   * Carica i film visti dall'utente
   */
  async loadWatchedMovies() {
    try {
      const userId = store.getters['auth/userId'];
      const response = await api.get(`/users/${userId}/watched`);
      
      // Aggiorna lo store con i film visti
      if (response.data && Array.isArray(response.data.movies)) {
        store.commit('movies/SET_WATCHED', response.data.movies);
      }
      
      return response.data;
    } catch (error) {
      console.error('Errore durante il caricamento dei film visti:', error);
      throw error;
    }
  },
  
  /**
   * Carica i film raccomandati per l'utente
   */
  async loadRecommendations() {
    try {
      const userId = store.getters['auth/userId'];
      const response = await api.get(`/users/${userId}/recommendations`);
      
      // Aggiorna lo store con i consigli personalizzati
      if (response.data && Array.isArray(response.data.movies)) {
        store.commit('movies/SET_RECOMMENDATIONS', response.data.movies);
      }
      
      return response.data;
    } catch (error) {
      console.error('Errore durante il caricamento delle raccomandazioni:', error);
      throw error;
    }
  },
  
  /**
   * Sincronizza le preferenze dell'utente con il backend
   */
  async syncUserPreferences(preferences) {
    try {
      const userId = store.getters['auth/userId'];
      const response = await api.put(`/users/${userId}/preferences`, preferences);
      
      // Aggiorna lo store con le preferenze aggiornate
      if (response.data) {
        store.commit('auth/UPDATE_PREFERENCES', response.data);
      }
      
      return response.data;
    } catch (error) {
      console.error('Errore durante la sincronizzazione delle preferenze:', error);
      throw error;
    }
  },
  
  /**
   * Sincronizza il profilo utente con il backend
   */
  async syncUserProfile(profileData) {
    try {
      const userId = store.getters['auth/userId'];
      const response = await api.put(`/users/${userId}/profile`, profileData);
      
      // Aggiorna lo store con i dati del profilo aggiornati
      if (response.data) {
        store.commit('auth/SET_USER_PROFILE', response.data);
      }
      
      return response.data;
    } catch (error) {
      console.error('Errore durante la sincronizzazione del profilo:', error);
      throw error;
    }
  },
  
  /**
   * Perform full data synchronization
   */
  async fullSync() {
    const isAuthenticated = store.getters['auth/isAuthenticated'];
    if (!isAuthenticated) return;
    
    try {
      // Sync favorites
      const favorites = store.getters['movies/favoriteMovies'];
      await this.syncFavorites(favorites);
      
      // Sync watched movies
      const watched = store.getters['movies/watchedMovies'];
      await this.syncWatchedMovies(watched);
      
      return true;
    } catch (error) {
      console.error('Error during full sync:', error);
      return false;
    }
  }
};

export default syncService; 