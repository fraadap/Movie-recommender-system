<template>
  <footer class="footer-bar">
    <div class="footer-content">
      <span class="copyright">&copy; {{ currentYear }} MovieMatcher. Tutti i diritti riservati.</span>
      <span class="version">v1.0.0</span>
    </div>
  </footer>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'FooterBar',
  setup() {
    const currentYear = ref(new Date().getFullYear())
    return { currentYear }
  }
}
</script>

<style lang="scss" scoped>
.footer-bar {
  height: var(--footer-height);
  background-color: var(--bg-color-light);
  border-top: 1px solid var(--border-color);
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-color-light);
  font-size: 0.8rem;
  transition: background-color var(--transition-speed);
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: var(--content-width, 1200px);
  
  .copyright {
    // Add styles if needed
  }
  
  .version {
    font-weight: 500;
  }
}
</style> 