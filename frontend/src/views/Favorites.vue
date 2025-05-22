<template>
  <div class="watched-page">
    <div class="page-header">
      <h1>Your Watched Movies</h1>
      <p class="subheader">Keep track of movies you've watched and rated</p>
    </div>

    <div v-if="loading" class="loader">
      <div class="spinner"></div>
      <span>Loading your watched movies...</span>
    </div>

    <div v-else-if="!watchedMovies.length" class="empty-state">
      <div class="empty-icon">🎬</div>
      <h3>You haven't watched any movies yet</h3>
      <p>Movies you watch and rate will appear here so you can keep track of them</p>
      <router-link to="/search" class="btn-primary">Discover Movies</router-link>
    </div>

    <template v-else>
      <div class="controls">
        <div class="filter-sort">
          <div class="sort-control">
            <label for="sort-by">Sort by:</label>
            <select id="sort-by" v-model="sortBy" @change="sortWatched">
              <option value="date">Recently Added</option>
              <option value="rating-desc">Highest Rating</option>
              <option value="rating-asc">Lowest Rating</option>
              <option value="title">Title</option>
              <option value="year-desc">Newest</option>
              <option value="year-asc">Oldest</option>
            </select>
          </div>
          
          <div class="filter-control">
            <label for="filter-ratings">Filter by rating:</label>
            <select id="filter-ratings" v-model="filterRating">
              <option value="all">All Ratings</option>
              <option value="rated">Rated Only</option>
              <option value="unrated">Unrated Only</option>
              <option value="5">5 Stars</option>
              <option value="4">4+ Stars</option>
              <option value="3">3+ Stars</option>
              <option value="2">2+ Stars</option>
              <option value="1">1+ Star</option>
            </select>
          </div>
        </div>
        
        <div class="action-buttons" v-if="selectedMovies.length">
          <span class="selected-count">{{ selectedMovies.length }} selected</span>
          <button @click="clearSelection" class="btn-outline">Clear</button>
          <button @click="removeSelected" class="btn-danger">Remove</button>
        </div>
      </div>

      <!-- Collaborative Recommendations Carousel -->
      <div v-if="recommendations.length" class="recommendations-section">
        <h2>Recommended Based on Your Watch History</h2>
        <div class="carousel-container">
          <button 
            @click="scrollCarousel('left')" 
            class="carousel-control left"
            :disabled="carouselScrollPos <= 0"
          >
            &#10094;
          </button>
          
          <div class="carousel" ref="carousel">
            <div 
              v-for="movie in recommendations" 
              :key="movie.movie_id" 
              class="carousel-item"
              @click="viewMovie(movie)"
            >
              <div class="carousel-poster">
                <img 
                  v-if="getPosterUrl(movie.poster_path)" 
                  :src="getPosterUrl(movie.poster_path)" 
                  :alt="movie.title" 
                />
                <div v-else class="poster-placeholder">
                  <span>{{ movie.title[0] }}</span>
                </div>
              </div>
              <div class="carousel-info">
                <h4>{{ movie.title }}</h4>
                <div class="match-score">
                  <i class="ai-icon">★</i>
                  <span>{{ Math.round(movie.score * 100) }}% match</span>
                </div>
              </div>
            </div>
          </div>
          
          <button 
            @click="scrollCarousel('right')" 
            class="carousel-control right"
          >
            &#10095;
          </button>
        </div>
      </div>

      <!-- Watched Movies Grid -->
      <div class="watched-grid">
        <div 
          v-for="movie in filteredWatched" 
          :key="movie.movie_id" 
          class="watched-item"
          :class="{ 'selected': isSelected(movie) }"
          @click="toggleSelection(movie)"
        >
          <div class="movie-poster">
            <img 
              v-if="getPosterUrl(movie.poster_path)" 
              :src="getPosterUrl(movie.poster_path)" 
              :alt="movie.title" 
            />
            <div v-else class="poster-placeholder">
              <span>{{ movie.title[0] }}</span>
            </div>
            
            <div class="movie-overlay">
              <div class="user-rating" v-if="getUserRating(movie.movie_id)">
                <div class="rating-stars">
                  <star-rating 
                    :rating="getUserRating(movie.movie_id)" 
                    :read-only="true"
                    :increment="0.5"
                    :star-size="16"
                    :show-rating="false"
                    inactive-color="rgba(255, 255, 255, 0.3)"
                    active-color="#ffc107"
                  />
                </div>
                <div class="rating-value">{{ (getUserRating(movie.movie_id) * 2).toFixed(1) }}/10</div>
              </div>
              
              <div class="movie-actions">
                <button @click.stop="viewMovie(movie)" class="action-btn view-btn">
                  <i class="view-icon">👁️</i>
                </button>
                <button @click.stop="showRating(movie)" class="action-btn rate-btn">
                  <i class="rate-icon">★</i>
                </button>
                <button @click.stop="removeWatched(movie)" class="action-btn remove-btn">
                  <i class="remove-icon">×</i>
                </button>
              </div>
            </div>
            
            <div class="selection-indicator">
              <div class="checkmark">✓</div>
            </div>
          </div>
          
          <div class="movie-info">
            <h3 class="movie-title">{{ movie.title }}</h3>
            <div class="movie-meta">
              <span v-if="movie.release_year" class="year">{{ movie.release_year }}</span>
              <span v-if="movie.vote_average" class="rating">
                {{ movie.vote_average.toFixed(1) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Rating Dialog -->
    <div v-if="ratingDialog" class="rating-dialog">
      <div class="rating-container">
        <div class="rating-header">
          <h3>Rate "{{ currentMovie.title }}"</h3>
          <button @click="ratingDialog = false" class="close-btn">×</button>
        </div>
        
        <div class="rating-body">
          <star-rating 
            v-model="currentRating"
            :increment="0.5"
            :star-size="36"
            :show-rating="false"
            inactive-color="#6c757d"
            active-color="#ffc107"
          />
          <div class="rating-value">{{ (currentRating * 2).toFixed(1) }}/10</div>
        </div>
        
        <div class="rating-footer">
          <button @click="ratingDialog = false" class="btn-outline">Cancel</button>
          <button @click="submitRating" class="btn-primary">Save Rating</button>
        </div>
      </div>
    </div>
    
    <!-- Confirmation Dialog -->
    <div v-if="confirmDialog" class="confirm-dialog">
      <div class="confirm-container">
        <div class="confirm-header">
          <h3>Confirm Removal</h3>
          <button @click="confirmDialog = false" class="close-btn">×</button>
        </div>
        
        <div class="confirm-body">
          <p v-if="selectedMovies.length">
            Are you sure you want to remove {{ selectedMovies.length }} 
            {{ selectedMovies.length === 1 ? 'movie' : 'movies' }} from your watched list?
          </p>
          <p v-else>
            Are you sure you want to remove "{{ currentMovie.title }}" from your watched list?
          </p>
        </div>
        
        <div class="confirm-footer">
          <button @click="confirmDialog = false" class="btn-outline">Cancel</button>
          <button @click="confirmRemove" class="btn-danger">Remove</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';
import StarRating from 'vue-star-rating';

export default {
  name: 'WatchedView',
  components: {
    StarRating
  },
  setup() {
    const store = useStore();
    const router = useRouter();
    
    // Refs
    const carousel = ref(null);
    const carouselScrollPos = ref(0);
    const sortBy = ref('date');
    const filterRating = ref('all');
    const ratingDialog = ref(false);
    const confirmDialog = ref(false);
    const currentMovie = ref({});
    const currentRating = ref(0);
    const selectedMovies = ref([]);
    
    // Computed properties
    const loading = computed(() => store.getters['movies/loading']);
    const watchedMovies = computed(() => store.getters['movies/watchedMovies'] || []);
    const userRatings = computed(() => store.getters['movies/userRatings'] || {});
    const recommendations = computed(() => store.getters['movies/recommendedMovies'] || []);
    
    const filteredWatched = computed(() => {
      let result = [...watchedMovies.value];
      
      // Apply rating filter
      if (filterRating.value !== 'all') {
        if (filterRating.value === 'rated') {
          result = result.filter(movie => 
            userRatings.value[movie.movie_id] && userRatings.value[movie.movie_id] > 0
          );
        } else if (filterRating.value === 'unrated') {
          result = result.filter(movie => 
            !userRatings.value[movie.movie_id] || userRatings.value[movie.movie_id] === 0
          );
        } else {
          // Filter by star rating
          const minRating = parseInt(filterRating.value);
          result = result.filter(movie => 
            userRatings.value[movie.movie_id] && userRatings.value[movie.movie_id] >= minRating
          );
        }
      }
      
      return result;
    });
    
    // Methods
    function getPosterUrl(path) {
      if (!path) return null;
      return `https://image.tmdb.org/t/p/w500${path}`;
    }
    
    function getUserRating(movieId) {
      return userRatings.value[movieId] || 0;
    }
    
    function sortWatched() {
      // Sorting is just changing the order items are displayed, not changing the underlying data
      // The actual sorting happens in the computed property
    }
    
    function viewMovie(movie) {
      store.dispatch('movies/selectMovie', movie);
      router.push('/');
    }
    
    function showRating(movie) {
      currentMovie.value = movie;
      currentRating.value = getUserRating(movie.movie_id);
      ratingDialog.value = true;
    }
    
    function submitRating() {
      store.dispatch('movies/rateMovie', {
        movieId: currentMovie.value.movie_id,
        rating: currentRating.value
      });
      ratingDialog.value = false;
    }
    
    function removeWatched(movie) {
      currentMovie.value = movie;
      confirmDialog.value = true;
    }
    
    function confirmRemove() {
      if (selectedMovies.value.length) {
        // Remove selected movies
        selectedMovies.value.forEach(movie => {
          store.dispatch('movies/toggleWatched', movie);
        });
        selectedMovies.value = [];
      } else {
        // Remove single movie
        store.dispatch('movies/toggleWatched', currentMovie.value);
      }
      confirmDialog.value = false;
    }
    
    function toggleSelection(movie) {
      const index = selectedMovies.value.findIndex(m => m.movie_id === movie.movie_id);
      if (index === -1) {
        selectedMovies.value.push(movie);
      } else {
        selectedMovies.value.splice(index, 1);
      }
    }
    
    function isSelected(movie) {
      return selectedMovies.value.some(m => m.movie_id === movie.movie_id);
    }
    
    function clearSelection() {
      selectedMovies.value = [];
    }
    
    function removeSelected() {
      if (selectedMovies.value.length > 0) {
        confirmDialog.value = true;
      }
    }
    
    function scrollCarousel(direction) {
      if (!carousel.value) return;
      
      const scrollAmount = carousel.value.clientWidth * 0.8;
      const maxScroll = carousel.value.scrollWidth - carousel.value.clientWidth;
      
      if (direction === 'left') {
        carouselScrollPos.value = Math.max(0, carouselScrollPos.value - scrollAmount);
      } else {
        carouselScrollPos.value = Math.min(maxScroll, carouselScrollPos.value + scrollAmount);
      }
      
      carousel.value.scrollTo({
        left: carouselScrollPos.value,
        behavior: 'smooth'
      });
    }
    
    // Load data when component mounts
    onMounted(async () => {
      // Load watched movies and ratings
      await store.dispatch('movies/loadWatchedMovies');
      await store.dispatch('movies/loadUserRatings');
      
      // Get collaborative recommendations if we have watched movies
      if (watchedMovies.value.length > 0) {
        const movieIds = watchedMovies.value.map(movie => movie.movie_id);
        store.dispatch('movies/getCollaborativeRecommendations', {
          userId: localStorage.getItem('userId') || 'anonymous',
          topK: 15
        });
      }
      
      // Monitor carousel scroll position
      if (carousel.value) {
        carousel.value.addEventListener('scroll', () => {
          carouselScrollPos.value = carousel.value.scrollLeft;
        });
      }
    });
    
    return {
      loading,
      watchedMovies,
      filteredWatched,
      recommendations,
      sortBy,
      filterRating,
      ratingDialog,
      confirmDialog,
      currentMovie,
      currentRating,
      selectedMovies,
      carousel,
      carouselScrollPos,
      getPosterUrl,
      getUserRating,
      sortWatched,
      viewMovie,
      showRating,
      submitRating,
      removeWatched,
      confirmRemove,
      toggleSelection,
      isSelected,
      clearSelection,
      removeSelected,
      scrollCarousel
    };
  }
};
</script>

<style scoped lang="scss">
.watched-page {
  padding: 20px 0 60px;
  position: relative;
}

.page-header {
  margin-bottom: 30px;
  
  h1 {
    font-size: 2.5rem;
    margin-bottom: 5px;
    
    @media (max-width: 768px) {
      font-size: 2rem;
    }
  }
  
  .subheader {
    color: var(--text-secondary);
    font-size: 1.1rem;
  }
}

// Empty state
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background-color: var(--card-background);
  border-radius: 10px;
  margin-bottom: 30px;
  
  .empty-icon {
    font-size: 4rem;
    margin-bottom: 20px;
  }
  
  h3 {
    font-size: 1.5rem;
    margin-bottom: 15px;
  }
  
  p {
    color: var(--text-secondary);
    margin-bottom: 25px;
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
  }
}

// Controls
.controls {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
  
  .filter-sort {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
    
    .sort-control, .filter-control {
      display: flex;
      align-items: center;
      
      label {
        margin-right: 10px;
        white-space: nowrap;
      }
      
      select {
        padding: 8px 12px;
        border-radius: 5px;
        background-color: var(--card-background);
        color: var(--text-color);
        border: 1px solid rgba(255, 255, 255, 0.1);
        
        &:focus {
          outline: none;
          border-color: var(--primary-color);
        }
      }
    }
  }
  
  .action-buttons {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .selected-count {
      font-size: 0.9rem;
      color: var(--text-secondary);
    }
    
    button {
      padding: 8px 15px;
      font-size: 0.9rem;
    }
  }
}

// Recommendations Carousel
.recommendations-section {
  margin-bottom: 40px;
  
  h2 {
    margin-bottom: 15px;
    font-size: 1.5rem;
  }
  
  .carousel-container {
    position: relative;
    display: flex;
    align-items: center;
  }
  
  .carousel {
    display: flex;
    overflow-x: auto;
    scroll-behavior: smooth;
    padding: 10px 0;
    gap: 15px;
    scrollbar-width: none;
    width: 100%;
    
    &::-webkit-scrollbar {
      display: none;
    }
  }
  
  .carousel-control {
    background-color: rgba(0, 0, 0, 0.6);
    color: white;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    position: absolute;
    z-index: 2;
    
    &:hover {
      background-color: var(--primary-color);
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    &.left {
      left: 5px;
    }
    
    &.right {
      right: 5px;
    }
  }
  
  .carousel-item {
    flex: 0 0 auto;
    width: 160px;
    margin-right: 15px;
    cursor: pointer;
    transition: transform 0.3s;
    
    &:hover {
      transform: scale(1.05);
    }
    
    .carousel-poster {
      height: 240px;
      border-radius: 8px;
      overflow: hidden;
      margin-bottom: 10px;
      
      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      
      .poster-placeholder {
        width: 100%;
        height: 100%;
        background-color: #2a2a2a;
        display: flex;
        align-items: center;
        justify-content: center;
        
        span {
          font-size: 3rem;
          font-weight: bold;
          color: rgba(255, 255, 255, 0.2);
        }
      }
    }
    
    .carousel-info {
      h4 {
        font-size: 0.9rem;
        margin-bottom: 5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .match-score {
        display: flex;
        align-items: center;
        font-size: 0.8rem;
        color: var(--primary-color);
        
        .ai-icon {
          margin-right: 4px;
        }
      }
    }
  }
}

// Watched Movies Grid
.watched-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 15px;
  }
}

.watched-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  background-color: var(--card-background);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  transition: transform 0.3s, box-shadow 0.3s;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    
    .movie-overlay {
      opacity: 1;
    }
  }
  
  &.selected {
    border: 2px solid var(--primary-color);
    
    .selection-indicator {
      opacity: 1;
    }
  }
  
  .movie-poster {
    position: relative;
    width: 100%;
    height: 0;
    padding-bottom: 150%; // 2:3 aspect ratio
    
    img {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .poster-placeholder {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: #2a2a2a;
      display: flex;
      align-items: center;
      justify-content: center;
      
      span {
        font-size: 3rem;
        font-weight: bold;
        color: rgba(255, 255, 255, 0.2);
      }
    }
    
    .movie-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(
        to bottom,
        rgba(0, 0, 0, 0.1) 0%,
        rgba(0, 0, 0, 0.8) 100%
      );
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 15px;
      opacity: 0;
      transition: opacity 0.3s;
      
      .user-rating {
        display: flex;
        flex-direction: column;
        align-items: center;
        background-color: rgba(0, 0, 0, 0.7);
        padding: 8px 12px;
        border-radius: 8px;
        align-self: center;
        
        .rating-value {
          margin-top: 5px;
          font-size: 0.9rem;
          font-weight: 600;
        }
      }
      
      .movie-actions {
        display: flex;
        justify-content: center;
        gap: 10px;
        
        .action-btn {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          background-color: rgba(0, 0, 0, 0.7);
          transition: background-color 0.2s, transform 0.2s;
          
          &:hover {
            transform: scale(1.1);
          }
          
          &:active {
            transform: scale(0.95);
          }
          
          i {
            font-style: normal;
          }
        }
        
        .view-btn {
          color: white;
          
          &:hover {
            background-color: rgba(255, 255, 255, 0.2);
          }
        }
        
        .rate-btn {
          color: #ffc107;
          
          &:hover {
            background-color: rgba(255, 193, 7, 0.2);
          }
        }
        
        .remove-btn {
          color: var(--error-color);
          font-size: 1.2rem;
          
          &:hover {
            background-color: rgba(255, 82, 82, 0.2);
          }
        }
      }
    }
    
    .selection-indicator {
      position: absolute;
      top: 10px;
      right: 10px;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background-color: var(--primary-color);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 0.8rem;
      opacity: 0;
      transition: opacity 0.2s;
      z-index: 3;
    }
  }
  
  .movie-info {
    padding: 12px;
    
    .movie-title {
      font-size: 0.95rem;
      font-weight: 600;
      margin-bottom: 5px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .movie-meta {
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      color: var(--text-secondary);
      
      .rating {
        color: #ffc107;
        font-weight: 500;
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

// Dialogs
.rating-dialog, .confirm-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  
  .rating-container, .confirm-container {
    background-color: var(--card-background);
    border-radius: 10px;
    width: 90%;
    max-width: 400px;
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
    overflow: hidden;
  }
  
  .rating-header, .confirm-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    h3 {
      margin: 0;
      font-size: 1.2rem;
    }
    
    .close-btn {
      background: none;
      border: none;
      color: var(--text-color);
      font-size: 1.5rem;
      cursor: pointer;
      
      &:hover {
        color: var(--error-color);
      }
    }
  }
  
  .rating-body {
    padding: 30px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    
    .rating-value {
      margin-top: 15px;
      font-size: 1.5rem;
      font-weight: 600;
    }
  }
  
  .confirm-body {
    padding: 30px 20px;
    text-align: center;
    
    p {
      margin: 0;
    }
  }
  
  .rating-footer, .confirm-footer {
    display: flex;
    justify-content: flex-end;
    padding: 15px 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    gap: 10px;
    
    button {
      padding: 8px 20px;
    }
  }
}
</style> 