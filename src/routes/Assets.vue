<template>
  <main>
    <div class="row inner">
      <h1>Assets</h1>
      <router-link class="btn tight-right" to="/new_asset/"><img src="img/add.svg"/> New asset</router-link>
    </div>
    <div v-if="!loaded">Loading...</div>

    <div class="summary" v-for="(ass, i) in assets" :key="i">
      <router-link :to="'/assets/'+ass.asset_uuid+'/'">{{ass.ticker}} – {{ass.name}}</router-link><br>
      <small>Asset Id: {{ass.asset_id}}</small>
      <hr/>
      <div class="row even">
        <div>
          <h2>General information</h2>
          <table class="labeled">
            <tr><td>Type:</td><td>{{ass.type}}</td></tr>
            <tr><td>Status:</td><td>active, registered, authorized</td></tr>
            <tr><td>Requirements:</td><td><a href="#" class="tag">kyced</a><a href="#" class="tag">verified</a></td></tr>
            <tr><td>Treasury:</td><td>Jade HW</td></tr>
          </table>
        </div>
        <div>
          <h2>Blockchain information</h2>
          <table class="labeled">
            <tr><td>Issued total:</td><td>21 000 000</td></tr>
            <tr><td>Reissuance:</td><td>1</td></tr>
            <tr><td>Owners:</td><td>56 users, 10 543 distributed</td></tr>
            <tr><td>Locked UTXOs:</td><td>7</td></tr>
          </table>
        </div>
        <div>
          <h2>AMP actions</h2>
          <table class="labeled">
            <tr><td>Assignments:</td><td>17 pending, 34 total</td></tr>
            <tr><td>Distributions:</td><td>3 unsigned, 12 total</td></tr>
            <tr><td>Lost UTXOs:</td><td>2</td></tr>
          </table>
        </div>
      </div>
      <hr/>
      <div class="actions right">
        <router-link :to="'/assets/'+ass.asset_uuid+'/dashboard/'">Dashboard</router-link>
        <router-link :to="'/assets/'+ass.asset_uuid+'/assignments/'">Assignments</router-link>
        <router-link :to="'/assets/'+ass.asset_uuid+'/distributions/'">Distributions</router-link>
        <router-link :to="'/assets/'+ass.asset_uuid+'/history/'">History</router-link>
      </div>
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
      return this.$store.getters.assetsSummary();
    },
    loaded(){
      return this.$store.state.loaded;
    }
  },
}
</script>