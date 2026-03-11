<template>
  <router-view @login-success="handleLoginSuccess" />
</template>

<script setup>
import { provide, ref, onMounted } from 'vue';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8003';

const isLoggedIn = ref(false);
const username = ref('');
const isAdmin = ref(localStorage.getItem('is_admin') === 'true');

const checkLoginStatus = async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    isLoggedIn.value = false;
    username.value = '';
    isAdmin.value = false;
    return;
  }

  try {
    const response = await axios.get(`${API_BASE_URL}/user`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    isLoggedIn.value = response.data.logged_in;
    username.value = response.data.username || '';
    isAdmin.value = response.data.is_admin || false;
  } catch (error) {
    console.error('检查登录状态失败:', error);
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('is_admin');
    isLoggedIn.value = false;
    username.value = '';
    isAdmin.value = false;
  }
};

const handleLoginSuccess = (userData) => {
  isLoggedIn.value = true;
  username.value = userData.username;
  isAdmin.value = userData.is_admin;
  localStorage.setItem('username', userData.username);
  localStorage.setItem('is_admin', userData.is_admin);
};

const logout = async () => {
  const token = localStorage.getItem('token');
  if (token) {
    try {
      await axios.post(`${API_BASE_URL}/logout`, {}, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
    } catch (error) {
      console.error('退出登录失败:', error);
    }
  }
  
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  localStorage.removeItem('is_admin');
  isLoggedIn.value = false;
  username.value = '';
  isAdmin.value = false;
};

provide('auth', {
  isLoggedIn,
  username,
  isAdmin,
  checkLoginStatus,
  logout
});

onMounted(() => {
  checkLoginStatus();
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f5f5f5;
  color: #333;
  line-height: 1.6;
}
</style>
