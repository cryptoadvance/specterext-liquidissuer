<template>
  <nav class="side">
    <router-link to="/" class="logo">
      <div class="menu-icon">
        <img src="img/blockstream_logo.png"/>
      </div>
      <div class="menu-body">
        Blockstream.info<br>
        <small>1670906 blocks</small>
      </div>
    </router-link>
    <router-link to="/assets/">
      <div class="menu-icon">
        <img src="img/asset.svg"/>
      </div>
      <div class="menu-body">
        Assets<br>
        <small>2 assets</small>
      </div>
    </router-link>
<!--     <div class="submenu">
      <a href="#">
        <div>LGOO</div>
        <div>Liquid Goo</div>
      </a>
      <a href="#">
        <div>L-DIY</div>
        <div>Specter-DIY preorder</div>
      </a>
    </div>
 -->
    <router-link to="/categories/">
      <div class="menu-icon">
        <img src="img/category.svg"/>
      </div>
      <div class="menu-body">
        Categories<br>
        <small>2 categories</small>
      </div>
    </router-link>
    <router-link to="/users/">
      <div class="menu-icon">
        <img src="img/users.svg"/>
      </div>
      <div class="menu-body">
        Users<br>
        <small>73 users</small>
      </div>
    </router-link>
    <router-link to="/managers/">
      <div class="menu-icon">
        <img src="img/managers.svg"/>
      </div>
      <div class="menu-body">
        Managers<br>
        <small>0 managers</small>
      </div>
    </router-link>
    <router-link to="/treasury/">
      <div class="menu-icon">
        <img src="img/treasury.svg"/>
      </div>
      <div class="menu-body">
        Treasury<br>
        <small>2 wallets</small>
      </div>
    </router-link>
    <div class="spacer"></div>
    <router-link to="/settings/">
      <div class="menu-icon">
        <img src="img/settings.svg"/>
      </div>
      <div class="menu-body">
        Settings<br>
        <small>Amp issuer v0.1</small>
      </div>
    </router-link>
  </nav>
 </template>
