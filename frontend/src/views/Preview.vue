<template>
  <div class="preview-page">
    <!-- 导航栏 -->
    <header class="header">
      <div class="container">
        <div class="header-content">
          <h1 class="logo">Luckymax</h1>
          <div class="header-actions">
            <template v-if="auth.isLoggedIn.value">
              <div class="user-profile">
                <div class="user-avatar" @click="toggleUserMenu">
                  <span class="avatar-text">{{ auth.username.value.charAt(0).toUpperCase() }}</span>
                </div>
                <div class="user-menu" v-if="showUserMenu">
                  <span class="menu-username">{{ auth.username.value }}</span>
                  <button @click="handleLogout" class="menu-logout-btn">退出</button>
                </div>
              </div>
            </template>
            <template v-else>
              <router-link to="/login" class="login-btn">登录</router-link>
            </template>
            <router-link to="/" class="back-home-btn">返回首页</router-link>
          </div>
        </div>
      </div>
    </header>

    <!-- 图片预览区域 -->
    <section class="preview-section">
      <div class="container">
        <div class="preview-content" v-if="image">
          <!-- 左侧图片区域 -->
          <div class="image-container">
            <img 
              :src="`${API_BASE_URL}/thumbnail/${image.file_id}`" 
              :alt="image.display_name || image.original_filename"
              class="preview-image"
              @error="handleImageError"
            />
          </div>

          <!-- 右侧信息区域 -->
          <div class="info-container">
            <h2 class="image-title">{{ image.display_name || image.original_filename }}</h2>
            
            <div class="image-meta">
              <div class="meta-item">
                <span class="meta-label">分辨率：</span>
                <span class="meta-value">{{ image.resolution || '未知' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">文件大小：</span>
                <span class="meta-value">{{ image.size || '未知' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">分类：</span>
                <span class="meta-value">{{ image.category || '电脑' }}</span>
              </div>
            </div>

            <div class="action-buttons" v-if="auth.isLoggedIn.value">
              <button 
                @click="downloadOriginalImage(image.share_url)"
                class="action-btn download"
              >
                <span class="btn-icon">↓</span>
                下载原图
              </button>
              <button 
                class="action-btn share"
                @click="copyImageLink(image.share_url)"
              >
                <span class="btn-icon">↑</span>
                复制链接
              </button>
            </div>
            <div class="action-buttons" v-else>
              <p class="login-hint">登录后可下载和分享</p>
              <router-link to="/login" class="action-btn login-hint-btn">立即登录</router-link>
            </div>

            <div class="share-link-box" v-if="showCopiedMessage">
              <span class="copied-text">链接已复制！</span>
            </div>
          </div>
        </div>

        <!-- 加载中 -->
        <div class="loading-state" v-else>
          <div class="loading-spinner"></div>
          <p>加载中...</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, inject } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const auth = inject('auth', {
  isLoggedIn: ref(false),
  username: ref(''),
  isAdmin: ref(false),
  checkLoginStatus: async () => {},
  logout: async () => {}
});
const API_BASE_URL = '/api';

const image = ref(null);
const showCopiedMessage = ref(false);
const showUserMenu = ref(false);

// 切换用户菜单
const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value;
};

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  const userProfile = document.querySelector('.user-profile');
  if (userProfile && !userProfile.contains(event.target)) {
    showUserMenu.value = false;
  }
};

// 监听点击事件
onMounted(() => {
  fetchImageInfo();
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});

// 退出登录
const handleLogout = async () => {
  await auth.logout();
  router.push('/');
};

// 获取图片信息
const fetchImageInfo = async () => {
  const fileId = route.params.id;
  if (!fileId) {
    router.push('/');
    return;
  }

  try {
    const response = await axios.get(`${API_BASE_URL}/images`);
    const foundImage = response.data.images.find(img => img.file_id === fileId);
    
    if (foundImage) {
      image.value = {
        ...foundImage,
        category: foundImage.category || '电脑'
      };
    } else {
      router.push('/');
    }
  } catch (error) {
    console.error('获取图片信息失败:', error);
    router.push('/');
  }
};

// 复制图片链接
const copyImageLink = (shareUrl) => {
  const fullUrl = `${window.location.origin}${shareUrl}`;
  navigator.clipboard.writeText(fullUrl).then(() => {
    showCopiedMessage.value = true;
    setTimeout(() => {
      showCopiedMessage.value = false;
    }, 2000);
  });
};

// 下载原图
const downloadOriginalImage = async (shareUrl) => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API_BASE_URL}${shareUrl}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : ''
      },
      responseType: 'blob'
    });
    
    // 直接处理文件内容
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', image.value.original_filename || `image_${Date.now()}`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // 释放URL对象
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
    }, 100);
  } catch (error) {
    console.error('下载失败:', error);
    alert('下载失败：' + (error.response?.data?.detail || '未知错误'));
  }
};

// 处理图片加载错误
const handleImageError = (e) => {
  console.error('图片加载失败');
  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMTAwIiBjeT0iMTAwIiByPSIxMCIgZmlsbD0iI2U4ZThlOCIvPjx0ZXh0IHg9IjEwMCIgeT0iMTA1IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiM4ODgiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkltYWdlIFJlcG9ydDwvdGV4dD48L3N2Zz4=';
};

onMounted(() => {
  fetchImageInfo();
});
</script>

<style scoped>
/* 页面容器 */
.preview-page {
  min-height: 100vh;
  background: #f9f9f9;
}

/* 导航栏 */
.header {
  background: #f9f9f9;
  padding: 20px 0;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.05);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  font-size: 1.8rem;
  font-weight: 700;
  color: #000;
  margin: 0;
}

.header-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  font-weight: 500;
  color: #000;
  margin-right: 10px;
}

.logout-btn, .login-btn, .back-home-btn {
  display: inline-block;
  padding: 8px 16px;
  background: #f5f5f5;
  color: #000;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.08),
    -4px -4px 8px rgba(255, 255, 255, 0.9);
}

.logout-btn:hover, .login-btn:hover, .back-home-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.1),
    -6px -6px 12px rgba(255, 255, 255, 0.95);
}

/* 用户头像 */
.user-profile {
  position: relative;
  margin-right: 10px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.08),
    -4px -4px 8px rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
}

.user-avatar:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.1),
    -6px -6px 12px rgba(255, 255, 255, 0.95);
}

.avatar-text {
  font-weight: 600;
  color: #000;
  font-size: 1rem;
}

/* 用户菜单 */
.user-menu {
  position: absolute;
  top: 50px;
  right: 0;
  background: #f5f5f5;
  border-radius: 12px;
  padding: 15px;
  min-width: 180px;
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.1),
    -8px -8px 16px rgba(255, 255, 255, 0.9);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.menu-username {
  font-weight: 500;
  color: #000;
  text-align: center;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.menu-logout-btn {
  padding: 8px 16px;
  background: #f5f5f5;
  color: #000;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    2px 2px 4px rgba(0, 0, 0, 0.08),
    -2px -2px 4px rgba(255, 255, 255, 0.9);
}

.menu-logout-btn:hover {
  transform: translateY(-1px);
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.1),
    -4px -4px 8px rgba(255, 255, 255, 0.95);
}

/* 预览区域 */
.preview-section {
  padding: 40px 0;
  min-height: calc(100vh - 100px);
}

.preview-content {
  display: flex;
  gap: 40px;
  background: #f5f5f5;
  border-radius: 16px;
  padding: 30px;
  box-shadow: 
    12px 12px 24px rgba(0, 0, 0, 0.08),
    -12px -12px 24px rgba(255, 255, 255, 0.9);
}

/* 左侧图片区域 */
.image-container {
  flex: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f8f8;
  border-radius: 12px;
  box-shadow: 
    inset 6px 6px 12px rgba(0, 0, 0, 0.05),
    inset -6px -6px 12px rgba(255, 255, 255, 0.8);
  overflow: hidden;
  min-height: 500px;
}

.preview-image {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
  transition: transform 0.3s ease;
}

.preview-image:hover {
  transform: scale(1.02);
}

/* 右侧信息区域 */
.info-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 30px;
  padding: 20px;
}

.image-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #000;
  margin: 0;
  word-break: break-all;
}

.image-meta {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-label {
  font-weight: 500;
  color: #666;
  min-width: 80px;
}

.meta-value {
  color: #333;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 20px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 15px 25px;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  border: none;
}

.action-btn.download {
  background: #000;
  color: white;
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.2),
    -6px -6px 12px rgba(255, 255, 255, 0.1);
}

.action-btn.download:hover {
  transform: translateY(-2px);
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.3),
    -8px -8px 16px rgba(255, 255, 255, 0.15);
}

.login-hint {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

.login-hint-btn {
  display: inline-block;
  margin-top: 10px;
  padding: 12px 24px;
  background: #000;
  color: white;
  text-decoration: none;
  border-radius: 10px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.2),
    -4px -4px 8px rgba(255, 255, 255, 0.1);
}

.login-hint-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -6px -6px 12px rgba(255, 255, 255, 0.15);
}

.action-btn.share {
  background: #f5f5f5;
  color: #000;
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.08),
    -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.action-btn.share:hover {
  transform: translateY(-2px);
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.1),
    -8px -8px 16px rgba(255, 255, 255, 0.95);
}

.btn-icon {
  font-size: 1.2rem;
}

.share-link-box {
  text-align: center;
  padding: 10px;
  background: #e8f5e9;
  border-radius: 8px;
  margin-top: 10px;
}

.copied-text {
  color: #4CAF50;
  font-weight: 500;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 500px;
  gap: 20px;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #000;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .preview-content {
    flex-direction: column;
    gap: 30px;
  }

  .image-container {
    min-height: 300px;
  }

  .preview-image {
    max-height: 400px;
  }

  .info-container {
    padding: 10px;
  }

  .image-title {
    font-size: 1.2rem;
  }
}
</style>
