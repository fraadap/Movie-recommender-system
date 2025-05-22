<template>
  <div class="profile-container">
    <div class="profile-header">
      <h1>Il tuo profilo</h1>
    </div>
    
    <div class="profile-content">
      <div class="card personal-info">
        <div class="card-header">
          <h2>Informazioni personali</h2>
          <button 
            class="btn-edit" 
            @click="isEditing = !isEditing"
            :class="{ 'active': isEditing }"
          >
            <i class="fas" :class="isEditing ? 'fa-times' : 'fa-edit'"></i>
            {{ isEditing ? 'Annulla' : 'Modifica' }}
          </button>
        </div>
        
        <div class="card-content">
          <!-- View mode -->
          <div v-if="!isEditing" class="info-display">
            <div class="info-row">
              <div class="info-label">Nome</div>
              <div class="info-value">{{ user.name }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">Email</div>
              <div class="info-value">{{ user.email }}</div>
            </div>
            <div class="info-row">
              <div class="info-label">Iscrizione</div>
              <div class="info-value">{{ formattedJoinDate }}</div>
            </div>
          </div>
          
          <!-- Edit mode -->
          <form v-else class="edit-form" @submit.prevent="updateProfile">
            <div class="form-group">
              <label for="name">Nome</label>
              <input 
                id="name" 
                v-model="formData.name" 
                type="text" 
                required
                placeholder="Il tuo nome"
              />
            </div>
            <div class="form-group">
              <label for="email">Email</label>
              <input 
                id="email" 
                v-model="formData.email" 
                type="email" 
                required
                placeholder="La tua email"
              />
            </div>
            <div class="form-actions">
              <button type="submit" class="btn-primary" :disabled="isSubmitting">Salva</button>
            </div>
          </form>
        </div>
      </div>
      
      <div class="card password-change">
        <div class="card-header">
          <h2>Cambia password</h2>
        </div>
        
        <div class="card-content">
          <form class="password-form" @submit.prevent="updatePassword">
            <div class="form-group">
              <label for="current-password">Password attuale</label>
              <div class="password-input">
                <input 
                  id="current-password" 
                  v-model="passwordForm.currentPassword" 
                  :type="showPassword ? 'text' : 'password'" 
                  required
                  placeholder="La tua password attuale"
                />
                <button 
                  type="button"
                  class="toggle-password"
                  @click="showPassword = !showPassword"
                >
                  <i class="fas" :class="showPassword ? 'fa-eye-slash' : 'fa-eye'"></i>
                </button>
              </div>
            </div>
            <div class="form-group">
              <label for="new-password">Nuova password</label>
              <div class="password-input">
                <input 
                  id="new-password" 
                  v-model="passwordForm.newPassword" 
                  :type="showPassword ? 'text' : 'password'" 
                  required
                  placeholder="La tua nuova password"
                />
              </div>
              <div class="password-strength" v-if="passwordForm.newPassword">
                <div 
                  class="strength-meter" 
                  :class="passwordStrengthClass"
                ></div>
                <div class="strength-text">{{ passwordStrengthText }}</div>
              </div>
            </div>
            <div class="form-group">
              <label for="confirm-password">Conferma password</label>
              <div class="password-input">
                <input 
                  id="confirm-password" 
                  v-model="passwordForm.confirmPassword" 
                  :type="showPassword ? 'text' : 'password'" 
                  required
                  placeholder="Conferma la nuova password"
                />
              </div>
              <div 
                v-if="passwordForm.confirmPassword && passwordForm.newPassword !== passwordForm.confirmPassword" 
                class="password-mismatch"
              >
                Le password non corrispondono
              </div>
            </div>
            <div class="form-actions">
              <button 
                type="submit" 
                class="btn-primary" 
                :disabled="isSubmitting || !isPasswordFormValid"
              >
                Aggiorna password
              </button>
            </div>
          </form>
        </div>
      </div>
      
      <div class="card preferences">
        <div class="card-header">
          <h2>Preferenze</h2>
        </div>
        
        <div class="card-content">
          <div class="preference-item">
            <div class="preference-info">
              <div class="preference-label">Modalità scura</div>
              <div class="preference-description">Cambia l'aspetto dell'interfaccia</div>
            </div>
            <div class="preference-control">
              <label class="toggle">
                <input 
                  type="checkbox" 
                  :checked="isDarkMode" 
                  @change="toggleDarkMode"
                />
                <span class="slider"></span>
              </label>
            </div>
          </div>
          
          <div class="preference-item">
            <div class="preference-info">
              <div class="preference-label">Notifiche email</div>
              <div class="preference-description">Ricevi aggiornamenti sui nuovi film</div>
            </div>
            <div class="preference-control">
              <label class="toggle">
                <input 
                  type="checkbox" 
                  v-model="preferences.emailNotifications" 
                  @change="updatePreferences"
                />
                <span class="slider"></span>
              </label>
            </div>
          </div>
          
          <div class="preference-item">
            <div class="preference-info">
              <div class="preference-label">Auto-raccomandazioni</div>
              <div class="preference-description">Raccomandiamo film in base a quelli che guardi</div>
            </div>
            <div class="preference-control">
              <label class="toggle">
                <input 
                  type="checkbox" 
                  v-model="preferences.autoRecommendations" 
                  @change="updatePreferences"
                />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card data-sync">
        <div class="card-header">
          <h2>Sincronizzazione dati</h2>
        </div>
        
        <div class="card-content">
          <p class="sync-description">
            Sincronizza i tuoi dati (preferiti, film visti) tra i tuoi dispositivi 
            o dopo aver importato dati.
          </p>
          
          <div class="sync-actions">
            <button 
              class="btn-primary full-width" 
              @click="syncData" 
              :disabled="isSyncing"
            >
              <i class="fas fa-sync" :class="{ 'fa-spin': isSyncing }"></i>
              {{ isSyncing ? 'Sincronizzazione in corso...' : 'Sincronizza dati' }}
            </button>
          </div>
          
          <div v-if="syncStatus" class="sync-status">
            <div class="status-item">
              <span class="status-label">Ultimo aggiornamento:</span>
              <span class="status-value">{{ syncStatus.lastSync || 'Mai' }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">Preferiti sincronizzati:</span>
              <span class="status-value">{{ syncStatus.favorites || 0 }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">Film visti sincronizzati:</span>
              <span class="status-value">{{ syncStatus.watched || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card danger-zone">
        <div class="card-header danger">
          <h2>Zona di pericolo</h2>
        </div>
        
        <div class="card-content">
          <p class="danger-description">
            Le seguenti azioni sono irreversibili. Assicurati di voler procedere.
          </p>
          
          <div class="danger-actions">
            <button 
              class="btn-danger" 
              @click="confirmDeleteAccount"
            >
              <i class="fas fa-trash-alt"></i>
              Elimina account
            </button>
          </div>
          
          <div v-if="showDeleteConfirm" class="delete-confirm">
            <p>Sei sicuro di voler eliminare il tuo account? Questa azione non può essere annullata.</p>
            <div class="confirm-actions">
              <button class="btn-outline" @click="showDeleteConfirm = false">Annulla</button>
              <button class="btn-danger" @click="deleteAccount">Conferma eliminazione</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import syncService from '@/services/syncService';

export default {
  name: 'Profile',
  
  setup() {
    const store = useStore();
    const router = useRouter();
    
    // State
    const isEditing = ref(false);
    const isSubmitting = ref(false);
    const showPassword = ref(false);
    const showDeleteConfirm = ref(false);
    const isSyncing = ref(false);
    const syncStatus = ref(null);
    
    // Form data
    const formData = reactive({
      name: '',
      email: ''
    });
    
    const passwordForm = reactive({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    });
    
    const preferences = reactive({
      emailNotifications: false,
      autoRecommendations: true
    });
    
    // Computed properties
    const user = computed(() => store.getters['auth/user'] || {});
    const isDarkMode = computed(() => store.getters['ui/isDarkMode']);
    
    const formattedJoinDate = computed(() => {
      if (!user.value || !user.value.created_at) return 'N/A';
      return new Date(user.value.created_at).toLocaleDateString('it-IT', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    });
    
    const passwordStrength = computed(() => {
      const password = passwordForm.newPassword;
      if (!password) return 0;
      
      let score = 0;
      
      // Length check
      if (password.length >= 8) score += 1;
      if (password.length >= 12) score += 1;
      
      // Complexity checks
      if (/[A-Z]/.test(password)) score += 1;
      if (/[a-z]/.test(password)) score += 1;
      if (/[0-9]/.test(password)) score += 1;
      if (/[^A-Za-z0-9]/.test(password)) score += 1;
      
      return Math.min(score, 5);
    });
    
    const passwordStrengthClass = computed(() => {
      const strength = passwordStrength.value;
      if (strength < 2) return 'weak';
      if (strength < 4) return 'medium';
      return 'strong';
    });
    
    const passwordStrengthText = computed(() => {
      const strength = passwordStrength.value;
      if (strength < 2) return 'Debole';
      if (strength < 4) return 'Media';
      return 'Forte';
    });
    
    const isPasswordFormValid = computed(() => {
      return (
        passwordForm.currentPassword &&
        passwordForm.newPassword &&
        passwordForm.confirmPassword &&
        passwordForm.newPassword === passwordForm.confirmPassword &&
        passwordStrength.value >= 3
      );
    });
    
    // Methods
    const loadUserData = () => {
      formData.name = user.value.name || '';
      formData.email = user.value.email || '';
    };
    
    const updateProfile = async () => {
      isSubmitting.value = true;
      
      try {
        const success = await store.dispatch('auth/updateProfile', {
          name: formData.name,
          email: formData.email
        });
        
        if (success) {
          isEditing.value = false;
        }
      } catch (error) {
        console.error('Error updating profile:', error);
      } finally {
        isSubmitting.value = false;
      }
    };
    
    const updatePassword = async () => {
      if (!isPasswordFormValid.value) return;
      
      isSubmitting.value = true;
      
      try {
        const success = await store.dispatch('auth/updatePassword', {
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword
        });
        
        if (success) {
          passwordForm.currentPassword = '';
          passwordForm.newPassword = '';
          passwordForm.confirmPassword = '';
        }
      } catch (error) {
        console.error('Error updating password:', error);
      } finally {
        isSubmitting.value = false;
      }
    };
    
    const toggleDarkMode = () => {
      store.dispatch('ui/toggleDarkMode');
    };
    
    const updatePreferences = () => {
      // Here you would usually sync preferences with backend
    };
    
    const syncData = async () => {
      isSyncing.value = true;
      
      try {
        await syncService.fullSync();
        
        // Update sync status
        syncStatus.value = {
          lastSync: new Date().toLocaleString('it-IT'),
          favorites: store.getters['movies/favoriteMovies'].length,
          watched: store.getters['movies/watchedMovies'].length
        };
      } catch (error) {
        console.error('Error syncing data:', error);
      } finally {
        isSyncing.value = false;
      }
    };
    
    const confirmDeleteAccount = () => {
      showDeleteConfirm.value = true;
    };
    
    const deleteAccount = async () => {
      // This would call a backend API to delete the account
      // For now, we'll just log out
      await store.dispatch('auth/logout');
      
      router.push('/register');
    };
    
    // Lifecycle hooks
    onMounted(() => {
      loadUserData();
      
      // Initialize sync status
      syncStatus.value = {
        lastSync: localStorage.getItem('lastSyncDate') || 'Mai',
        favorites: store.getters['movies/favoriteMovies'].length,
        watched: store.getters['movies/watchedMovies'].length
      };
    });
    
    return {
      isEditing,
      isSubmitting,
      showPassword,
      showDeleteConfirm,
      isSyncing,
      syncStatus,
      formData,
      passwordForm,
      preferences,
      user,
      isDarkMode,
      formattedJoinDate,
      passwordStrength,
      passwordStrengthClass,
      passwordStrengthText,
      isPasswordFormValid,
      updateProfile,
      updatePassword,
      toggleDarkMode,
      updatePreferences,
      syncData,
      confirmDeleteAccount,
      deleteAccount
    };
  }
};
</script>

<style scoped lang="scss">
.profile-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 30px 20px;
}

.profile-header {
  margin-bottom: 30px;
  
  h1 {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-color);
  }
}

.profile-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 25px;
}

.card {
  background-color: var(--card-background);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  
  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    h2 {
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--text-color);
      margin: 0;
    }
    
    &.danger {
      h2 {
        color: var(--error-color);
      }
    }
    
    .btn-edit {
      background: none;
      border: none;
      color: var(--primary-color);
      padding: 5px 10px;
      border-radius: 4px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 500;
      
      &:hover {
        background-color: rgba(0, 0, 0, 0.05);
      }
      
      &.active {
        color: var(--error-color);
      }
      
      i {
        font-size: 0.9rem;
      }
    }
  }
  
  .card-content {
    padding: 20px;
  }
}

.info-display {
  .info-row {
    margin-bottom: 15px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .info-label {
      font-size: 0.875rem;
      color: var(--text-secondary);
      margin-bottom: 5px;
    }
    
    .info-value {
      font-size: 1rem;
      color: var(--text-color);
    }
  }
}

.edit-form, .password-form {
  .form-group {
    margin-bottom: 20px;
    
    label {
      display: block;
      font-size: 0.875rem;
      color: var(--text-secondary);
      margin-bottom: 5px;
    }
    
    input {
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      background-color: var(--card-background);
      color: var(--text-color);
      font-size: 1rem;
      
      &:focus {
        outline: none;
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
      }
    }
  }
  
  .password-input {
    position: relative;
    
    input {
      padding-right: 40px;
    }
    
    .toggle-password {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: var(--text-secondary);
      cursor: pointer;
      
      &:hover {
        color: var(--text-color);
      }
    }
  }
  
  .password-strength {
    margin-top: 10px;
    
    .strength-meter {
      height: 5px;
      border-radius: 2px;
      background-color: #e0e0e0;
      position: relative;
      
      &::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        border-radius: 2px;
        transition: width 0.3s ease;
      }
      
      &.weak::before {
        width: 33%;
        background-color: #f44336;
      }
      
      &.medium::before {
        width: 66%;
        background-color: #ffc107;
      }
      
      &.strong::before {
        width: 100%;
        background-color: #4caf50;
      }
    }
    
    .strength-text {
      font-size: 0.8rem;
      margin-top: 5px;
      text-align: right;
    }
  }
  
  .password-mismatch {
    color: var(--error-color);
    font-size: 0.8rem;
    margin-top: 5px;
  }
  
  .form-actions {
    display: flex;
    justify-content: flex-end;
    
    button {
      padding: 10px 20px;
    }
  }
}

.preference-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  border-bottom: 1px solid var(--border-color);
  
  &:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }
  
  .preference-info {
    .preference-label {
      font-weight: 500;
      margin-bottom: 4px;
      color: var(--text-color);
    }
    
    .preference-description {
      font-size: 0.875rem;
      color: var(--text-secondary);
    }
  }
}

.toggle {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  
  input {
    opacity: 0;
    width: 0;
    height: 0;
    
    &:checked + .slider {
      background-color: var(--primary-color);
      
      &:before {
        transform: translateX(20px);
      }
    }
  }
  
  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    transition: 0.4s;
    border-radius: 24px;
    
    &:before {
      position: absolute;
      content: "";
      height: 20px;
      width: 20px;
      left: 2px;
      bottom: 2px;
      background-color: white;
      transition: 0.4s;
      border-radius: 50%;
    }
  }
}

.sync-description, .danger-description {
  margin-bottom: 20px;
  font-size: 0.95rem;
  color: var(--text-secondary);
}

.sync-actions, .danger-actions {
  margin-bottom: 20px;
}

.sync-status {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
  
  .status-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .status-label {
      color: var(--text-secondary);
    }
    
    .status-value {
      font-weight: 500;
      color: var(--text-color);
    }
  }
}

.delete-confirm {
  margin-top: 20px;
  padding: 15px;
  background-color: rgba(244, 67, 54, 0.08);
  border-radius: 4px;
  
  p {
    margin-bottom: 15px;
    color: var(--error-color);
  }
  
  .confirm-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
}

.btn-primary, .btn-danger, .btn-outline {
  padding: 10px 15px;
  border-radius: 4px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  
  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  i {
    font-size: 0.9rem;
  }
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
  
  &:hover:not(:disabled) {
    background-color: var(--primary-dark);
  }
}

.btn-danger {
  background-color: var(--error-color);
  color: white;
  
  &:hover {
    background-color: darken(#f44336, 10%);
  }
}

.btn-outline {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-color);
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.05);
  }
}

.full-width {
  width: 100%;
}

@media (max-width: 768px) {
  .profile-container {
    padding: 20px 15px;
  }
  
  .profile-header {
    margin-bottom: 20px;
    
    h1 {
      font-size: 1.5rem;
    }
  }
}
</style> 