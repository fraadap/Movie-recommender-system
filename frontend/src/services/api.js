import axios from 'axios';
import store from '@/store';

// Create axios instance with base URL from environment
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_GATEWAY_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add interceptor to include auth token in requests
apiClient.interceptors.request.use(config => {
  const token = store.getters['auth/token'];
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// Add response interceptor to handle common errors
apiClient.interceptors.response.use(
  response => response,
  error => {
    // Handle token expiration
    if (error.response && error.response.status === 401) {
      store.dispatch('auth/logout');
    }
    
    // Log the error, but don't dispatch UI notifications
    if (error.response && error.response.data && error.response.data.message) {
      console.error('API Error:', error.response.data.message);
    } else if (error.message) {
      console.error('Connection Error:', error.message);
    } else {
      console.error('API Error:', error);
    }
    
    return Promise.reject(error);
  }
);

// ===== MOVIE APIS =====

/**
 * Search for movies
 * @param {string} query - Search query
 * @param {number} limit - Number of results to return (optional)
 * @returns {Promise} - Promise with search results
 */
export const searchMovies = async (query, limit = 10) => {
  try {
    const response = await apiClient.post('/search', {
      query,
      top_k: limit
    });
    
    // Based on search_lambda_router.py, the response is directly an array of movies
    if (!response.data || !Array.isArray(response.data)) {
      console.warn('Unexpected response format from search API');
      return [];
    }
    
    return response.data;
  } catch (error) {
    console.error('Error searching movies:', error);
    throw error;
  }
};

/**
 * Get movie recommendations
 * @param {number} limit - Number of results to return (optional)
 * @param {string} userId - User ID (optional)
 * @returns {Promise} - Promise with recommendations
 */
export const getRecommendations = async (limit = 10, userId = null) => {
  try {
    const payload = {
      top_k: limit
    };
    
    if (userId) {
      payload.user_id = userId;
    }
    
    const response = await apiClient.post('/recommend', payload);
    
    // Based on search_lambda_router.py, the response is directly an array of movies
    if (!response.data || !Array.isArray(response.data)) {
      console.warn('Unexpected response format from recommendations API');
      return [];
    }
    
    return response.data;
  } catch (error) {
    console.error('Error getting recommendations:', error);
    throw error;
  }
};

/**
 * Get movie details
 * @param {string|array} movieIds - Movie ID or array of movie IDs
 * @returns {Promise} - Promise with movie details
 */
export const getMovieDetails = async (movieIds) => {
  try {
    // Convert single ID to array
    const ids = Array.isArray(movieIds) ? movieIds : [movieIds];
    
    const response = await apiClient.post('/content', {
      movie_ids: ids,
      top_k: ids.length
    });
    
    // Based on search_lambda_router.py, the response is directly an array of movies
    if (!response.data || !Array.isArray(response.data)) {
      console.warn('Unexpected response format from content API');
      return Array.isArray(movieIds) ? [] : null;
    }
    
    // If only one movie was requested, return just that movie
    if (!Array.isArray(movieIds) && response.data.length > 0) {
      return response.data[0];
    }
    
    return response.data;
  } catch (error) {
    console.error('Error getting movie details:', error);
    throw error;
  }
};

/**
 * Get similar movies
 * @param {string} movieId - Movie ID
 * @param {number} limit - Number of results to return (optional)
 * @returns {Promise} - Promise with similar movies
 */
export const getSimilarMovies = async (movieId, limit = 10) => {
  try {
    const response = await apiClient.post('/collaborative', {
      movie_id: movieId,
      top_k: limit
    });
    
    // Based on search_lambda_router.py, the response is directly an array of movies
    if (!response.data || !Array.isArray(response.data)) {
      console.warn('Unexpected response format from collaborative API');
      return [];
    }
    
    return response.data;
  } catch (error) {
    console.error('Error getting similar movies:', error);
    throw error;
  }
};

// ===== AUTH APIS =====

/**
 * Login user
 * @param {Object} credentials - User credentials
 * @param {string} credentials.email - User email
 * @param {string} credentials.password - User password
 * @returns {Promise} - Promise with user data and token
 */
export const login = async (credentials) => {
  try {
    const response = await apiClient.post('/auth/login', credentials);
    return response.data;
  } catch (error) {
    console.error('Error logging in:', error);
    throw error;
  }
};

/**
 * Register user
 * @param {Object} userData - User data
 * @param {string} userData.name - User name
 * @param {string} userData.email - User email
 * @param {string} userData.password - User password
 * @returns {Promise} - Promise with user data and token
 */
export const register = async (userData) => {
  try {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  } catch (error) {
    console.error('Error registering:', error);
    throw error;
  }
};

/**
 * Update user profile
 * @param {Object} userData - User data to update
 * @returns {Promise} - Promise with updated user data
 */
export const updateProfile = async (userData) => {
  try {
    const response = await apiClient.put('/auth/profile', userData);
    return response.data;
  } catch (error) {
    console.error('Error updating profile:', error);
    throw error;
  }
};

/**
 * Change user password
 * @param {Object} passwordData - Password data
 * @param {string} passwordData.current_password - Current password
 * @param {string} passwordData.new_password - New password
 * @returns {Promise}
 */
export const changePassword = async (passwordData) => {
  try {
    const response = await apiClient.put('/auth/password', passwordData);
    return response.data;
  } catch (error) {
    console.error('Error changing password:', error);
    throw error;
  }
};

// ===== USER DATA APIS =====

/**
 * Get user favorites
 * @returns {Promise} - Promise with user favorites
 */
export const getFavorites = async () => {
  try {
    const response = await apiClient.get('/user-data/favorites');
    
    // Ensure response data is in expected format
    if (!response.data || !response.data.favorites || !Array.isArray(response.data.favorites)) {
      console.warn('Unexpected response format from favorites API');
      return [];
    }
    
    return response.data.favorites;
  } catch (error) {
    console.error('Error getting favorites:', error);
    throw error;
  }
};

/**
 * Add movie to favorites
 * @param {string} movieId - Movie ID
 * @returns {Promise} - Promise with updated favorites
 */
export const addFavorite = async (movieId) => {
  try {
    const response = await apiClient.post(`/user-data/favorites/${movieId}`);
    return response.data;
  } catch (error) {
    console.error('Error adding favorite:', error);
    throw error;
  }
};

/**
 * Remove movie from favorites
 * @param {string} movieId - Movie ID
 * @returns {Promise} - Promise with updated favorites
 */
export const removeFavorite = async (movieId) => {
  try {
    const response = await apiClient.delete(`/user-data/favorites/${movieId}`);
    return response.data;
  } catch (error) {
    console.error('Error removing favorite:', error);
    throw error;
  }
};

/**
 * Toggle movie favorite status
 * @param {string} movieId - Movie ID
 * @returns {Promise} - Promise with updated favorite status
 */
export const toggleFavorite = async (movieId) => {
  try {
    const response = await apiClient.post(`/user-data/favorites/toggle`, { 
      movie_id: movieId 
    });
    
    // The response from MovieUserDataFunction.py includes isFavorite flag
    if (response.data && typeof response.data.isFavorite === 'boolean') {
      return {
        isFavorite: response.data.isFavorite,
        message: response.data.message
      };
    }
    
    return response.data;
  } catch (error) {
    console.error('Error toggling favorite:', error);
    throw error;
  }
};

/**
 * Get user watched movies
 * @returns {Promise} - Promise with user watched movies
 */
export const getWatchedMovies = async () => {
  try {
    const response = await apiClient.get('/user-data/watched');
    
    // Ensure response data is in expected format
    if (!response.data || !response.data.watched || !Array.isArray(response.data.watched)) {
      console.warn('Unexpected response format from watched API');
      return [];
    }
    
    return response.data.watched;
  } catch (error) {
    console.error('Error getting watched movies:', error);
    throw error;
  }
};

/**
 * Add movie to watched
 * @param {string} movieId - Movie ID
 * @returns {Promise} - Promise with updated watched
 */
export const addWatched = async (movieId) => {
  try {
    const response = await apiClient.post(`/user-data/watched/${movieId}`);
    return response.data;
  } catch (error) {
    console.error('Error adding watched movie:', error);
    throw error;
  }
};

/**
 * Remove movie from watched
 * @param {string} movieId - Movie ID
 * @returns {Promise} - Promise with updated watched
 */
export const removeWatched = async (movieId) => {
  try {
    const response = await apiClient.delete(`/user-data/watched/${movieId}`);
    return response.data;
  } catch (error) {
    console.error('Error removing watched movie:', error);
    throw error;
  }
};

// ===== USER PREFERENCES APIS =====

/**
 * Get user preferences
 * @returns {Promise} - Promise with user preferences
 */
export const getUserPreferences = async () => {
  try {
    const response = await apiClient.get('/user/preferences');
    return response.data;
  } catch (error) {
    console.error('Error getting user preferences:', error);
    throw error;
  }
};

/**
 * Update user preferences
 * @param {Object} preferences - User preferences
 * @returns {Promise} - Promise with updated preferences
 */
export const updateUserPreferences = async (preferences) => {
  try {
    const response = await apiClient.put('/user/preferences', preferences);
    return response.data;
  } catch (error) {
    console.error('Error updating user preferences:', error);
    throw error;
  }
};

/**
 * Get user activity
 * @returns {Promise} - Promise with user activity
 */
export const getUserActivity = async () => {
  try {
    const response = await apiClient.get('/user/activity');
    return response.data;
  } catch (error) {
    console.error('Error getting user activity:', error);
    throw error;
  }
};

/**
 * Delete user account
 * @param {Object} confirmationData - Confirmation data 
 * @param {string} confirmationData.password - Current password
 * @returns {Promise}
 */
export const deleteUserAccount = async (confirmationData) => {
  try {
    const response = await apiClient.delete('/user/account', {
      data: confirmationData
    });
    return response.data;
  } catch (error) {
    console.error('Error deleting account:', error);
    throw error;
  }
};

export default {
  searchMovies,
  getRecommendations,
  getMovieDetails,
  getSimilarMovies,
  login,
  register,
  updateProfile,
  changePassword,
  getFavorites,
  toggleFavorite,
  getWatchedMovies,
  addWatched,
  removeWatched,
  getUserPreferences,
  updateUserPreferences,
  getUserActivity,
  deleteUserAccount
};