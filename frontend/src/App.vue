<template>
  <div id="app" :class="{ 'dark-mode': isDarkMode }">
    <sidebar />
    <div class="main-content" :class="{ 'sidebar-open': isSidebarOpen }">
      <header-bar />
      <main>
        <router-view />
      </main>
      <footer-bar />
    </div>
  </div>
</template>

<script>
import { computed, onMounted, provide } from 'vue'
import { useStore } from 'vuex'
import Sidebar from './components/Sidebar.vue'
import HeaderBar from './components/HeaderBar.vue'
import FooterBar from './components/FooterBar.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    HeaderBar,
    FooterBar,
  },
  setup() {
    const store = useStore()
    
    // Initialize UI settings from localStorage
    onMounted(() => {
      store.dispatch('ui/initializeSettings')
      
      // Check for mobile layout on load and resize
      const checkMobile = () => {
        store.commit('ui/SET_IS_MOBILE', window.innerWidth < 768)
      }
      
      checkMobile()
      window.addEventListener('resize', checkMobile)
      
      // Clean up event listener
      return () => {
        window.removeEventListener('resize', checkMobile)
      }
    })
    
    // Set up computed properties for UI state
    const isSidebarOpen = computed(() => store.getters['ui/isSidebarOpen'])
    const isDarkMode = computed(() => store.getters['ui/isDarkMode'])
    
    // Provide dark mode state to components
    provide('isDarkMode', isDarkMode)
    
    return {
      isSidebarOpen,
      isDarkMode
    }
  }
}
</script>

<style lang="scss">
:root {
  --primary-color: #e50914;
  --primary-hover: #f40612;
  --secondary-color: #221f1f;
  --accent-color: #f5f5f1;
  
  --bg-color: #f5f5f5;
  --bg-color-light: #ffffff;
  --bg-color-dark: #141414;
  
  --text-color: #221f1f;
  --text-color-light: #757575;
  --text-color-inverse: #f5f5f1;
  
  --border-color: #e0e0e0;
  --card-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  --sidebar-width: 250px;
  --header-height: 60px;
  --footer-height: 40px;
  
  --transition-speed: 0.3s;
}

.dark-mode {
  --bg-color: #141414;
  --bg-color-light: #221f1f;
  --bg-color-dark: #000000;
  
  --text-color: #f5f5f1;
  --text-color-light: #b3b3b3;
  --text-color-inverse: #221f1f;
  
  --border-color: #333333;
  --card-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Roboto', sans-serif;
  font-size: 16px;
  line-height: 1.5;
  color: var(--text-color);
  background-color: var(--bg-color);
}

#app {
  display: flex;
  min-height: 100vh;
  transition: background-color var(--transition-speed);
  background-color: var(--bg-color);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: var(--sidebar-width);
  transition: margin-left var(--transition-speed);
  
  &.sidebar-open {
    @media (max-width: 767px) {
      margin-left: var(--sidebar-width);
    }
  }
  
  @media (max-width: 767px) {
    margin-left: 0;
  }
}

main {
  flex: 1;
  padding: 20px;
  margin-top: var(--header-height);
  margin-bottom: var(--footer-height);
}

a {
  color: var(--primary-color);
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
}

button {
  cursor: pointer;
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: var(--primary-hover);
  }
  
  &:disabled {
    background-color: var(--text-color-light);
    cursor: not-allowed;
  }
}

.card {
  background-color: var(--bg-color-light);
  border-radius: 8px;
  box-shadow: var(--card-shadow);
  padding: 16px;
  margin-bottom: 16px;
  transition: background-color var(--transition-speed), box-shadow var(--transition-speed);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: 16px;
  color: var(--text-color);
}

/* Form elements */
input, textarea, select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background-color: var(--bg-color-light);
  color: var(--text-color);
  transition: border-color 0.2s, background-color var(--transition-speed);
  
  &:focus {
    outline: none;
    border-color: var(--primary-color);
  }
}

.form-group {
  margin-bottom: 16px;
  
  label {
    display: block;
    margin-bottom: 6px;
    font-size: 0.9rem;
    font-weight: 500;
  }
}

/* Loading spinner */
.loading-spinner {
  display: inline-block;
  width: 24px;
  height: 24px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style> 