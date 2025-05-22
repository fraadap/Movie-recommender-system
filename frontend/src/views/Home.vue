<template>
  <div class="home-page">
    <!-- Hero section -->
    <section class="hero">
      <div class="hero-content">
        <h1>Scopri i migliori film per i tuoi gusti</h1>
        <p>Raccomandazioni personalizzate basate su tecnologie di AI avanzate</p>
        <router-link to="/search" class="btn-primary">Cerca un film</router-link>
      </div>
    </section>
    
    <!-- Personal recommendations section -->
    <section v-if="isAuthenticated" class="recommendations">
      <div class="section-header">
        <h2>Consigliati per te</h2>
        <div v-if="!recommendedMovies.length && !loading" class="empty-state">
          <p>Valuta più film per ottenere consigli personalizzati</p>
        </div>
      </div>
      
      <div v-if="loading" class="loader">
        <div class="spinner"></div>
        <span>Caricamento consigli...</span>
      </div>
      
      <div v-else class="movie-carousel">
        <div v-if="recommendedMovies.length" class="movie-grid">
          <MovieCard 
            v-for="movie in recommendedMovies" 
            :key="movie.movie_id" 
            :movie="movie"
            @click="selectMovie(movie)"
          />
        </div>
      </div>
    </section>
    
    <!-- Recently viewed section -->
    <section v-if="recentlyViewed.length" class="recently-viewed">
      <div class="section-header">
        <h2>Visti di recente</h2>
      </div>
      
      <div class="movie-carousel">
        <div class="movie-grid">
          <MovieCard 
            v-for="movie in recentlyViewed" 
            :key="movie.movie_id" 
            :movie="movie"
            @click="selectMovie(movie)"
          />
        </div>
      </div>
    </section>
    
    <!-- Trending movies section -->
    <section class="trending">
      <div class="section-header">
        <h2>I più popolari</h2>
      </div>
      
      <div v-if="loading" class="loader">
        <div class="spinner"></div>
        <span>Caricamento film popolari...</span>
      </div>
      
      <div v-else class="movie-carousel">
        <div class="movie-grid">
          <MovieCard 
            v-for="movie in trendingMovies" 
            :key="movie.movie_id" 
            :movie="movie"
            @click="selectMovie(movie)"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { computed, onMounted, ref } from 'vue';
import { useStore } from 'vuex';
import MovieCard from '@/components/MovieCard.vue';

export default {
  name: 'HomeView',
  components: {
    MovieCard
  },
  setup() {
    const store = useStore();
    const trendingMovies = ref([]);
    
    // Computed properties
    const isAuthenticated = computed(() => store.getters['auth/isAuthenticated']);
    const user = computed(() => store.getters['auth/user']);
    const recommendedMovies = computed(() => store.getters['movies/recommendedMovies']);
    const recentlyViewed = computed(() => store.getters['movies/recentlyViewed']);
    const loading = computed(() => store.getters['movies/loading']);
    
    // Methods
    const selectMovie = (movie) => {
      store.dispatch('movies/selectMovie', movie);
    };
    
    // Load recommendations and trending movies on mount
    onMounted(async () => {
      // Load recently viewed from localStorage
      store.dispatch('movies/loadRecentlyViewed');
      
      // Get collaborative recommendations if user is logged in
      if (isAuthenticated.value && user.value) {
        store.dispatch('movies/getCollaborativeRecommendations', {
          userId: user.value.id,
          topK: 10
        });
      }
      
      // Simulate loading trending movies (in a real app, you'd call an API)
      // This is just placeholder data for now
      trendingMovies.value = [
        {
          movie_id: '299536',
          title: 'Avengers: Infinity War',
          overview: "Gli Avengers e i loro alleati dovranno essere pronti a sacrificare tutto nel tentativo di sconfiggere il potente Thanos prima che il suo impeto di devastazione e rovina porti alla fine dell'universo.",
          poster_path: '/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg',
          release_year: 2018,
          vote_average: 8.3,
          genres: ['Avventura', 'Azione', 'Fantascienza']
        },
        {
          movie_id: '724089',
          title: "Gabriel's Inferno Part II",
          overview: "Il professor Gabriel Emerson si unisce finalmente a Julia Mitchell in una tenera, sensuale relazione. Ma la loro felicità è minacciata da cospiratori, rivali e segreti del passato di Gabriel.",
          poster_path: '/x5o8cLZfEXMoZczTYWLrUo1P7UJ.jpg',
          release_year: 2020,
          vote_average: 8.8,
          genres: ['Romance']
        },
        {
          movie_id: '238',
          title: 'Il padrino',
          overview: "Il potente boss Don Vito Corleone, ormai vecchio, decide di trasferire il suo impero nelle mani del figlio Michael. Inizialmente riluttante, Michael si troverà costretto dalle circostanze a entrare negli affari di famiglia e a prendere decisioni difficili.",
          poster_path: '/d4KNaTrltq6bpkFS01pYtyXa09m.jpg',
          release_year: 1972,
          vote_average: 8.7,
          genres: ['Drammatico', 'Crime']
        },
        {
          movie_id: '278',
          title: 'Le ali della libertà',
          overview: "Andy Dufresne, un banchiere, viene condannato all'ergastolo per l'omicidio di sua moglie e del suo amante. Scoprirà che in prigione la sola cosa che può salvarlo è l'amicizia e la speranza.",
          poster_path: '/9O7gLzmreU0nGkIB6K3BsJbzvNv.jpg',
          release_year: 1994,
          vote_average: 8.7,
          genres: ['Drammatico', 'Crime']
        },
        {
          movie_id: '696374',
          title: "Gabriel's Inferno",
          overview: "Un professore di letteratura intrigante che nasconde un oscuro passato incontra una studentessa innocente. La loro attrazione scatena una storia d'amore sensuale in cui si troveranno ad affrontare i loro demoni personali.",
          poster_path: '/oyG9TL7FcRP4EZ9Vid6uKzwdndz.jpg',
          release_year: 2020,
          vote_average: 8.6,
          genres: ['Romance']
        }
      ];
    });
    
    return {
      isAuthenticated,
      recommendedMovies,
      recentlyViewed,
      trendingMovies,
      loading,
      selectMovie
    };
  }
};
</script>

<style scoped lang="scss">
.home-page {
  padding-bottom: 60px;
}

// Hero section
.hero {
  height: 60vh;
  min-height: 400px;
  background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
              url('https://source.unsplash.com/random/1920x1080/?movie,cinema') no-repeat center center;
  background-size: cover;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  margin-bottom: 40px;
  border-radius: 10px;
  
  .hero-content {
    max-width: 800px;
    padding: 20px;
    
    h1 {
      font-size: 3rem;
      margin-bottom: 20px;
      color: white;
      text-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);
    }
    
    p {
      font-size: 1.2rem;
      margin-bottom: 30px;
      color: #e0e0e0;
      text-shadow: 1px 1px 5px rgba(0, 0, 0, 0.5);
    }
    
    .btn-primary {
      display: inline-block;
      padding: 12px 30px;
      background-color: var(--primary-color);
      color: white;
      border-radius: 30px;
      font-size: 1.1rem;
      text-decoration: none;
      transition: background-color 0.3s, transform 0.3s;
      
      &:hover {
        background-color: var(--accent-color);
        transform: translateY(-2px);
      }
    }
  }
}

// Section styling
section {
  margin-bottom: 40px;
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h2 {
      font-size: 1.8rem;
      font-weight: 600;
    }
  }
  
  .empty-state {
    text-align: center;
    padding: 40px;
    background-color: var(--card-background);
    border-radius: 10px;
    
    p {
      color: #888;
      margin-bottom: 20px;
    }
  }
}

// Movie grid
.movie-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

// Loader
.loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  
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
  .hero {
    min-height: 300px;
    
    .hero-content {
      h1 {
        font-size: 2rem;
      }
      
      p {
        font-size: 1rem;
      }
    }
  }
  
  .movie-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 15px;
  }
}
</style> 