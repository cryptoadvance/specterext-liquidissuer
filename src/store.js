import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

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
  }
});