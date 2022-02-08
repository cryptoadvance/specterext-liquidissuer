import Vue from 'vue';
import VueRouter from 'vue-router';
import {store} from './store';

import App from './App.vue';
import Login from './routes/Login';
import Dashboard from './routes/Dashboard';
import Assets from './routes/Assets';
import Asset from './routes/Asset';
import Users from './routes/Users';
import Categories from './routes/Categories';
import Managers from './routes/Managers';
import User from './routes/User';


// import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

// remove for production api
const SUFFIX = ""; // for static data
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

const routes = [
  { "path": "/", "component": Dashboard, "name": "Dashboard" },
  { "path": "/login", "component": Login, "name": "Login" },
  { "path": "/users", "component": Users, "name": "Users" },
  { "path": "/categories", "component": Categories, "name": "Categories" },
  { "path": "/assets", "component": Assets, "name": "Assets" },
  { "path": "/assets/:auid", "component": Asset, "name": "Asset" },
  { "path": "/managers", "component": Managers, "name": "Managers" },
  { "path": "/user/:userId", "component": User, "name": "User details" },
];

const router = new VueRouter({routes});

Vue.component('side-bar', Sidebar);

window.app = new Vue({
  data: {
  },
  render: h => h(App),
  created(){
    this.sync();
  },
  methods: {
    async sync() {
      let [users, assets, categories, managers] = await Promise.all([
        fetch(`${API}/registered_users${SUFFIX}`),
        fetch(`${API}/assets${SUFFIX}`),
        fetch(`${API}/categories${SUFFIX}`),
        fetch(`${API}/managers${SUFFIX}`),
      ]);
      let u = {}; let a = {}; let c = {}; let m = {};
      // from list to dict conversion
      (await users.json()).forEach((user)=>{
        u[user.id] = user;
      });
      (await assets.json()).forEach((asset)=>{
        a[asset.asset_uuid] = asset;
      });
      (await categories.json()).forEach((category) => {
        c[category.id] = category;
      });
      (await managers.json()).forEach((manager) => {
        m[manager.id] = manager;
      });
      store.commit('setUsers', u);
      store.commit('setCategories', c);
      store.commit('setAssets', a);
      store.commit('setManagers', m);
      console.log("synced");
    },
  },
  router,
  store,
}).$mount('#app');
