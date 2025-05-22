import apiService from '@/services/api';

const TOKEN_KEY = 'user_token';
const USER_KEY = 'user_data';

export default {
  namespaced: true,
  
  state: {
    token: localStorage.getItem(TOKEN_KEY) || null,
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
    loading: false,
    error: null
  },
  
  getters: {
    isAuthenticated: state => !!state.token,
    user: state => state.user,
    userName: state => state.user ? state.user.name : null,
    token: state => state.token,
    isLoading: state => state.loading,
    hasError: state => !!state.error,
    error: state => state.error
  },
  
  mutations: {
    SET_TOKEN(state, token) {
      state.token = token;
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    },
    
    SET_USER(state, user) {
      state.user = user;
      if (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
      } else {
        localStorage.removeItem(USER_KEY);
      }
    },
    
    SET_LOADING(state, isLoading) {
      state.loading = isLoading;
    },
    
    SET_ERROR(state, error) {
      state.error = error;
    },
    
    CLEAR_ERROR(state) {
      state.error = null;
    }
  },
  
  actions: {
    async login({ commit, dispatch }, credentials) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      
      try {
        const response = await apiService.login(credentials);
        const { token, user } = response.data;
        
        commit('SET_TOKEN', token);
        commit('SET_USER', user);
        
        return true;
      } catch (error) {
        console.error('Login error:', error);
        
        const errorMessage = error.response && error.response.data && error.response.data.message
          ? error.response.data.message
          : 'Failed to log in. Please check your credentials and try again.';
          
        commit('SET_ERROR', errorMessage);
        return false;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    async register({ commit }, userData) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      
      try {
        const response = await apiService.register(userData);
        const { token, user } = response.data;
        
        commit('SET_TOKEN', token);
        commit('SET_USER', user);
        
        return true;
      } catch (error) {
        console.error('Registration error:', error);
        
        const errorMessage = error.response && error.response.data && error.response.data.message
          ? error.response.data.message
          : 'Registration failed. Please try again.';
          
        commit('SET_ERROR', errorMessage);
        return false;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    async fetchCurrentUser({ commit, state }) {
      if (!state.token) return null;
      
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      
      try {
        const response = await apiService.getCurrentUser();
        commit('SET_USER', response.data);
        return response.data;
      } catch (error) {
        console.error('Error fetching user profile:', error);
        
        // If unauthorized, clear the token and user data
        if (error.response && error.response.status === 401) {
          commit('SET_TOKEN', null);
          commit('SET_USER', null);
        }
        
        return null;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    async updateProfile({ commit }, userData) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      
      try {
        const response = await apiService.updateProfile(userData);
        commit('SET_USER', response.data);
        return true;
      } catch (error) {
        console.error('Error updating profile:', error);
        
        const errorMessage = error.response && error.response.data && error.response.data.message
          ? error.response.data.message
          : 'Failed to update profile. Please try again.';
          
        commit('SET_ERROR', errorMessage);
        return false;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    async updatePassword({ commit }, passwordData) {
      commit('SET_LOADING', true);
      commit('CLEAR_ERROR');
      
      try {
        await apiService.updatePassword(passwordData);
        return true;
      } catch (error) {
        console.error('Error updating password:', error);
        
        const errorMessage = error.response && error.response.data && error.response.data.message
          ? error.response.data.message
          : 'Failed to update password. Please try again.';
          
        commit('SET_ERROR', errorMessage);
        return false;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    
    async logout({ commit }) {
      commit('SET_LOADING', true);
      
      try {
        // Try to call the logout endpoint but don't wait for it to complete
        apiService.logout().catch(error => console.error('Logout API error:', error));
      } finally {
        // Always clear user data, even if the API call fails
        commit('SET_TOKEN', null);
        commit('SET_USER', null);
        commit('SET_LOADING', false);
      }
    }
  }
}; 