<template>
  <main>
    <h1>Users</h1>
    <div class="table-holder">
      <a style="max-width: 180px;margin-left:auto;" href="#/new_registered_user" class="btn">
        <svg width="20" height="20" viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"></path></svg>
        Add new user
      </a>
    </div>
    <br>
    <div class="table-holder">
      <table>
        <thead>
          <tr><th>ID</th><th>Name</th><th>GAID</th></tr>
        </thead>
        <tbody>
          <tr><td colspan="3">Loading...</td></tr>

<!--           <tr v-for="uid in Object.keys(users)">
            <td>{{uid}}</td><td>{{users[uid].name}}</td><td>{{users[uid].gaid}}</td>
          </tr>
 -->
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
      users: {},
    }
  },
}
</script>