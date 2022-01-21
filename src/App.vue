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
    <h1>{{title}}</h1>
    <nav-bar/>
    <router-view/>
  </div>
</template>

<script>

export default {
  name: 'App',
  data() {
    return {
      title: '',
    }
  },
  watch: {
    $route: {
      immediate: true,
      handler(to) {
        document.title = `Amp issuer - ${to.name}`;
        this.title = to.name;
      }
    },
  },
}
</script>
