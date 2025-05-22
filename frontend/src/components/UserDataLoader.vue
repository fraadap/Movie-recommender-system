<template>
  <!-- Componente invisibile che gestisce il caricamento dei dati utente -->
  <div class="user-data-loader"></div>
</template>

<script>
import { onMounted, onUnmounted, watch } from 'vue';
import { useStore } from 'vuex';
import { useRouter, useRoute } from 'vue-router';
import syncService from '@/services/syncService';

export default {
  name: 'UserDataLoader',
  
  setup() {
    const store = useStore();
    const router = useRouter();
    const route = useRoute();
    
    // Intervallo per la sincronizzazione periodica
    let syncInterval = null;
    
    /**
     * Carica i dati utente dal backend
     */
    const loadUserData = async () => {
      const isAuthenticated = store.getters['auth/isAuthenticated'];
      const lastSync = localStorage.getItem('lastSyncDate');
      
      if (isAuthenticated) {
        try {
          // Se non ci sono dati sincronizzati recentemente, carica i dati
          if (!lastSync || Date.now() - new Date(lastSync).getTime() > 1000 * 60 * 60) { // 1 ora
            await syncService.loadUserData();
            
            // Aggiorna la data ultimo aggiornamento
            localStorage.setItem('lastSyncDate', new Date().toISOString());
          }
        } catch (error) {
          console.error('Errore durante il caricamento dei dati utente:', error);
          
          // Gestione errori gravi
          if (error.status === 401) {
            store.dispatch('auth/logout');
            router.push('/login');
          }
        }
      }
    };
    
    /**
     * Configura la sincronizzazione periodica
     */
    const setupPeriodicSync = () => {
      // Pulisci eventuali intervalli esistenti
      if (syncInterval) {
        clearInterval(syncInterval);
      }
      
      // Se l'utente è autenticato, imposta la sincronizzazione periodica
      if (store.getters['auth/isAuthenticated']) {
        // Sincronizza dati ogni 30 minuti se l'utente è attivo
        syncInterval = setInterval(() => {
          // Controlla se l'utente è ancora autenticato
          if (store.getters['auth/isAuthenticated']) {
            syncService.loadUserData().catch(err => {
              console.error('Errore sincronizzazione periodica:', err);
            });
          } else {
            // Se l'utente non è più autenticato, rimuovi l'intervallo
            clearInterval(syncInterval);
          }
        }, 1000 * 60 * 30); // 30 minuti
      }
    };
    
    // Osserva i cambiamenti dello stato di autenticazione
    watch(
      () => store.getters['auth/isAuthenticated'],
      (isAuthenticated) => {
        if (isAuthenticated) {
          loadUserData();
          setupPeriodicSync();
        } else {
          // Pulizia quando l'utente si disconnette
          if (syncInterval) {
            clearInterval(syncInterval);
            syncInterval = null;
          }
        }
      }
    );
    
    // Carica i dati al montaggio del componente
    onMounted(() => {
      loadUserData();
      setupPeriodicSync();
    });
    
    // Pulizia quando il componente viene smontato
    onUnmounted(() => {
      if (syncInterval) {
        clearInterval(syncInterval);
        syncInterval = null;
      }
    });
    
    return {};
  }
};
</script>

<style scoped>
.user-data-loader {
  display: none;
}
</style> 