<style>
#app {
}
</style>

<template>
  <div id="app">
    <side-bar/>
    <router-view/>
  </div>
</template>

<script>

export default {
  name: 'App',
  data() {
    return {
    }
  },
  watch: {
    $route: {
      immediate: true,
      handler(to) {
        document.title = `Amp issuer - ${to.name}`;
        this.title = to.name;
      },
    },
  },
}
</script>
