<template>
  <div class="movie-card" :class="{ 'is-detailed': isDetailed }">
    <div class="poster-container" @click="goToDetails">
      <div class="poster-overlay">
        <div class="movie-rating">
          <i class="fas fa-star"></i>
          <span>{{ formattedRating }}</span>
        </div>
        
        <div class="movie-year">{{ movie.release_year }}</div>
        
        <div class="movie-actions">
          <button 
            class="action-btn favorite-btn" 
            :class="{ 'is-active': isFavorite }"
            @click.stop="toggleFavorite"
            :title="isFavorite ? 'Rimuovi dai preferiti' : 'Aggiungi ai preferiti'"
          >
            <i class="fas" :class="isFavorite ? 'fa-heart' : 'fa-heart'"></i>
          </button>
          
          <button 
            v-if="showWatchedToggle"
            class="action-btn watched-btn" 
            :class="{ 'is-active': isWatched }"
            @click.stop="toggleWatched"
            :title="isWatched ? 'Rimuovi da visti' : 'Segna come visto'"
          >
            <i class="fas" :class="isWatched ? 'fa-eye' : 'fa-eye'"></i>
          </button>
        </div>
      </div>
      
      <img 
        v-if="posterUrl" 
        :src="posterUrl" 
        :alt="movie.title" 
        class="movie-poster"
        @error="handleImageError"
      >
      <div v-else class="poster-placeholder">
        <span class="movie-title-small">{{ movie.title }}</span>
      </div>
    </div>
    
    <div class="movie-info" @click="goToDetails">
      <h3 class="movie-title" :title="movie.title">{{ movie.title }}</h3>
      
      <div class="movie-genres" v-if="formattedGenres">
        <span>{{ formattedGenres }}</span>
      </div>
      
      <p class="movie-overview" v-if="isDetailed && movie.overview">
        {{ truncatedOverview }}
      </p>
    </div>
  </div>
</template>

<script>
import { computed, toRefs } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'MovieCard',
  props: {
    movie: {
      type: Object,
      required: true
    },
    isDetailed: {
      type: Boolean,
      default: false
    },
    showWatchedToggle: {
      type: Boolean,
      default: true
    }
  },
  
  setup(props, { emit }) {
    const { movie } = toRefs(props)
    const store = useStore()
    const router = useRouter()
    
    const posterUrl = computed(() => {
      if (!movie.value.poster_path) return null
      
      // Check if poster_path is a full URL or just a path
      if (movie.value.poster_path.startsWith('http')) {
        return movie.value.poster_path
      }
      
      // TMDB posters
      return `https://image.tmdb.org/t/p/w342${movie.value.poster_path}`
    })
    
    const formattedRating = computed(() => {
      return movie.value.vote_average ? movie.value.vote_average.toFixed(1) : 'N/A'
    })
    
    const formattedGenres = computed(() => {
      if (!movie.value.genres || movie.value.genres.length === 0) return null
      return movie.value.genres.slice(0, 2).join(', ')
    })
    
    const truncatedOverview = computed(() => {
      if (!movie.value.overview) return ''
      return movie.value.overview.length > 120 
        ? movie.value.overview.substring(0, 120) + '...'
        : movie.value.overview
    })
    
    const isFavorite = computed(() => {
      const favorites = store.getters['movies/favorites']
      return favorites.some(fav => fav.movie_id === movie.value.movie_id)
    })
    
    const isWatched = computed(() => {
      const watched = store.getters['movies/watched']
      return watched.some(w => w.movie_id === movie.value.movie_id)
    })
    
    const goToDetails = () => {
      router.push({ name: 'MovieDetail', params: { id: movie.value.movie_id } })
    }
    
    const toggleFavorite = async (event) => {
      if (isLoading.value) return;
      if (!store.getters['auth/isAuthenticated']) {
        // Removed warning notification
        console.warn('User not authenticated. Cannot add to favorites.')
        return
      }

      try {
        isLoading.value = true
        const result = await toggleFavoriteAPI(props.movie.movie_id)
        
        // Update UI based on response
        if (result && typeof result.isFavorite === 'boolean') {
          isFavorite.value = result.isFavorite
          
          // Removed success notification
          console.log(result.isFavorite 
            ? `${props.movie.title} added to favorites`
            : `${props.movie.title} removed from favorites`)
          
          // Update store if needed
          if (result.isFavorite) {
            store.dispatch('movies/addToFavorites', props.movie)
          } else {
            store.dispatch('movies/removeFromFavorites', props.movie.movie_id)
          }
        }
      } catch (error) {
        // Removed error notification
        console.error('Error toggling favorite:', error)
      } finally {
        isLoading.value = false
      }
    }
    
    const toggleWatched = () => {
      if (isWatched.value) {
        store.dispatch('movies/removeFromWatched', movie.value.movie_id)
      } else {
        store.dispatch('movies/addToWatched', movie.value.movie_id)
      }
      
      emit('watched-toggled', { 
        movieId: movie.value.movie_id, 
        isWatched: !isWatched.value 
      })
    }
    
    const handleImageError = (event) => {
      event.target.style.display = 'none'
      const placeholder = event.target.parentNode.querySelector('.poster-placeholder')
      if (placeholder) {
        placeholder.style.display = 'flex'
      }
    }
    
    return {
      posterUrl,
      formattedRating,
      formattedGenres,
      truncatedOverview,
      isFavorite,
      isWatched,
      goToDetails,
      toggleFavorite,
      toggleWatched,
      handleImageError
    }
  }
}
</script>

<style lang="scss" scoped>
.movie-card {
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color-light);
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
  height: 100%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
    
    .poster-overlay {
      opacity: 1;
    }
  }
  
  &.is-detailed {
    flex-direction: row;
    height: auto;
    
    .poster-container {
      flex: 0 0 150px;
      height: 225px;
    }
    
    .movie-info {
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      align-items: flex-start;
    }
    
    .movie-title {
      font-size: 1.1rem;
      margin-bottom: 8px;
    }
    
    .movie-genres {
      margin-bottom: 12px;
    }
    
    .movie-overview {
      display: block;
      font-size: 0.9rem;
      color: var(--text-color-light);
      line-height: 1.4;
    }
  }
}

.poster-container {
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  overflow: hidden;
  background-color: var(--bg-color-dark);
  cursor: pointer;
}

.movie-poster {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
  
  .movie-card:hover & {
    transform: scale(1.05);
  }
}

.poster-placeholder {
  display: none;
  width: 100%;
  height: 100%;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, var(--primary-color-light), var(--primary-color-dark));
  color: white;
  padding: 16px;
  text-align: center;
}

.movie-title-small {
  font-weight: 700;
  font-size: 1rem;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.poster-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0.5) 0%,
    rgba(0, 0, 0, 0) 30%,
    rgba(0, 0, 0, 0) 70%,
    rgba(0, 0, 0, 0.7) 100%
  );
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 10px;
}

.movie-info {
  padding: 12px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.movie-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.movie-genres {
  font-size: 0.8rem;
  color: var(--text-color-light);
  margin-bottom: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.movie-overview {
  display: none;
}

.movie-rating, .movie-year {
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 0.75rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  z-index: 2;
}

.movie-rating {
  color: #ffdd57;
  
  i {
    margin-right: 4px;
  }
}

.movie-year {
  align-self: flex-end;
}

.movie-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  position: absolute;
  bottom: 10px;
  right: 10px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.2s;
  
  &:hover {
    background-color: rgba(0, 0, 0, 0.9);
    transform: scale(1.1);
  }
  
  &.is-active {
    background-color: var(--primary-color);
    
    &:hover {
      background-color: var(--primary-color-dark);
    }
  }
}

.favorite-btn {
  &.is-active {
    color: #ff5757;
  }
}

.watched-btn {
  &.is-active {
    color: #57ff57;
  }
}

@media (max-width: 767px) {
  .movie-card.is-detailed {
    flex-direction: column;
    
    .poster-container {
      width: 100%;
      flex: none;
      height: auto;
    }
  }
}
</style> 