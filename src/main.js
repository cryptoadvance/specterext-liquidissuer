import Vue from 'vue';
import VueRouter from 'vue-router';
import {store} from './store';
import {router} from './router';
import App from './App.vue';

/* Components */

// import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

// remove for production api
const API = "http://localhost:8081/api";
const TOKEN = "qwe";

class Amp {
  constructor(api, token=null){
    this.api = api;
    this.token = token;
  }
  get loginRequired(){
    return (this.token == null);
  }
}
window.amp = new Amp(API, TOKEN);

Vue.config.productionTip = false;
Vue.use(VueRouter);

Vue.component('side-bar', Sidebar);

window.app = new Vue({
  data: {
  },
  render: h => h(App),
  created(){
    store.dispatch('init');
  },
  methods: {
  },
  router,
  store,
}).$mount('#app');
