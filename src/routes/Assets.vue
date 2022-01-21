<template>
  <main>
    <div class="table-holder">
      <router-link to="/new_asset" class="btn" style="max-width: 180px;margin-left:auto;">
        <svg width="20" height="20" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"></path></svg>
        Add new asset
      </router-link>
    </div>
    <br>
    <div class="table-holder">
      <table>
        <thead>
			<tr><th>Ticker</th><th>Name</th><th>Asset ID</th><th>Requirements</th></tr>
        </thead>
        <tbody>
          <tr v-if="!loaded"><td colspan="4">Loading...</td></tr>
          <tr v-if="loaded && !Object.keys(assets).length"><td colspan="4">No assets</td></tr>
          <tr v-for="(ass, i) in assets" :key="i">
            <td>{{ass.ticker}}</td><td>{{ass.name}}</td><td>{{ass.asset_id}}</td><td>{{ass.requirements.length}}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>

<script>

export default {
  name: 'Assets',
  data() {
    return {
    }
  },
  computed: {
    assets () {
      let aids = Object.keys(this.$store.state.assets).sort();
      return aids.map((aid) => this.$store.state.assets[aid]);
    },
    loaded(){
      return this.$store.state.loaded;
    }
  },
}
</script>