<template>
  <div class="search-page">
    <h1>Cerca Film</h1>
    
    <div class="search-container">
      <div class="search-input-container">
        <input 
          type="text" 
          v-model="searchQuery" 
          @input="handleSearch"
          placeholder="Cerca per titolo, genere, attori o trama..."
          class="search-input"
        >
        <button 
          v-if="searchQuery" 
          @click="clearSearch" 
          class="clear-btn"
        >
          ✕
        </button>
      </div>
      
      <div class="search-info">
        <p v-if="searchQuery && !loading" class="results-count">
          {{ searchResults.length }} risultati trovati
        </p>
      </div>
    </div>
    
    <div v-if="loading" class="loader">
      <div class="spinner"></div>
      <span>Ricerca in corso...</span>
    </div>
    
    <div v-else-if="searchQuery && searchResults.length === 0" class="no-results">
      <h3>Nessun risultato trovato</h3>
      <p>Prova a modificare la tua ricerca o a usare termini diversi</p>
    </div>
    
    <div v-else-if="searchResults.length > 0" class="search-results">
      <div class="movie-grid">
        <MovieCard 
          v-for="movie in searchResults" 
          :key="movie.movie_id" 
          :movie="movie"
          :score="movie.score"
          @click="selectMovie(movie)"
        />
      </div>
    </div>
    
    <div v-else class="search-tips">
      <h3>Suggerimenti per la ricerca</h3>
      <p>Puoi cercare film utilizzando:</p>
      <ul>
        <li>Titoli di film: es. "Il Padrino", "Interstellar"</li>
        <li>Generi: es. "horror con zombie", "commedia romantica"</li>
        <li>Attori o registi: es. "film con Tom Hanks", "diretto da Nolan"</li>
        <li>Tematiche o descrizioni: es. "film sulla seconda guerra mondiale", "viaggi nello spazio"</li>
        <li>Combinazioni: es. "thriller psicologico con Leonardo DiCaprio"</li>
      </ul>
      
      <div class="example-searches">
        <h4>Prova queste ricerche:</h4>
        <div class="examples">
          <button @click="setExampleSearch('film di fantascienza con alieni')" class="example-btn">film di fantascienza con alieni</button>
          <button @click="setExampleSearch('commedia romantica ambientata a New York')" class="example-btn">commedia romantica a New York</button>
          <button @click="setExampleSearch('thriller con colpi di scena')" class="example-btn">thriller con colpi di scena</button>
          <button @click="setExampleSearch('film d\'animazione per famiglie')" class="example-btn">film d'animazione per famiglie</button>
          <button @click="setExampleSearch('avventura fantasy con draghi')" class="example-btn">avventura fantasy con draghi</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useStore } from 'vuex';
import MovieCard from '@/components/MovieCard.vue';
import debounce from 'lodash.debounce';

export default {
  name: 'SearchView',
  components: {
    MovieCard
  },
  setup() {
    const store = useStore();
    const searchQuery = ref('');
    
    // Computed properties
    const searchResults = computed(() => store.getters['movies/searchResults']);
    const loading = computed(() => store.getters['movies/loading']);
    
    // Create debounced search function
    const debouncedSearch = debounce((query) => {
      if (query.trim()) {
        store.dispatch('movies/searchMovies', {
          query: query,
          topK: 20
        });
      } else {
        store.commit('movies/SET_SEARCH_RESULTS', []);
      }
    }, 500);
    
    // Methods
    const handleSearch = () => {
      debouncedSearch(searchQuery.value);
    };
    
    const clearSearch = () => {
      searchQuery.value = '';
      store.commit('movies/SET_SEARCH_RESULTS', []);
    };
    
    const selectMovie = (movie) => {
      store.dispatch('movies/selectMovie', movie);
    };
    
    const setExampleSearch = (example) => {
      searchQuery.value = example;
      handleSearch();
    };
    
    // Clear results when component is mounted
    onMounted(() => {
      clearSearch();
    });
    
    return {
      searchQuery,
      searchResults,
      loading,
      handleSearch,
      clearSearch,
      selectMovie,
      setExampleSearch
    };
  }
};
</script>

<style scoped lang="scss">
.search-page {
  padding: 20px 0 60px;
  
  h1 {
    font-size: 2.5rem;
    margin-bottom: 30px;
  }
}

// Search container
.search-container {
  margin-bottom: 30px;
  
  .search-input-container {
    position: relative;
    margin-bottom: 15px;
    
    .search-input {
      width: 100%;
      padding: 15px 50px 15px 20px;
      border: none;
      border-radius: 30px;
      background-color: var(--card-background);
      color: var(--text-color);
      font-size: 1.1rem;
      transition: box-shadow 0.3s;
      
      &:focus {
        outline: none;
        box-shadow: 0 0 0 2px var(--primary-color);
      }
      
      &::placeholder {
        color: rgba(255, 255, 255, 0.5);
      }
    }
    
    .clear-btn {
      position: absolute;
      top: 50%;
      right: 15px;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.7);
      font-size: 1.2rem;
      cursor: pointer;
      
      &:hover {
        color: white;
      }
    }
  }
  
  .search-info {
    .results-count {
      font-size: 0.9rem;
      color: rgba(255, 255, 255, 0.7);
    }
  }
}

// Search results
.search-results {
  .movie-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 20px;
  }
}

// No results
.no-results {
  text-align: center;
  padding: 60px 20px;
  background-color: var(--card-background);
  border-radius: 10px;
  
  h3 {
    font-size: 1.5rem;
    margin-bottom: 15px;
  }
  
  p {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 30px;
  }
}

// Search tips
.search-tips {
  margin-top: 40px;
  background-color: var(--card-background);
  padding: 30px;
  border-radius: 10px;
  
  h3 {
    font-size: 1.5rem;
    margin-bottom: 20px;
  }
  
  p {
    margin-bottom: 15px;
  }
  
  ul {
    margin-bottom: 30px;
    padding-left: 20px;
    
    li {
      margin-bottom: 10px;
      color: rgba(255, 255, 255, 0.8);
    }
  }
  
  .example-searches {
    h4 {
      margin-bottom: 15px;
    }
    
    .examples {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      
      .example-btn {
        background-color: rgba(103, 58, 183, 0.15);
        border: 1px solid rgba(103, 58, 183, 0.3);
        padding: 8px 15px;
        border-radius: 20px;
        color: var(--text-color);
        cursor: pointer;
        transition: background-color 0.2s;
        
        &:hover {
          background-color: rgba(103, 58, 183, 0.3);
        }
      }
    }
  }
}

// Loader
.loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 0;
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid rgba(255, 255, 255, 0.1);
    border-radius: 50%;
    border-top-color: var(--primary-color);
    animation: spin 1s ease-in-out infinite;
    margin-bottom: 15px;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
}

// Responsive adjustments
@media (max-width: 768px) {
  .search-page {
    h1 {
      font-size: 2rem;
    }
  }
  
  .search-results {
    .movie-grid {
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 15px;
    }
  }
  
  .example-searches {
    .examples {
      flex-direction: column;
      
      .example-btn {
        width: 100%;
        margin-bottom: 8px;
      }
    }
  }
}
</style> 