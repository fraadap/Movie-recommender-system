<template>
  <header class="header-bar">
    <div class="header-left">
      <button class="toggle-sidebar" @click="toggleSidebar">
        <i class="fas fa-bars"></i>
      </button>
      <div class="breadcrumb">
        <span>{{ currentRouteName }}</span>
      </div>
    </div>
    
    <div class="search-bar" v-if="!isMobile">
      <i class="fas fa-search search-icon"></i>
      <input 
        type="text" 
        placeholder="Cerca un film..." 
        v-model="searchQuery" 
        @keyup.enter="handleSearch"
        @focus="isSearchFocused = true"
        @blur="isSearchFocused = false"
      >
      <button 
        class="search-clear" 
        v-if="searchQuery" 
        @click="clearSearch"
      >
        <i class="fas fa-times"></i>
      </button>
    </div>
    
    <div class="header-right">
      <div class="user-menu" v-if="isAuthenticated">
        <div class="user-avatar" @click="toggleUserDropdown">
          <span class="avatar-text">{{ userInitials }}</span>
        </div>
        
        <div class="user-dropdown" v-if="isUserDropdownOpen">
          <div class="user-info">
            <div class="user-name">{{ user.name }}</div>
            <div class="user-email">{{ user.email }}</div>
          </div>
          
          <ul class="dropdown-menu">
            <li>
              <router-link to="/profile" class="dropdown-item">
                <i class="fas fa-user"></i>
                <span>Profilo</span>
              </router-link>
            </li>
            <li>
              <a href="#" class="dropdown-item" @click.prevent="toggleDarkMode">
                <i class="fas" :class="isDarkMode ? 'fa-sun' : 'fa-moon'"></i>
                <span>{{ isDarkMode ? 'Modalità Chiara' : 'Modalità Scura' }}</span>
              </a>
            </li>
            <li class="divider"></li>
            <li>
              <a href="#" class="dropdown-item" @click.prevent="logout">
                <i class="fas fa-sign-out-alt"></i>
                <span>Logout</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
      
      <div class="auth-buttons" v-else>
        <router-link to="/login" class="btn btn-secondary btn-sm">Accedi</router-link>
        <router-link to="/register" class="btn btn-primary btn-sm">Registrati</router-link>
      </div>
    </div>
  </header>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'HeaderBar',
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()
    
    const searchQuery = ref('')
    const isSearchFocused = ref(false)
    const isUserDropdownOpen = ref(false)
    
    const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
    const user = computed(() => store.getters['auth/user'])
    const isMobile = computed(() => store.getters['ui/isMobile'])
    const isDarkMode = computed(() => store.getters['ui/isDarkMode'])
    
    const userInitials = computed(() => {
      if (!user.value || !user.value.name) return '?'
      return user.value.name
        .split(' ')
        .map(name => name.charAt(0).toUpperCase())
        .slice(0, 2)
        .join('')
    })
    
    const currentRouteName = computed(() => {
      const matched = route.matched[0]
      if (!matched) return 'Home'
      
      const name = matched.name
      if (typeof name === 'string') {
        return name.charAt(0).toUpperCase() + name.slice(1)
      } else if (route.path === '/') {
        return 'Home'
      } else {
        return route.path.split('/')[1].charAt(0).toUpperCase() + 
               route.path.split('/')[1].slice(1)
      }
    })
    
    const toggleSidebar = () => {
      store.dispatch('ui/toggleSidebar')
    }
    
    const toggleUserDropdown = () => {
      isUserDropdownOpen.value = !isUserDropdownOpen.value
    }
    
    const toggleDarkMode = () => {
      store.dispatch('ui/toggleDarkMode')
      isUserDropdownOpen.value = false
    }
    
    const handleSearch = () => {
      if (searchQuery.value.trim()) {
        router.push({ path: '/search', query: { q: searchQuery.value } })
      }
    }
    
    const clearSearch = () => {
      searchQuery.value = ''
    }
    
    const logout = () => {
      store.dispatch('auth/logout')
      router.push('/login')
      isUserDropdownOpen.value = false
    }
    
    const handleClickOutside = (event) => {
      const userMenu = document.querySelector('.user-menu')
      if (userMenu && !userMenu.contains(event.target) && isUserDropdownOpen.value) {
        isUserDropdownOpen.value = false
      }
    }
    
    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
    })
    
    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
    })
    
    return {
      searchQuery,
      isSearchFocused,
      isUserDropdownOpen,
      isAuthenticated,
      user,
      userInitials,
      isMobile,
      isDarkMode,
      currentRouteName,
      toggleSidebar,
      toggleUserDropdown,
      toggleDarkMode,
      handleSearch,
      clearSearch,
      logout
    }
  }
}
</script>

<style lang="scss" scoped>
.header-bar {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background-color: var(--bg-color-light);
  border-bottom: 1px solid var(--border-color);
  transition: background-color var(--transition-speed);
}

.header-left {
  display: flex;
  align-items: center;
  
  .toggle-sidebar {
    margin-right: 16px;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-color);
    background: none;
    border: none;
    font-size: 1.1rem;
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.2s, color 0.2s;
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
      color: var(--primary-color);
    }
  }
  
  .breadcrumb {
    font-weight: 500;
    font-size: 1.1rem;
    color: var(--text-color);
  }
}

.search-bar {
  position: relative;
  flex: 1;
  max-width: 400px;
  margin: 0 24px;
  
  .search-icon {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-color-light);
  }
  
  input {
    width: 100%;
    height: 36px;
    padding: 0 36px 0 36px;
    border-radius: 18px;
    border: 1px solid var(--border-color);
    background-color: var(--bg-color);
    color: var(--text-color);
    transition: border-color 0.2s, box-shadow 0.2s;
    
    &:focus {
      outline: none;
      border-color: var(--primary-color);
      box-shadow: 0 0 0 3px rgba(var(--primary-color-rgb), 0.2);
    }
    
    &::placeholder {
      color: var(--text-color-light);
    }
  }
  
  .search-clear {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: var(--text-color-light);
    cursor: pointer;
    
    &:hover {
      color: var(--text-color);
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
}

.user-menu {
  position: relative;
  
  .user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background-color: var(--primary-color);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background-color 0.2s;
    
    &:hover {
      background-color: var(--primary-color-dark);
    }
    
    .avatar-text {
      font-weight: 600;
      font-size: 0.9rem;
    }
  }
  
  .user-dropdown {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 240px;
    background-color: var(--bg-color-light);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 10;
    overflow: hidden;
    
    .user-info {
      padding: 16px;
      border-bottom: 1px solid var(--border-color);
      
      .user-name {
        font-weight: 500;
        margin-bottom: 4px;
        color: var(--text-color);
      }
      
      .user-email {
        font-size: 0.85rem;
        color: var(--text-color-light);
      }
    }
    
    .dropdown-menu {
      list-style: none;
      padding: 8px 0;
      margin: 0;
      
      .divider {
        height: 1px;
        background-color: var(--border-color);
        margin: 4px 0;
      }
      
      .dropdown-item {
        display: flex;
        align-items: center;
        padding: 8px 16px;
        color: var(--text-color);
        transition: background-color 0.2s;
        
        i {
          width: 20px;
          margin-right: 8px;
          font-size: 0.9rem;
        }
        
        &:hover {
          background-color: rgba(0, 0, 0, 0.05);
          text-decoration: none;
        }
      }
    }
  }
}

.auth-buttons {
  display: flex;
  gap: 8px;
  
  .btn {
    padding: 4px 12px;
    font-size: 0.85rem;
  }
}

@media (max-width: 767px) {
  .header-bar {
    padding: 0 12px;
  }
  
  .search-bar {
    display: none;
  }
  
  .header-left .breadcrumb {
    font-size: 1rem;
  }
  
  .auth-buttons {
    .btn {
      padding: 4px 8px;
      font-size: 0.8rem;
    }
  }
}
</style> 