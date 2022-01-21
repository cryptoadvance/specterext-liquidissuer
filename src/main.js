import Vue from 'vue';
import VueRouter from 'vue-router';
import App from './App.vue';
import Login from './routes/Login';
import Dashboard from './routes/Dashboard';
import Assets from './routes/Assets';
import Users from './routes/Users';
import Categories from './routes/Categories';

// remove for production api
const SUFFIX = ".json"; // for static data
const API = "/api";
const TOKEN = "";

class Amp {
  constructor(api, token=null){
    this.api = api;
    this._data = {
      users: {},
      assets: {},
      categories: {},
      managers: {},
    }
    if(token){
      this.login(token)
    }
  }
  async login(token){
    this.token = token;
    let [users, assets, categories] = await Promise.all([
      fetch(`${this.api}/registered_users${SUFFIX}`),
      fetch(`${this.api}/assets${SUFFIX}`),
      fetch(`${this.api}/categories${SUFFIX}`),
    ]);
    // from list to dict conversion
    users.forEach((user)=>{
      this._data.users[user.id] = user;
    });
    assets.forEach((asset)=>{
      this._data.assets[asset.asset_uuid] = asset;
    });
    categories.forEach((category) => {
      this._data.categories[category.id] = category;
    });

  }
  get loginRequired(){
    return (this.token == null);
  }
  get users(){
    return this._data.users;
  }
}
window.amp = new Amp(API, TOKEN);

Vue.config.productionTip = false;
Vue.use(VueRouter);

const routes = [
  { "path": "/", "component": Dashboard },
  { "path": "/login", "component": Login },
  { "path": "/users", "component": Users },
  { "path": "/categories", "component": Categories },
  { "path": "/assets", "component": Assets },
];

const router = new VueRouter({routes});

new Vue({
  render: h => h(App),
  router,
}).$mount('#app');
