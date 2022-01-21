<template>
  <main>
    <div class="table-holder">
      <router-link to="/new_category" class="btn" style="max-width: 180px;margin-left:auto;">
        <svg width="20" height="20" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"></path></svg>
        Add new category
      </router-link>
    </div>
    <br>
    <div class="table-holder">
      <table>
        <thead>
			<tr><th>ID</th><th>Name</th><th>Description</th><th>Assets</th><th>Investors</th><th>Users</th></tr>
        </thead>
        <tbody>
          <tr v-if="!loaded"><td colspan="6">Loading...</td></tr>
          <tr v-if="loaded && !Object.keys(categories).length"><td colspan="6">No categories</td></tr>
          <tr v-for="(cat, i) in categories" :key="i">
            <td>{{cat.id}}</td><td>{{cat.name}}</td><td>{{cat.description}}</td><td>{{cat.assets.length}}</td><td>{{cat.investors.length}}</td><td>{{cat.registered_users.length}}</td>
          </tr>

        </tbody>
      </table>
    </div>
  </main>
</template>

<script>

export default {
  name: 'Categories',
  data() {
    return {
    }
  },
  computed: {
    categories () {
      let cids = Object.keys(this.$store.state.categories).sort();
      return cids.map((cid) => this.$store.state.categories[cid]);
    },
    loaded(){
      return this.$store.state.loaded;
    }
  },
}
</script>