<template>
  <div class="movie-detail" v-if="movie">
    <div class="backdrop" :style="backdropStyle"></div>
    
    <div class="content-container">
      <div class="movie-header">
        <div class="poster-container">
          <img v-if="movie.poster_path" :src="posterUrl" :alt="movie.title" class="poster" />
          <div v-else class="no-poster">
            <span>{{ movie.title }}</span>
          </div>
        </div>
        
        <div class="movie-info">
          <h1 class="title">{{ movie.title }}</h1>
          
          <div class="meta">
            <span v-if="movie.release_year" class="year">{{ movie.release_year }}</span>
            <span v-if="movie.runtime" class="runtime">{{ formatRuntime(movie.runtime) }}</span>
            <span v-if="movie.vote_average" class="rating">
              <i class="fas fa-star"></i> {{ Number(movie.vote_average).toFixed(1) }}/10
            </span>
          </div>
          
          <div v-if="movie.genres && movie.genres.length" class="genres">
            <span v-for="genre in movie.genres" :key="genre" class="genre-tag">
              {{ genre }}
            </span>
          </div>
          
          <p v-if="movie.overview" class="overview">{{ movie.overview }}</p>
          
          <div class="actions">
            <button 
              @click="toggleFavorite" 
              class="btn-action" 
              :class="{ 'is-active': isFavorite }"
              :disabled="favLoading"
            >
              <i class="fas" :class="isFavorite ? 'fa-heart' : 'fa-heart-o'"></i>
              {{ isFavorite ? 'Nei preferiti' : 'Aggiungi ai preferiti' }}
            </button>
            
            <button 
              @click="toggleWatched" 
              class="btn-action" 
              :class="{ 'is-active': isWatched }"
              :disabled="watchLoading"
            >
              <i class="fas" :class="isWatched ? 'fa-check-circle' : 'fa-check-circle-o'"></i>
              {{ isWatched ? 'Visto' : 'Segna come visto' }}
            </button>
          </div>
        </div>
      </div>
      
      <div v-if="loading" class="loading-container">
        <div class="loader"></div>
        <p>Caricamento dei film simili...</p>
      </div>
      
      <div v-else-if="similarMovies.length" class="similar-section">
        <h2>Film simili</h2>
        <div class="similar-movies">
          <div 
            v-for="similarMovie in similarMovies" 
            :key="similarMovie.movie_id" 
            class="similar-movie-card"
          >
            <movie-card :movie="similarMovie" />
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="loading-container full-page">
    <div class="loader"></div>
    <p>Caricamento dettagli film...</p>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'
import { getMovieDetails, getSimilarMovies, toggleFavorite as toggleFav, addToWatched, removeFromWatched } from '@/services/api'
import MovieCard from '@/components/MovieCard.vue'

export default {
  name: 'MovieDetail',
  components: {
    MovieCard
  },
  
  setup() {
    const store = useStore()
    const route = useRoute()
    const router = useRouter()
    
    const movie = ref(null)
    const similarMovies = ref([])
    const loading = ref(false)
    const favLoading = ref(false)
    const watchLoading = ref(false)
    
    const isFavorite = computed(() => {
      if (!movie.value) return false
      const favorites = store.getters['movies/favorites']
      return favorites.some(fav => fav.movie_id === movie.value.movie_id)
    })
    
    const isWatched = computed(() => {
      if (!movie.value) return false
      const watched = store.getters['movies/watched']
      return watched.some(w => w.movie_id === movie.value.movie_id)
    })
    
    const posterUrl = computed(() => {
      if (!movie.value || !movie.value.poster_path) return null
      
      if (movie.value.poster_path.startsWith('http')) {
        return movie.value.poster_path
      }
      
      return `https://image.tmdb.org/t/p/w500${movie.value.poster_path}`
    })
    
    const backdropStyle = computed(() => {
      if (!movie.value || !movie.value.backdrop_path) {
        return {
          backgroundColor: '#1a1a2e'
        }
      }
      
      const backdropUrl = movie.value.backdrop_path.startsWith('http')
        ? movie.value.backdrop_path
        : `https://image.tmdb.org/t/p/original${movie.value.backdrop_path}`
      
      return {
        backgroundImage: `linear-gradient(to bottom, rgba(26, 26, 46, 0.7), rgba(26, 26, 46, 0.95)), url(${backdropUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center top'
      }
    })
    
    const formatRuntime = (minutes) => {
      if (!minutes) return null
      const hrs = Math.floor(minutes / 60)
      const mins = minutes % 60
      return `${hrs}h ${mins}m`
    }
    
    const loadMovieDetails = async () => {
      const movieId = route.params.id
      if (!movieId) {
        router.push({ name: 'Home' })
        return
      }
      
      try {
        movie.value = null
        const result = await getMovieDetails(movieId)
        if (Array.isArray(result) && result.length > 0) {
          movie.value = result[0]
          loadSimilarMovies(movieId)
        } else {
          console.error('Could not load movie details.')
          router.push({ name: 'Home' })
        }
      } catch (error) {
        console.error('Error loading movie details:', error)
        router.push({ name: 'Home' })
      }
    }
    
    const loadSimilarMovies = async (movieId) => {
      try {
        loading.value = true
        const result = await getSimilarMovies(movieId, 6)
        if (Array.isArray(result)) {
          similarMovies.value = result.filter(m => m.movie_id !== movieId)
        }
      } catch (error) {
        console.error('Error loading similar movies:', error)
      } finally {
        loading.value = false
      }
    }
    
    const toggleFavorite = async () => {
      if (!store.getters['auth/isAuthenticated']) {
        console.warn('User not authenticated. Cannot add to favorites.')
        return
      }
      
      try {
        favLoading.value = true
        const result = await toggleFav(movie.value.movie_id)
        
        if (result && typeof result.isFavorite === 'boolean') {
          // Update store
          if (result.isFavorite) {
            store.dispatch('movies/addToFavorites', movie.value)
            console.log(`${movie.value.title} added to favorites`)
          } else {
            store.dispatch('movies/removeFromFavorites', movie.value.movie_id)
            console.log(`${movie.value.title} removed from favorites`)
          }
        }
      } catch (error) {
        console.error('Error toggling favorite:', error)
      } finally {
        favLoading.value = false
      }
    }
    
    const toggleWatched = async () => {
      if (!store.getters['auth/isAuthenticated']) {
        console.warn('User not authenticated. Cannot track watched movies.')
        return
      }
      
      try {
        watchLoading.value = true
        
        if (isWatched.value) {
          await removeFromWatched(movie.value.movie_id)
          store.dispatch('movies/removeFromWatched', movie.value.movie_id)
          console.log(`${movie.value.title} removed from watched list`)
        } else {
          await addToWatched(movie.value.movie_id)
          store.dispatch('movies/addToWatched', movie.value)
          console.log(`${movie.value.title} added to watched list`)
        }
      } catch (error) {
        console.error('Error toggling watched status:', error)
      } finally {
        watchLoading.value = false
      }
    }
    
    onMounted(() => {
      loadMovieDetails()
    })
    
    return {
      movie,
      similarMovies,
      loading,
      favLoading,
      watchLoading,
      isFavorite,
      isWatched,
      posterUrl,
      backdropStyle,
      formatRuntime,
      toggleFavorite,
      toggleWatched
    }
  }
}
</script>

<style lang="scss" scoped>
.movie-detail {
  position: relative;
  min-height: 100vh;
  background-color: var(--bg-color);
}

.backdrop {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 500px;
  z-index: 1;
}

.content-container {
  position: relative;
  z-index: 2;
  padding: 30px 20px;
  max-width: 1200px;
  margin: 0 auto;
  
  @media (min-width: 768px) {
    padding: 60px 40px;
  }
}

.movie-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 40px;
  
  @media (min-width: 768px) {
    flex-direction: row;
    gap: 40px;
  }
}

.poster-container {
  flex-shrink: 0;
  width: 100%;
  max-width: 300px;
  margin: 0 auto 30px;
  
  @media (min-width: 768px) {
    margin: 0;
    width: 300px;
  }
  
  .poster {
    width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  }
  
  .no-poster {
    width: 100%;
    aspect-ratio: 2/3;
    background-color: #2a3a4a;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    
    span {
      font-weight: bold;
      font-size: 1.5rem;
      color: white;
      text-align: center;
      padding: 20px;
    }
  }
}

.movie-info {
  flex: 1;
  color: white;
}

.title {
  font-size: 2rem;
  margin: 0 0 16px;
  
  @media (min-width: 768px) {
    font-size: 2.5rem;
  }
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
  font-size: 1rem;
  
  .year, .runtime, .rating {
    display: flex;
    align-items: center;
  }
  
  .rating {
    i {
      color: #ffc107;
      margin-right: 6px;
    }
  }
}

.genres {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  
  .genre-tag {
    background-color: rgba(255, 255, 255, 0.1);
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
  }
}

.overview {
  font-size: 1rem;
  line-height: 1.6;
  margin-bottom: 30px;
  color: rgba(255, 255, 255, 0.9);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 30px;
}

.btn-action {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-radius: 4px;
  border: none;
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  
  i {
    margin-right: 8px;
    font-size: 1rem;
  }
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.2);
  }
  
  &.is-active {
    background-color: var(--primary-color);
    
    &:hover {
      background-color: var(--primary-dark);
    }
  }
  
  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
}

.similar-section {
  margin-top: 60px;
  
  h2 {
    color: white;
    margin: 0 0 20px;
    font-size: 1.5rem;
  }
}

.similar-movies {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 20px;
  
  @media (min-width: 768px) {
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  }
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: white;
  
  &.full-page {
    min-height: 60vh;
  }
  
  .loader {
    width: 40px;
    height: 40px;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: var(--primary-color);
    animation: spin 1s ease-in-out infinite;
    margin-bottom: 16px;
  }
  
  p {
    margin: 0;
    color: rgba(255, 255, 255, 0.7);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style> 