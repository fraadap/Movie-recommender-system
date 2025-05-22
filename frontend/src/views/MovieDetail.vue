<template>
  <div class="movie-detail-container">
    <MovieDetail />
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import MovieDetail from '@/components/MovieDetail.vue';

export default defineComponent({
  name: 'MovieDetailView',
  components: {
    MovieDetail
  }
});
</script>

<style scoped lang="scss">
.movie-detail-container {
  min-height: calc(100vh - 60px);
  background-color: #0a1929;
}
</style> 