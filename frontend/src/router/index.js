import { createRouter, createWebHistory } from 'vue-router';
import store from '@/store';

// Lazy-loaded components
const Home = () => import('../views/Home.vue');
const Search = () => import('../views/Search.vue');
const Login = () => import('../views/Login.vue');
const Register = () => import('../views/Register.vue');
const Profile = () => import('../views/Profile.vue');
const Favorites = () => import('../views/Favorites.vue');
const MovieDetail = () => import('../views/MovieDetail.vue');

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { requiresAuth: true }
  },
  {
    path: '/search',
    name: 'Search',
    component: Search,
    meta: { requiresAuth: true }
  },
  {
    path: '/movie/:id',
    name: 'MovieDetail',
    component: MovieDetail,
    meta: { requiresAuth: true },
    props: true
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: Favorites,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresAuth: false }
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated'];
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'Login' });
  } else if (!to.meta.requiresAuth && isAuthenticated) {
    next({ name: 'Home' });
  } else {
    next();
  }
});

export default router; 