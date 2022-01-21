<template>
  <main>
    <div class="table-holder">
      <router-link to="/new_user" class="btn" style="max-width: 180px;margin-left:auto;">
        <svg width="20" height="20" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"></path></svg>
        Add new user
      </router-link>
    </div>
    <br>
    <div class="table-holder">
      <table>
        <thead>
          <tr><th>ID</th><th>Name</th><th>GAID</th></tr>
        </thead>
        <tbody>
          <tr v-if="!loaded"><td colspan="3">Loading...</td></tr>
          <tr v-if="loaded && !Object.keys(users).length"><td colspan="3">No registered users</td></tr>
          <tr v-for="(user, i) in users" :key="i" @click="selectUser(user.id)">
            <td>{{user.id}}</td><td>{{user.name}}</td><td>{{user.GAID}}</td>
          </tr>

        </tbody>
      </table>
    </div>
  </main>
</template>

<script>

export default {
  name: 'Users',
  data() {
    return {
    }
  },
  methods: {
    selectUser(uid){
      console.log(this.$store.state.users[uid]);
      this.$router.push(`/user/${uid}`);
    },
  },
  computed: {
    users () {
      let uids = Object.keys(this.$store.state.users).sort();
      return uids.map((uid) => this.$store.state.users[uid]);
    },
    loaded(){
      return this.$store.state.loaded;
    }
  },
}
</script>