import apiService from '@/services/api';

// API endpoints
const TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500';

export default {
  namespaced: true,
  
  state: {
    trendingMovies: [],
    searchResults: [],
    recommendations: [],
    loadingSearch: false,
    loadingTrending: false,
    loadingRecommendations: false,
    selectedMovie: null,
    watchedMovies: [],
    favoriteMovies: [],
    recentlyViewed: [],
    error: null
  },
  
  getters: {
    trendingMovies: state => state.trendingMovies,
    searchResults: state => state.searchResults,
    recommendations: state => state.recommendations,
    isLoadingSearch: state => state.loadingSearch,
    isLoadingTrending: state => state.loadingTrending,
    isLoadingRecommendations: state => state.loadingRecommendations,
    selectedMovie: state => state.selectedMovie,
    watchedMovies: state => state.watchedMovies,
    favoriteMovies: state => state.favoriteMovies,
    recentlyViewed: state => state.recentlyViewed,
    hasError: state => state.error !== null,
    errorMessage: state => state.error
  },
  
  mutations: {
    SET_TRENDING_MOVIES(state, movies) {
      state.trendingMovies = movies;
    },
    SET_SEARCH_RESULTS(state, results) {
      state.searchResults = results;
    },
    SET_RECOMMENDATIONS(state, recommendations) {
      state.recommendations = recommendations;
    },
    SET_LOADING_SEARCH(state, isLoading) {
      state.loadingSearch = isLoading;
    },
    SET_LOADING_TRENDING(state, isLoading) {
      state.loadingTrending = isLoading;
    },
    SET_LOADING_RECOMMENDATIONS(state, isLoading) {
      state.loadingRecommendations = isLoading;
    },
    SET_SELECTED_MOVIE(state, movie) {
      state.selectedMovie = movie;
    },
    SET_FAVORITES(state, movies) {
      state.favoriteMovies = movies;
    },
    SET_WATCHED_MOVIES(state, movies) {
      state.watchedMovies = movies;
    },
    ADD_TO_WATCHED(state, movie) {
      if (!state.watchedMovies.some(m => m.movie_id === movie.movie_id)) {
        state.watchedMovies.unshift(movie);
      }
    },
    TOGGLE_FAVORITE(state, movieId) {
      const index = state.favoriteMovies.findIndex(m => m.movie_id === movieId);
      if (index === -1) {
        const movie = state.trendingMovies.find(m => m.movie_id === movieId) || 
                     state.searchResults.find(m => m.movie_id === movieId) ||
                     state.recentlyViewed.find(m => m.movie_id === movieId);
        if (movie) state.favoriteMovies.push(movie);
      } else {
        state.favoriteMovies.splice(index, 1);
      }
    },
    ADD_TO_RECENTLY_VIEWED(state, movie) {
      // Remove if already exists
      const index = state.recentlyViewed.findIndex(m => m.movie_id === movie.movie_id);
      if (index !== -1) {
        state.recentlyViewed.splice(index, 1);
      }
      // Add to beginning of array
      state.recentlyViewed.unshift(movie);
      // Keep only last 10 items
      if (state.recentlyViewed.length > 10) {
        state.recentlyViewed = state.recentlyViewed.slice(0, 10);
      }
    },
    SET_ERROR(state, error) {
      state.error = error;
    },
    CLEAR_ERROR(state) {
      state.error = null;
    }
  },
  
  actions: {
    initialize({ dispatch }) {
      dispatch('fetchTrendingMovies');
      dispatch('loadUserFavorites');
      dispatch('loadWatchedMovies');
    },
    
    async searchMovies({ commit }, query) {
      if (!query.trim()) {
        commit('SET_SEARCH_RESULTS', []);
        return;
      }
      
      commit('SET_LOADING_SEARCH', true);
      commit('CLEAR_ERROR');
      
      try {
        const response = await apiService.searchMovies(query);
        commit('SET_SEARCH_RESULTS', response.data.movies || []);
      } catch (error) {
        console.error('Error searching movies:', error);
        commit('SET_ERROR', 'Failed to search movies. Please try again later.');
        commit('SET_SEARCH_RESULTS', []);
      } finally {
        commit('SET_LOADING_SEARCH', false);
      }
    },
    
    async fetchTrendingMovies({ commit }) {
      commit('SET_LOADING_TRENDING', true);
      commit('CLEAR_ERROR');
      
      try {
        const response = await apiService.getTrendingMovies();
        commit('SET_TRENDING_MOVIES', response.data.movies || []);
      } catch (error) {
        console.error('Error fetching trending movies:', error);
        commit('SET_ERROR', 'Failed to fetch trending movies. Please try again later.');
      } finally {
        commit('SET_LOADING_TRENDING', false);
      }
    },
    
    async getRecommendations({ commit, state }) {
      if (state.watchedMovies.length === 0) return;
      
      commit('SET_LOADING_RECOMMENDATIONS', true);
      commit('CLEAR_ERROR');
      
      try {
        // Get movie IDs from watched movies
        const movieIds = state.watchedMovies.map(movie => movie.movie_id);
        
        const response = await apiService.getRecommendations(movieIds);
        commit('SET_RECOMMENDATIONS', response.data.recommendations || []);
      } catch (error) {
        console.error('Error fetching recommendations:', error);
        commit('SET_ERROR', 'Failed to fetch recommendations. Please try again later.');
      } finally {
        commit('SET_LOADING_RECOMMENDATIONS', false);
      }
    },
    
    async getContentRecommendations({ commit }, content) {
      commit('SET_LOADING_RECOMMENDATIONS', true);
      commit('CLEAR_ERROR');
      
      try {
        const response = await apiService.getContentRecommendations(content);
        commit('SET_RECOMMENDATIONS', response.data.recommendations || []);
      } catch (error) {
        console.error('Error fetching content recommendations:', error);
        commit('SET_ERROR', 'Failed to fetch recommendations. Please try again later.');
      } finally {
        commit('SET_LOADING_RECOMMENDATIONS', false);
      }
    },
    
    async getMovieDetails({ commit }, movieId) {
      commit('CLEAR_ERROR');
      
      try {
        const response = await apiService.getMovieDetails(movieId);
        
        if (response.data) {
          commit('SET_SELECTED_MOVIE', response.data);
          commit('ADD_TO_RECENTLY_VIEWED', response.data);
        }
        return response.data;
      } catch (error) {
        console.error('Error fetching movie details:', error);
        commit('SET_ERROR', 'Failed to fetch movie details. Please try again later.');
        return null;
      }
    },
    
    async getMovieRecommendations({ commit }, movieId) {
      commit('SET_LOADING_RECOMMENDATIONS', true);
      commit('CLEAR_ERROR');
      
      try {
        const response = await apiService.getSimilarMovies(movieId);
        commit('SET_RECOMMENDATIONS', response.data.similar_movies || []);
      } catch (error) {
        console.error('Error fetching movie recommendations:', error);
        commit('SET_ERROR', 'Failed to fetch similar movies. Please try again later.');
      } finally {
        commit('SET_LOADING_RECOMMENDATIONS', false);
      }
    },
    
    async loadUserFavorites({ commit }) {
      commit('CLEAR_ERROR');
      
      try {
        const favorites = await apiService.getFavorites();
        // Just use favorites directly since our API service now returns the array
        commit('SET_FAVORITES', favorites); 
      } catch (error) {
        console.error('Error loading favorites:', error);
        commit('SET_ERROR', 'Failed to load favorite movies.');
      }
    },
    
    async loadWatchedMovies({ commit }) {
      commit('CLEAR_ERROR');
      
      try {
        const watched = await apiService.getWatchedMovies();
        // Just use watched directly since our API service now returns the array
        commit('SET_WATCHED_MOVIES', watched);
      } catch (error) {
        console.error('Error loading watched movies:', error);
        commit('SET_ERROR', 'Failed to load watched movies.');
      }
    },
    
    addToWatched({ commit, dispatch }, movie) {
      commit('ADD_TO_WATCHED', movie);
      
      // Try to sync with backend
      apiService.addWatched(movie.movie_id).catch(error => {
        console.error('Error syncing watched movie:', error);
      });
      
      // If we added a movie to watched, update recommendations
      dispatch('getRecommendations');
    },
    
    removeFromWatched({ commit, state }, movieId) {
      const index = state.watchedMovies.findIndex(m => m.movie_id === movieId);
      if (index !== -1) {
        commit('SET_WATCHED_MOVIES', [
          ...state.watchedMovies.slice(0, index),
          ...state.watchedMovies.slice(index + 1)
        ]);
        
        // Try to sync with backend
        apiService.removeWatched(movieId).catch(error => {
          console.error('Error removing watched movie:', error);
        });
      }
    },
    
    async toggleFavorite({ commit, state }, movieId) {
      commit('TOGGLE_FAVORITE', movieId);
      
      // Try to sync with backend
      try {
        const isFavorite = state.favoriteMovies.some(m => m.movie_id === movieId);
        
        if (isFavorite) {
          await apiService.addToFavorites(movieId);
        } else {
          await apiService.removeFromFavorites(movieId);
        }
      } catch (error) {
        console.error('Error syncing favorite:', error);
      }
    },
    
    viewMovieDetails({ commit }, movie) {
      commit('SET_SELECTED_MOVIE', movie);
      commit('ADD_TO_RECENTLY_VIEWED', movie);
    }
  }
}; 