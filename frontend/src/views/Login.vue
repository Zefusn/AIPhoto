<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-card">
        <h1 class="login-title">Luckymax</h1>
        <p class="login-subtitle">{{ isRegister ? '注册账户' : '登录账户' }}</p>
        
        <form @submit.prevent="handleSubmit" class="login-form">
          <div class="form-group">
            <input 
              type="text" 
              v-model="username" 
              placeholder="用户名"
              class="form-input"
              required
            />
          </div>
          <div class="form-group">
            <input 
              type="password" 
              v-model="password" 
              placeholder="密码"
              class="form-input"
              required
            />
          </div>
          
          <div class="error-message" v-if="error">
            {{ error }}
          </div>
          
          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? '处理中...' : (isRegister ? '注册' : '登录') }}
          </button>
        </form>
        
        <div class="switch-mode">
          <span>{{ isRegister ? '已有账户？' : '没有账户？' }}</span>
          <a href="#" @click.prevent="toggleMode">{{ isRegister ? '立即登录' : '立即注册' }}</a>
        </div>
        
        <div class="back-home">
          <router-link to="/">返回首页</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const API_BASE_URL = '/api';

const username = ref('');
const password = ref('');
const isRegister = ref(false);
const isLoading = ref(false);
const error = ref('');

const emit = defineEmits(['login-success']);

const toggleMode = () => {
  isRegister.value = !isRegister.value;
  error.value = '';
};

const handleSubmit = async () => {
  error.value = '';
  isLoading.value = true;
  
  try {
    if (isRegister.value) {
      const formData = new FormData();
      formData.append('username', username.value);
      formData.append('password', password.value);
      
      const response = await axios.post(`${API_BASE_URL}/register`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      alert('注册成功，请登录');
      isRegister.value = false;
    } else {
      const formData = new FormData();
      formData.append('username', username.value);
      formData.append('password', password.value);
      
      const response = await axios.post(`${API_BASE_URL}/login`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('username', response.data.username);
      localStorage.setItem('is_admin', response.data.is_admin);
      
      emit('login-success', {
        username: response.data.username,
        is_admin: response.data.is_admin
      });
      
      router.push('/');
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '操作失败，请重试';
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9f9f9;
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 400px;
}

.login-card {
  background: #f5f5f5;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 
    12px 12px 24px rgba(0, 0, 0, 0.08),
    -12px -12px 24px rgba(255, 255, 255, 0.9);
}

.login-title {
  text-align: center;
  font-size: 2rem;
  font-weight: 700;
  color: #000;
  margin: 0 0 10px 0;
}

.login-subtitle {
  text-align: center;
  font-size: 1rem;
  color: #666;
  margin: 0 0 30px 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  width: 100%;
}

.form-input {
  width: 100%;
  padding: 15px 20px;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  color: #333;
  background: #f0f0f0;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.05),
    inset -4px -4px 8px rgba(255, 255, 255, 0.8);
  outline: none;
  transition: all 0.3s ease;
}

.form-input:focus {
  box-shadow: 
    inset 6px 6px 12px rgba(0, 0, 0, 0.08),
    inset -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.form-input::placeholder {
  color: #999;
}

.error-message {
  color: #f44336;
  font-size: 0.9rem;
  text-align: center;
  padding: 10px;
}

.submit-btn {
  width: 100%;
  padding: 15px;
  background: #000;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.2),
    -4px -4px 8px rgba(255, 255, 255, 0.1);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -6px -6px 12px rgba(255, 255, 255, 0.15);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.switch-mode {
  text-align: center;
  margin-top: 25px;
  font-size: 0.9rem;
  color: #666;
}

.switch-mode a {
  color: #000;
  text-decoration: none;
  font-weight: 500;
  margin-left: 5px;
}

.switch-mode a:hover {
  text-decoration: underline;
}

.back-home {
  text-align: center;
  margin-top: 20px;
}

.back-home a {
  color: #666;
  text-decoration: none;
  font-size: 0.9rem;
}

.back-home a:hover {
  text-decoration: underline;
}
</style>
