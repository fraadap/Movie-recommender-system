import { createStore } from 'vuex';
import auth from './modules/auth';
import movies from './modules/movies';
import ui from './modules/ui';

export default createStore({
  modules: {
    auth,
    movies,
    ui
  }
}); 