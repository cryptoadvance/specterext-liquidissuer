import Vue from 'vue';
import VueRouter from 'vue-router';
import App from './App.vue';
import Login from './routes/Login';
import Dashboard from './routes/Dashboard';

Vue.config.productionTip = false;
Vue.use(VueRouter);

const routes = [
  { "path": "/", "component": Dashboard },
  { "path": "/login", "component": Login },
];

const router = new VueRouter({routes});

new Vue({
  render: h => h(App),
  router,
}).$mount('#app');
