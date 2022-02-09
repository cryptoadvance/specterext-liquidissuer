<template>
  <main>
    <div class="row inner">
      <h1>Assets</h1>
      <a class="btn tight-right" href="#"><img src="img/add.svg"/> New asset</a>
    </div>
    <div class="summary">
      <router-link to="/assets/asset-uid/">LGOO – Liquid Goo</router-link><br>
      <small>Asset Id: e3304b5cb8157f406635e8bd4215d4a109a5e4cdf26d3dfa5fc6e74dfe72be7f</small>
      <hr/>
      <div class="row even">
        <div>
          <h2>General information</h2>
          <table class="labeled">
            <tr><td>Type:</td><td>transfer restricted</td></tr>
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
        <a href="#">Dashboard</a>
        <a href="#">Assignments</a>
        <a href="#">Distributions</a>
        <a href="#">History</a>
      </div>
    </div>
    <hr/>
    <div class="summary">
      <a href="#">L-DIY – Specter-DIY preorders</a><br>
      <small>Asset Id: e3304b5cb8157f406635e8bd4215d4a109a5e4cdf26d3dfa5fc6e74dfe72be7f</small>
      <hr/>
      <div class="row even">
        <div>
          <h2>General information</h2>
          <table class="labeled">
            <tr><td>Type:</td><td>trackable</td></tr>
            <tr><td>Status:</td><td>locked</td></tr>
            <tr><td>Requirements:</td><td><a href="#" class="tag">verified</a></td></tr>
            <tr><td>Treasury:</td><td>Specter Multisig (2 of 3)</td></tr>
          </table>
        </div>
        <div>
          <h2>Blockchain information</h2>
          <table class="labeled">
            <tr><td>Issued total:</td><td>1 000</td></tr>
            <tr><td>Reissuance:</td><td>1</td></tr>
            <tr><td>Owners:</td><td>156 users, 183 distributed</td></tr>
            <tr><td>Locked UTXOs:</td><td>0</td></tr>
          </table>
        </div>
        <div>
          <h2>AMP actions</h2>
          <table class="labeled">
            <tr><td>Assignments:</td><td>1 pending, 157 total</td></tr>
            <tr><td>Distributions:</td><td>103 total</td></tr>
            <tr><td>Lost UTXOs:</td><td>0</td></tr>
          </table>
        </div>
      </div>
      <hr/>
      <div class="actions right">
        <a href="#">Dashboard</a>
        <a href="#">Assignments</a>
        <a href="#">Distributions</a>
        <a href="#">History</a>
      </div>
    </div>
  </main>
</template>

<script>

export default {
  data () {
    return {
      loading: false,
      error: null,
    }
  },
  created () {
    // fetch the data when the view is created and the data is
    // already being observed
    this.fetchData()
  },
  watch: {
    // call again the method if the route changes
    '$route': 'fetchData'
  },
  methods: {
    fetchData () {
      // check we can fetch data
      if(window.amp.loginRequired){
        this.$router.push("/login");
      }
      // this.error = this.post = null
      // this.loading = true
      // const fetchedId = this.$route.params.id
      // // replace `getPost` with your data fetching util / API wrapper
      // getPost(fetchedId, (err, post) => {
      //   // make sure this request is the last one we did, discard otherwise
      //   if (this.$route.params.id !== fetchedId) return
      //   this.loading = false
      //   if (err) {
      //     this.error = err.toString()
      //   } else {
      //     this.post = post
      //   }
      // })
    }
  }
}

</script>