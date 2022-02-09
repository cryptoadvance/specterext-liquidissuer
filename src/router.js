import Vue from 'vue';
import VueRouter from 'vue-router';

import Login from './routes/Login';
import Dashboard from './routes/Dashboard';
import Assets from './routes/Assets';
import Asset from './routes/Asset';
import Users from './routes/Users';
import Categories from './routes/Categories';
import Managers from './routes/Managers';
import User from './routes/User';

Vue.use(VueRouter);

const routes = [
  { "path": "/", "component": Dashboard, "name": "Dashboard" },
  { "path": "/login", "component": Login, "name": "Login" },
  { "path": "/users", "component": Users, "name": "Users" },
  { "path": "/categories", "component": Categories, "name": "Categories" },
  { "path": "/assets", "component": Assets, "name": "Assets" },
  { "path": "/assets/:auid", "component": Asset, "name": "Asset" },
  { "path": "/managers", "component": Managers, "name": "Managers" },
  { "path": "/user/:userId", "component": User, "name": "User details" },
];

export const router = new VueRouter({routes});