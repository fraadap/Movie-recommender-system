<template>
  <aside class="sidebar" :class="{ 'is-open': isSidebarOpen, 'is-mobile': isMobile }">
    <div class="sidebar-header">
      <router-link to="/" class="logo">
        <i class="fas fa-film"></i>
        <span class="logo-text">MovieMatcher</span>
      </router-link>
      <button class="sidebar-toggle" @click="toggleSidebar">
        <i class="fas fa-times"></i>
      </button>
    </div>

    <div class="sidebar-content">
      <nav class="sidebar-nav">
        <h3 class="sidebar-section-title">Menu</h3>
        <ul class="sidebar-menu">
          <li>
            <router-link to="/" class="sidebar-link" exact-active-class="active">
              <i class="fas fa-home"></i>
              <span>Home</span>
            </router-link>
          </li>
          <li>
            <router-link to="/search" class="sidebar-link" active-class="active">
              <i class="fas fa-search"></i>
              <span>Cerca</span>
            </router-link>
          </li>
          <li v-if="isAuthenticated">
            <router-link to="/favorites" class="sidebar-link" active-class="active">
              <i class="fas fa-heart"></i>
              <span>Preferiti</span>
            </router-link>
          </li>
        </ul>

        <template v-if="isAuthenticated">
          <h3 class="sidebar-section-title">Account</h3>
          <ul class="sidebar-menu">
            <li>
              <router-link to="/profile" class="sidebar-link" active-class="active">
                <i class="fas fa-user"></i>
                <span>Profilo</span>
              </router-link>
            </li>
            <li>
              <a href="#" class="sidebar-link" @click.prevent="toggleDarkMode">
                <i class="fas" :class="isDarkMode ? 'fa-sun' : 'fa-moon'"></i>
                <span>{{ isDarkMode ? 'Modalità Chiara' : 'Modalità Scura' }}</span>
              </a>
            </li>
            <li>
              <a href="#" class="sidebar-link" @click.prevent="logout">
                <i class="fas fa-sign-out-alt"></i>
                <span>Logout</span>
              </a>
            </li>
          </ul>
        </template>
        <template v-else>
          <h3 class="sidebar-section-title">Account</h3>
          <ul class="sidebar-menu">
            <li>
              <router-link to="/login" class="sidebar-link" active-class="active">
                <i class="fas fa-sign-in-alt"></i>
                <span>Accedi</span>
              </router-link>
            </li>
            <li>
              <router-link to="/register" class="sidebar-link" active-class="active">
                <i class="fas fa-user-plus"></i>
                <span>Registrati</span>
              </router-link>
            </li>
          </ul>
        </template>
      </nav>
    </div>

    <div class="sidebar-footer">
      <p class="version">v1.0.0</p>
      <p class="copyright">&copy; {{ currentYear }} MovieMatcher</p>
    </div>
  </aside>
</template>

<script>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'Sidebar',
  setup() {
    const store = useStore()
    const router = useRouter()
    const currentYear = ref(new Date().getFullYear())
    
    const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
    const isSidebarOpen = computed(() => store.getters['ui/isSidebarOpen'])
    const isMobile = computed(() => store.getters['ui/isMobile'])
    const isDarkMode = computed(() => store.getters['ui/isDarkMode'])
    
    const toggleSidebar = () => {
      store.dispatch('ui/toggleSidebar')
    }
    
    const toggleDarkMode = () => {
      store.dispatch('ui/toggleDarkMode')
    }
    
    const logout = () => {
      store.dispatch('auth/logout')
      router.push('/login')
      // Close sidebar on mobile after logout
      if (isMobile.value) {
        store.commit('ui/SET_SIDEBAR_OPEN', false)
      }
    }
    
    return {
      isAuthenticated,
      isSidebarOpen,
      isMobile,
      isDarkMode,
      currentYear,
      toggleSidebar,
      toggleDarkMode,
      logout
    }
  }
}
</script>

<style lang="scss" scoped>
.sidebar {
  width: var(--sidebar-width);
  background-color: var(--bg-color-light);
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
  z-index: 100;
  transition: transform var(--transition-speed), background-color var(--transition-speed);
  
  &.is-mobile {
    transform: translateX(calc(-1 * var(--sidebar-width)));
    
    &.is-open {
      transform: translateX(0);
    }
  }
}

.sidebar-header {
  height: var(--header-height);
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  
  .logo {
    display: flex;
    align-items: center;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--primary-color);
    
    i {
      font-size: 1.4rem;
      margin-right: 10px;
    }
  }
  
  .sidebar-toggle {
    display: none;
    background: none;
    border: none;
    color: var(--text-color);
    font-size: 1.2rem;
    padding: 4px;
    
    @media (max-width: 767px) {
      display: block;
    }
    
    &:hover {
      background: none;
      color: var(--primary-color);
    }
  }
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}

.sidebar-section-title {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-color-light);
  padding: 0 16px;
  margin: 16px 0 8px;
}

.sidebar-menu {
  list-style: none;
  padding: 0;
  margin: 0 0 24px;
  
  li {
    margin: 2px 0;
  }
  
  .sidebar-link {
    display: flex;
    align-items: center;
    padding: 10px 16px;
    color: var(--text-color);
    transition: background-color 0.2s, color 0.2s;
    border-left: 3px solid transparent;
    
    i {
      width: 20px;
      margin-right: 8px;
      font-size: 1rem;
      text-align: center;
    }
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
      text-decoration: none;
    }
    
    &.active {
      color: var(--primary-color);
      background-color: rgba(var(--primary-color-rgb), 0.1);
      border-left-color: var(--primary-color);
      font-weight: 500;
    }
  }
}

.sidebar-footer {
  padding: 16px;
  font-size: 0.8rem;
  color: var(--text-color-light);
  text-align: center;
  border-top: 1px solid var(--border-color);
  
  .version {
    margin-bottom: 4px;
  }
}
</style> 