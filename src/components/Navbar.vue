<style scoped>
  nav{
    margin-bottom: 50px;
  }
</style>

<template>
  <nav class="row center">
    <router-link to="/" class="btn radio left">Dashboard</router-link>
    <router-link to="/assets" class="btn radio">Assets</router-link>
    <router-link to="/categories" class="btn radio">Categories</router-link>
    <router-link to="/users" class="btn radio">Users</router-link>
    <router-link to="/managers" class="btn radio right">Managers</router-link>
  </nav>
</template>
