<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h1>Accedi</h1>
          <p>Bentornato su FilmMind!</p>
        </div>
        
        <div v-if="error" class="auth-error">
          {{ error }}
        </div>
        
        <form @submit.prevent="handleLogin" class="auth-form">
          <div class="form-group">
            <label for="email">Email</label>
            <input 
              type="email" 
              id="email" 
              v-model="email" 
              required 
              placeholder="La tua email"
            >
          </div>
          
          <div class="form-group">
            <label for="password">Password</label>
            <div class="password-input">
              <input 
                :type="showPassword ? 'text' : 'password'" 
                id="password" 
                v-model="password" 
                required 
                placeholder="La tua password"
              >
              <button 
                type="button" 
                class="toggle-password" 
                @click="togglePassword"
              >
                {{ showPassword ? 'Nascondi' : 'Mostra' }}
              </button>
            </div>
          </div>
          
          <div class="form-footer">
            <button 
              type="submit" 
              class="btn-primary" 
              :disabled="loading"
            >
              <span v-if="loading" class="spinner-small"></span>
              <span v-else>Accedi</span>
            </button>
          </div>
        </form>
        
        <div class="auth-alt">
          <p>Non hai un account? <router-link to="/register">Registrati</router-link></p>
        </div>
        
        <div class="demo-notice">
          <p>👉 Per testare l'app, usa:</p>
          <p class="credentials">Email: <code>demo@example.com</code></p>
          <p class="credentials">Password: <code>password</code></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';

export default {
  name: 'LoginView',
  setup() {
    const store = useStore();
    const router = useRouter();
    
    // State
    const email = ref('');
    const password = ref('');
    const showPassword = ref(false);
    
    // Computed
    const loading = computed(() => store.getters['auth/loading']);
    const error = computed(() => store.getters['auth/error']);
    
    // Methods
    const handleLogin = async () => {
      const success = await store.dispatch('auth/login', {
        email: email.value,
        password: password.value
      });
      
      if (success) {
        router.push('/');
      }
    };
    
    const togglePassword = () => {
      showPassword.value = !showPassword.value;
    };
    
    // Auto-fill demo credentials in development mode
    if (process.env.NODE_ENV === 'development') {
      email.value = 'demo@example.com';
      password.value = 'password';
    }
    
    return {
      email,
      password,
      showPassword,
      loading,
      error,
      handleLogin,
      togglePassword
    };
  }
};
</script>

<style scoped lang="scss">
.auth-page {
  min-height: calc(100vh - var(--header-height));
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.auth-container {
  width: 100%;
  max-width: 420px;
}

.auth-card {
  background-color: var(--card-background);
  border-radius: 10px;
  padding: 30px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.auth-header {
  text-align: center;
  margin-bottom: 30px;
  
  h1 {
    font-size: 2rem;
    margin-bottom: 10px;
  }
  
  p {
    color: rgba(255, 255, 255, 0.7);
  }
}

.auth-error {
  background-color: rgba(255, 82, 82, 0.1);
  border: 1px solid rgba(255, 82, 82, 0.5);
  color: #ff5252;
  padding: 12px;
  border-radius: 5px;
  margin-bottom: 20px;
  font-size: 0.9rem;
}

.auth-form {
  .form-group {
    margin-bottom: 25px;
    
    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
    }
    
    input {
      width: 100%;
      padding: 12px 15px;
      background-color: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 5px;
      color: var(--text-color);
      font-size: 1rem;
      transition: border-color 0.3s;
      
      &:focus {
        outline: none;
        border-color: var(--primary-color);
      }
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.4);
      }
    }
    
    .password-input {
      position: relative;
      
      input {
        padding-right: 100px;
      }
      
      .toggle-password {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        color: var(--primary-color);
        cursor: pointer;
        padding: 5px;
        font-size: 0.8rem;
      }
    }
  }
  
  .form-footer {
    margin-top: 30px;
    
    .btn-primary {
      display: block;
      width: 100%;
      padding: 14px;
      background-color: var(--primary-color);
      color: white;
      border: none;
      border-radius: 5px;
      font-size: 1rem;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 0.3s;
      
      &:hover {
        background-color: var(--accent-color);
      }
      
      &:disabled {
        background-color: rgba(103, 58, 183, 0.5);
        cursor: not-allowed;
      }
    }
  }
}

.auth-alt {
  margin-top: 25px;
  text-align: center;
  color: rgba(255, 255, 255, 0.7);
  
  a {
    color: var(--primary-color);
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
}

.demo-notice {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
  
  p {
    margin-bottom: 5px;
  }
  
  .credentials {
    margin-left: 10px;
    
    code {
      background-color: rgba(255, 255, 255, 0.1);
      padding: 2px 5px;
      border-radius: 3px;
      font-family: monospace;
    }
  }
}

.spinner-small {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style> 