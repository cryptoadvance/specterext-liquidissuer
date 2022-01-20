<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>

<template>
  <div id="app">
    <img alt="Vue logo" src="./assets/logo.png">
    <router-link to="/login">Login</router-link>
    <router-link to="/">Dashboard</router-link>
    <router-view/>
    <hello-world msg="Welcome to Your Vue.js App"/>
  </div>
</template>

<script>
import HelloWorld from './components/HelloWorld.vue';

export default {
  name: 'App',
  data() {
    return {
      amp: {
        users: [],
        assets: [],
        categories: [],
        managers: [],
      },
    }
  },
  components: {
    'hello-world': HelloWorld
  },
}
</script>
