<template>
  <main>
    <div class="table-holder">
      <router-link to="/new_manager" class="btn" style="max-width: 180px;margin-left:auto;">
        <svg width="20" height="20" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"></path></svg>
        Add new manager
      </router-link>
    </div>
    <br>
    <div class="table-holder">
      <table>
        <thead>
          <tr><th>ID</th><th>Username</th><th>Assets</th></tr>
        </thead>
        <tbody>
          <tr v-if="!loaded"><td colspan="3">Loading...</td></tr>
          <tr v-if="loaded && !Object.keys(managers).length"><td colspan="3">No managers</td></tr>
          <tr v-for="(manager, i) in managers" :key="i">
            <td>{{manager.id}}</td><td>{{manager.username}}</td><td>{{manager.assets.length}}</td>
          </tr>

        </tbody>
      </table>
    </div>
  </main>
</template>

<script>
/*
  {
    "username": "string",
    "id": 0,
    "is_locked": true,
    "assets": [
      "string"
    ]
  }
*/

export default {
  name: 'Managers',
  data() {
    return {
    }
  },
  computed: {
    managers () {
      let uids = Object.keys(this.$store.state.managers).sort();
      return uids.map((uid) => this.$store.state.managers[uid]);
    },
    loaded(){
      return this.$store.state.loaded;
    },
  },
}
</script>