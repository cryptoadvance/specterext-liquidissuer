import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

const API = "http://localhost:8081/api";

export const store = new Vuex.Store({
  state: {
    users: {},
    categories: {},
    assets: {},
    managers: {},
    loaded: false,
  },
  mutations: {
    setUsers(state, users){
      if(!state.loaded){ state.loaded = true; }
      state.users = users;
    },
    setCategories(state, categories){
      if(!state.loaded){ state.loaded = true; }
      state.categories = categories;
    },
    setAssets(state, assets){
      if(!state.loaded){ state.loaded = true; }
      state.assets = assets;
    },
    setManagers(state, managers){
      if(!state.loaded){ state.loaded = true; }
      state.managers = managers;
    },
  },
  getters: {
    assetSummary: (state) => (asset_uuid) => {
      if(!(asset_uuid in state.assets)){
        return null;
      }
      let result = {};
      let info = state.assets[asset_uuid];
      Object.assign(result, info);
      Object.assign(result, {
        type: (info.transfer_restricted ? 'transfer restricted' : 'trackable'), 
      });
      return result;
    },
    assetsSummary: (state, getters) => () => {
      let aids = Object.keys(state.assets).sort();
      return aids.map((aid) => getters.assetSummary(aid));
    },
  },
  actions: {
    async init( { commit } ) {
      let [users, assets, categories, managers] = await Promise.all([
        fetch(`${API}/registered_users`),
        fetch(`${API}/assets`),
        fetch(`${API}/categories`),
        fetch(`${API}/managers`),
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
      commit('setUsers', u);
      commit('setCategories', c);
      commit('setAssets', a);
      commit('setManagers', m);
      console.log("synced");
    }
  }
});