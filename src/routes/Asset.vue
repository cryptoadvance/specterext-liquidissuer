<template>
  <main>
    <div class="summary">
      <router-link to="/assets/asset-uid">LGOO – Liquid Goo</router-link><br>
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
      <div class="actions">
        <router-link to="./dashboard/">Dashboard</router-link>
        <router-link to="./assignments/">Assignments</router-link>
        <router-link to="./distributions/">Distributions</router-link>
        <router-link to="./activities/">Activities</router-link>
        <router-link to="./utxos/">UTXOs</router-link>
        <router-link to="./users/">Users</router-link>
      </div>
    </div>
    <hr/>

    <div class="inner">
      <h1>Uncomplete distributions – 3</h1>
      <div class="small tight-top">Select distributions from the list to sign and broadcast</div>
    </div>
    <table class="table">
      <thead><tr>
        <th>ID</th>
        <th>Status</th>
        <th>Amount</th>
        <th>Transactions</th>
        <th>Users</th>
      </tr></thead>
      <tbody>
        <tr>
          <td>123456</td>
          <td>Draft</td>
          <td>321.38</td>
          <td>1</td>
          <td>3</td>
        </tr>
      </tbody>
    </table>

    <div class="inner">
      <h1>Pending assignments – 2</h1>
      <div class="small tight-top">Select assignments from the list to create a new distribution</div>
    </div>
    <table class="table">
      <thead><tr>
        <th>ID</th>
        <th>Status</th>
        <th>Amount</th>
        <th>Transactions</th>
        <th>Users</th>
      </tr></thead>
      <tbody>
        <tr>
          <td>123456</td>
          <td>Draft</td>
          <td>321.38</td>
          <td>1</td>
          <td>3</td>
        </tr>
      </tbody>
    </table>
  </main>
</template>