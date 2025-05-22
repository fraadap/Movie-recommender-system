<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-header">
          <h1>Registrati</h1>
          <p>Unisciti a FilmMind per scoprire film personalizzati!</p>
        </div>
        
        <div v-if="error" class="auth-error">
          {{ error }}
        </div>
        
        <form @submit.prevent="handleRegister" class="auth-form">
          <div class="form-group">
            <label for="name">Nome</label>
            <input 
              type="text" 
              id="name" 
              v-model="name" 
              required 
              placeholder="Il tuo nome"
            >
          </div>
          
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
                placeholder="Scegli una password"
                minlength="8"
              >
              <button 
                type="button" 
                class="toggle-password" 
                @click="togglePassword"
              >
                {{ showPassword ? 'Nascondi' : 'Mostra' }}
              </button>
            </div>
            <div class="password-strength" v-if="password">
              <div class="strength-bar" :class="passwordStrengthClass"></div>
              <span>{{ passwordStrengthText }}</span>
            </div>
          </div>
          
          <div class="form-group">
            <label for="confirmPassword">Conferma Password</label>
            <input 
              type="password" 
              id="confirmPassword" 
              v-model="confirmPassword" 
              required 
              placeholder="Ripeti la password"
            >
            <div v-if="passwordMismatch" class="input-error">
              Le password non corrispondono
            </div>
          </div>
          
          <div class="form-group checkbox">
            <input 
              type="checkbox" 
              id="terms" 
              v-model="acceptTerms" 
              required
            >
            <label for="terms">
              Ho letto e accetto i <a href="#" @click.prevent="showTerms">Termini di Servizio</a> e l'<a href="#" @click.prevent="showPrivacy">Informativa sulla Privacy</a>
            </label>
          </div>
          
          <div class="form-footer">
            <button 
              type="submit" 
              class="btn-primary" 
              :disabled="loading || passwordMismatch || !isFormValid"
            >
              <span v-if="loading" class="spinner-small"></span>
              <span v-else>Registrati</span>
            </button>
          </div>
        </form>
        
        <div class="auth-alt">
          <p>Hai già un account? <router-link to="/login">Accedi</router-link></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';

export default {
  name: 'RegisterView',
  setup() {
    const store = useStore();
    const router = useRouter();
    
    // State
    const name = ref('');
    const email = ref('');
    const password = ref('');
    const confirmPassword = ref('');
    const showPassword = ref(false);
    const acceptTerms = ref(false);
    
    // Computed
    const loading = computed(() => store.getters['auth/loading']);
    const error = computed(() => store.getters['auth/error']);
    
    const passwordMismatch = computed(() => {
      return confirmPassword.value && password.value !== confirmPassword.value;
    });
    
    const isFormValid = computed(() => {
      return name.value && 
             email.value && 
             password.value && 
             password.value === confirmPassword.value &&
             password.value.length >= 8 &&
             acceptTerms.value;
    });
    
    const passwordStrength = computed(() => {
      if (!password.value) return 0;
      
      let strength = 0;
      
      // Length check
      if (password.value.length >= 8) strength += 1;
      if (password.value.length >= 12) strength += 1;
      
      // Complexity checks
      if (/[A-Z]/.test(password.value)) strength += 1;
      if (/[a-z]/.test(password.value)) strength += 1;
      if (/[0-9]/.test(password.value)) strength += 1;
      if (/[^A-Za-z0-9]/.test(password.value)) strength += 1;
      
      return Math.min(strength, 5);
    });
    
    const passwordStrengthClass = computed(() => {
      const strengthMap = {
        0: 'very-weak',
        1: 'weak',
        2: 'medium',
        3: 'good',
        4: 'strong',
        5: 'very-strong'
      };
      
      return strengthMap[passwordStrength.value];
    });
    
    const passwordStrengthText = computed(() => {
      const strengthMap = {
        0: 'Molto debole',
        1: 'Debole',
        2: 'Media',
        3: 'Buona',
        4: 'Forte',
        5: 'Molto forte'
      };
      
      return strengthMap[passwordStrength.value];
    });
    
    // Methods
    const handleRegister = async () => {
      if (!isFormValid.value) return;
      
      const success = await store.dispatch('auth/register', {
        name: name.value,
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
    
    const showTerms = () => {
      // In a real app, you would show a modal with terms of service
      alert('Termini di Servizio (simulati per demo)');
    };
    
    const showPrivacy = () => {
      // In a real app, you would show a modal with privacy policy
      alert('Informativa sulla Privacy (simulata per demo)');
    };
    
    return {
      name,
      email,
      password,
      confirmPassword,
      showPassword,
      acceptTerms,
      loading,
      error,
      passwordMismatch,
      isFormValid,
      passwordStrengthClass,
      passwordStrengthText,
      handleRegister,
      togglePassword,
      showTerms,
      showPrivacy
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
    
    .password-strength {
      margin-top: 10px;
      font-size: 0.8rem;
      
      .strength-bar {
        height: 4px;
        border-radius: 2px;
        margin-bottom: 5px;
        
        &.very-weak {
          width: 20%;
          background-color: #ff1744;
        }
        
        &.weak {
          width: 40%;
          background-color: #ff9100;
        }
        
        &.medium {
          width: 60%;
          background-color: #ffea00;
        }
        
        &.good {
          width: 80%;
          background-color: #00e676;
        }
        
        &.very-strong {
          width: 100%;
          background-color: #00b0ff;
        }
      }
      
      span {
        color: rgba(255, 255, 255, 0.7);
      }
    }
    
    .input-error {
      color: #ff5252;
      font-size: 0.8rem;
      margin-top: 5px;
    }
    
    &.checkbox {
      display: flex;
      align-items: flex-start;
      
      input {
        width: auto;
        margin-top: 3px;
        margin-right: 10px;
      }
      
      label {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.7);
        
        a {
          color: var(--primary-color);
          text-decoration: none;
          
          &:hover {
            text-decoration: underline;
          }
        }
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