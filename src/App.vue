<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  /*color: #2c3e50;*/
  margin: auto;
  width: 100%;
  max-width: 1000px;
  margin-top: 60px;
}
</style>

<template>
  <div id="app">
    <h1>Amp issuer</h1>
    <nav class="row center">
      <router-link to="/" class="btn radio left">Dashboard</router-link>
      <router-link to="/assets" class="btn radio">Assets</router-link>
      <router-link to="/categories" class="btn radio">Categories</router-link>
      <router-link to="/users" class="btn radio">Users</router-link>
      <router-link to="/managers" class="btn radio right">Managers</router-link>
    </nav>
    <router-view/>
  </div>
</template>

<script>

export default {
  name: 'App',
  data() {
    return {}
  },
  components: {
  },
}
</script>
