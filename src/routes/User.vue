<template>
  <main>
    <div class="card" style="text-align: left;">
      <div>Name:</div>
      <div class="row"><input type="text" :value="user.name"/> &nbsp; <button class="btn">Save</button></div>
      <br>
      <div>User ID: <span>{{user.id}}</span></div>
      <div>Default GAID: <span>{{user.GAID}}</span></div>
      <br><br>
    </div>
  </main>
</template>

<script>

export default {
  name: 'User',
  data() {
    return {
      summary: {},
      gaids: [],
    }
  },
  computed: {
    uid () {
      return this.$route.params.userId;
    },
    user () {
      let uid = this.$route.params.userId;
      return this.$store.state.users[uid];
    },
  },
  created () {
    this.fetchData()
  },
  watch: {
    '$route': 'fetchData'
  },
  methods: {
    async fetchData () {
      let res = await fetch(`${window.amp.api}/registered_users/${this.uid}/summary`);
      this.summary = await res.json();
      res = await fetch(`${window.amp.api}/registered_users/${this.uid}/gaids`);
      this.gaids = await res.json();
      console.log(this.summary);
      console.log(this.gaids);
    },
  },
}
</script>