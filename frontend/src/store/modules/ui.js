const DARK_MODE_KEY = 'dark_mode';

const defaultState = {
  isSidebarOpen: false,
  isMobile: window.innerWidth < 768,
  isDarkMode: false,
  // notifications: [] Removed notifications state
};

const getters = {
  isSidebarOpen: state => state.isSidebarOpen,
  isMobile: state => state.isMobile,
  isDarkMode: state => state.isDarkMode,
  // notifications: state => state.notifications Removed notifications getter
};

const actions = {
  // Toggle sidebar visibility
  toggleSidebar({ commit, state }) {
    commit('SET_SIDEBAR_OPEN', !state.isSidebarOpen);
  },
  
  // Toggle dark/light mode
  toggleDarkMode({ commit, state }) {
    const newMode = !state.isDarkMode;
    commit('SET_DARK_MODE', newMode);
    localStorage.setItem(DARK_MODE_KEY, JSON.stringify(newMode));
  },
  
  // Initialize UI settings from localStorage
  initializeSettings({ commit }) {
    // Load dark mode from localStorage
    const storedDarkMode = localStorage.getItem(DARK_MODE_KEY);
    if (storedDarkMode !== null) {
      commit('SET_DARK_MODE', JSON.parse(storedDarkMode));
    }
  },
  
  closeSidebar({ commit }) {
    commit('SET_SIDEBAR_OPEN', false);
  }
};

const mutations = {
  SET_SIDEBAR_OPEN(state, isOpen) {
    state.isSidebarOpen = isOpen;
  },
  SET_IS_MOBILE(state, isMobile) {
    state.isMobile = isMobile;
    // Optionally close sidebar on mobile transition
    if (isMobile && state.isSidebarOpen) {
      state.isSidebarOpen = false;
    }
  },
  SET_DARK_MODE(state, isDark) {
    state.isDarkMode = isDark;
    if (isDark) {
      document.documentElement.classList.add('dark-mode');
    } else {
      document.documentElement.classList.remove('dark-mode');
    }
  },
  // Removed ADD_NOTIFICATION and REMOVE_NOTIFICATION mutations
};

export default {
  namespaced: true,
  state: defaultState,
  getters,
  actions,
  mutations
}; 