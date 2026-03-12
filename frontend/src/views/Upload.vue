<template>
  <div class="upload">
    <!-- 导航栏 -->
    <header class="header">
      <div class="container">
        <div class="header-content">
          <h1 class="logo">Luckymax</h1>
          <div class="search-box">
            <input 
              type="text" 
              placeholder="搜索壁纸..." 
              class="search-input"
            />
            <button class="search-btn">搜索</button>
          </div>
          <div class="header-actions">
            <template v-if="auth.isLoggedIn.value">
              <span class="username">{{ auth.username.value }}</span>
              <button @click="handleLogout" class="logout-btn">退出</button>
            </template>
            <router-link to="/" class="back-home-btn">返回首页</router-link>
          </div>
        </div>
      </div>
    </header>
    
    <!-- 上传区域 -->
    <section class="upload-section">
      <div class="container">
        <h2 class="upload-title">上传壁纸</h2>
        <p class="upload-description">支持JPG、PNG、WebP格式，文件大小不超过10MB</p>
        
        <div class="upload-container">
          <!-- 左侧上传区域 -->
          <div class="upload-left">
            <!-- 上传界面 -->
            <div 
              v-if="!selectedFile"
              class="upload-area" 
              :class="{ 'dragover': isDragover }"
              @drop="handleDrop"
              @dragover.prevent="isDragover = true"
              @dragleave.prevent="isDragover = false"
              @click="triggerFileInput"
            >
              <input 
                type="file" 
                ref="fileInput" 
                accept="image/*" 
                @change="handleFileSelect"
                style="display: none;"
              />
              <div class="upload-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 5V19" stroke="#667eea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M5 12L12 5L19 12" stroke="#667eea" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <h3 class="upload-area-title">点击或拖拽文件到此处上传</h3>
              <p class="upload-area-subtitle">支持JPG、PNG、WebP格式</p>
            </div>
            
            <!-- 图片预览和重新上传 -->
            <div v-else-if="!uploadSuccess" class="upload-preview-area">
              <input 
                type="file" 
                ref="fileInput" 
                accept="image/*" 
                @change="handleFileSelect"
                style="display: none;"
              />
              <div class="uploaded-image">
                <img 
                  :src="previewUrl" 
                  alt="已上传图片" 
                  class="preview-image"
                  @error="handlePreviewError"
                />
              </div>
              <div class="upload-actions" style="text-align: center; padding: 0 10px;">
                <button 
                  class="upload-btn secondary" 
                  @click="triggerFileInput"
                >
                  重新上传
                </button>
              </div>
            </div>
            
            <!-- 上传成功 -->
            <div v-else class="upload-success-left">
              <input 
                type="file" 
                ref="fileInput" 
                accept="image/*" 
                @change="handleFileSelect"
                style="display: none;"
              />
              <div class="uploaded-image">
                <img 
                  :src="previewUrl" 
                  alt="已上传图片" 
                  class="preview-image"
                  @error="handlePreviewError"
                />
              </div>
              <div class="upload-actions" style="text-align: center; padding: 0 10px;">
                <button 
                  class="upload-btn secondary" 
                  @click="resetUpload"
                >
                  上传新文件
                </button>
              </div>
            </div>
          </div>
          
          <!-- 右侧预览区域 -->
          <div class="upload-right" v-if="selectedFile">
            <!-- 正常预览 -->
            <div class="preview-container" v-if="!uploadSuccess">
              <h3 class="preview-title">预览</h3>
              <div class="wallpaper-name-input">
                <label class="name-label">壁纸昵称：</label>
                <input 
                  type="text" 
                  v-model="wallpaperName" 
                  placeholder="请输入壁纸昵称"
                  class="name-input"
                />
              </div>
              <div class="wallpaper-category-input">
                <label class="category-label">分类：</label>
                <div class="category-options">
                  <label class="category-option">
                    <input 
                      type="radio" 
                      v-model="selectedCategory" 
                      value="电脑"
                    />
                    <span>电脑</span>
                  </label>
                  <label class="category-option">
                    <input 
                      type="radio" 
                      v-model="selectedCategory" 
                      value="手机"
                    />
                    <span>手机</span>
                  </label>
                </div>
              </div>
              <div class="preview-content">
                <img 
                  :src="previewUrl" 
                  alt="预览图片" 
                  class="preview-image"
                  @error="handlePreviewError"
                />
                <div class="file-info">
                  <div class="file-info-item">
                    <span class="label">文件名：</span>
                    <span class="value">{{ selectedFile.name }}</span>
                  </div>
                  <div class="file-info-item">
                    <span class="label">文件大小：</span>
                    <span class="value">{{ formatFileSize(selectedFile.size) }}</span>
                  </div>
                  <div class="file-info-item">
                    <span class="label">类型：</span>
                    <span class="value">{{ selectedFile.type }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 上传按钮 -->
              <div class="upload-actions" v-if="!isUploading">
                <button 
                  class="upload-btn primary" 
                  @click="uploadFile"
                  :disabled="isUploading"
                >
                  开始上传
                </button>
                <button 
                  class="cancel-btn" 
                  @click="resetUpload"
                >
                  取消
                </button>
              </div>
              
              <!-- 上传进度 -->
              <div class="upload-progress" v-if="isUploading">
                <div class="progress-bar-container">
                  <div class="progress-bar" :style="{ width: `${uploadProgress}%` }"></div>
                </div>
                <p class="progress-text">上传中... {{ uploadProgress }}%</p>
              </div>
              
              <!-- 错误提示 -->
              <div class="error-message" v-if="errorMessage">
                <div class="error-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="#f44336" stroke-width="2"/>
                    <path d="M12 8V12" stroke="#f44336" stroke-width="2" stroke-linecap="round"/>
                    <path d="M12 16H12.01" stroke="#f44336" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <span>{{ errorMessage }}</span>
              </div>
            </div>
            
            <!-- 上传成功 -->
            <div class="preview-container success-panel" v-else>
              <div class="upload-success">
                <div class="success-icon">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 6L9 17L4 12" stroke="#4CAF50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <h3 class="success-title">上传成功！</h3>
                <div class="share-link-container">
                  <label class="share-link-label">分享链接：</label>
                  <div class="share-link">
                    <input 
                      type="text" 
                      :value="shareUrl" 
                      readonly 
                      class="share-link-input"
                    />
                    <button 
                      class="copy-btn" 
                      @click="copyShareUrl"
                      :class="{ 'copied': isCopied }"
                    >
                      {{ isCopied ? '已复制' : '复制' }}
                    </button>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const auth = inject('auth', {
  isLoggedIn: ref(false),
  username: ref(''),
  isAdmin: ref(false),
  checkLoginStatus: async () => {},
  logout: async () => {}
});

// 状态管理
const fileInput = ref(null);
const selectedFile = ref(null);
const previewUrl = ref('');
const isDragover = ref(false);
const isUploading = ref(false);
const uploadProgress = ref(0);
const uploadSuccess = ref(false);
const shareUrl = ref('');
const errorMessage = ref('');
const isCopied = ref(false);
const wallpaperName = ref('');
const selectedCategory = ref('电脑');

// 后端API基础URL
const API_BASE_URL = '/api';

// 页面加载时检查登录状态
onMounted(async () => {
  await auth.checkLoginStatus();
  if (!auth.isLoggedIn.value) {
    router.push('/login');
  }
});

// 退出登录
const handleLogout = async () => {
  await auth.logout();
  router.push('/');
};

// 触发文件选择
const triggerFileInput = () => {
  fileInput.value.click();
};

// 处理文件选择
const handleFileSelect = (e) => {
  const file = e.target.files[0];
  if (file) {
    validateFile(file);
  }
};

// 处理拖拽上传
const handleDrop = (e) => {
  e.preventDefault();
  isDragover.value = false;
  const file = e.dataTransfer.files[0];
  if (file) {
    validateFile(file);
  }
};

// 验证文件
const validateFile = (file) => {
  // 检查文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!allowedTypes.includes(file.type)) {
    errorMessage.value = '只支持JPG、PNG、WebP格式的图片';
    return;
  }
  
  // 检查文件大小（10MB）
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    errorMessage.value = '文件大小不能超过10MB';
    return;
  }
  
  // 重置错误信息
  errorMessage.value = '';
  
  // 设置选中的文件
  selectedFile.value = file;
  
  // 生成预览
  const reader = new FileReader();
  reader.onload = (e) => {
    previewUrl.value = e.target.result;
  };
  reader.readAsDataURL(file);
};

// 处理预览图片加载错误
const handlePreviewError = (e) => {
  // 预览图片加载失败时，显示默认占位符
  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMTAwIiBjeT0iMTAwIiByPSIxMCIgZmlsbD0iI2U4ZThlOCIvPjx0ZXh0IHg9IjEwMCIgeT0iMTA1IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiM4ODgiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkltYWdlIFJlcG9ydDwvdGV4dD48L3N2Zz4=';
};

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 上传文件
const uploadFile = async () => {
  if (!selectedFile.value) return;
  
  const formData = new FormData();
  formData.append('file', selectedFile.value);
  formData.append('wallpaper_name', wallpaperName.value || selectedFile.value.name);
  formData.append('category', selectedCategory.value);
  
  isUploading.value = true;
  uploadProgress.value = 0;
  errorMessage.value = '';
  
  try {
    const token = localStorage.getItem('token');
    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      onUploadProgress: (progressEvent) => {
        // 限制进度最大为90%，留给后端处理时间
        const percent = Math.round((progressEvent.loaded / progressEvent.total) * 100);
        uploadProgress.value = Math.min(percent, 90);
      }
    });
    
    // 上传成功，显示100%
    uploadProgress.value = 100;
    uploadSuccess.value = true;
    shareUrl.value = `${API_BASE_URL}${response.data.share_url}`;
  } catch (error) {
    console.error('上传失败:', error);
    errorMessage.value = '上传失败，请重试';
  } finally {
    isUploading.value = false;
  }
};

// 复制分享链接
const copyShareUrl = () => {
  navigator.clipboard.writeText(shareUrl.value).then(() => {
    isCopied.value = true;
    // 3秒后恢复按钮状态
    setTimeout(() => {
      isCopied.value = false;
    }, 3000);
  }).catch(err => {
    console.error('复制失败:', err);
    errorMessage.value = '复制失败，请手动复制';
  });
};

// 重置上传
const resetUpload = () => {
  selectedFile.value = null;
  previewUrl.value = '';
  uploadProgress.value = 0;
  uploadSuccess.value = false;
  shareUrl.value = '';
  errorMessage.value = '';
  isCopied.value = false;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};
</script>

<style scoped>
/* 全局样式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* 头部 */
.header {
  background: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 0;
  gap: 20px;
}

.logo {
  font-size: 1.8rem;
  font-weight: 700;
  color: #000;
  margin: 0;
  flex-shrink: 0;
}

.search-box {
  display: flex;
  flex: 1;
  max-width: 500px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e0e0e0;
}

.search-input {
  flex: 1;
  padding: 10px 15px;
  border: none;
  font-size: 0.9rem;
  outline: none;
  background: white;
}

.search-btn {
  padding: 0 20px;
  background-color: #000;
  color: white;
  border: none;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.search-btn:hover {
  background-color: #333;
}

.header-actions {
  flex-shrink: 0;
}

.upload-btn {
  display: inline-block;
  padding: 10px 20px;
  background: #000;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.2),
    -4px -4px 8px rgba(255, 255, 255, 0.1);
}

.upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -6px -6px 12px rgba(255, 255, 255, 0.15);
}

.upload-btn.active {
  background: #000;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.3),
    inset -4px -4px 8px rgba(255, 255, 255, 0.1);
  color: white;
}

.back-home-btn {
  display: inline-block;
  padding: 10px 20px;
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

.back-home-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.1),
    -6px -6px 12px rgba(255, 255, 255, 0.95);
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.2),
    -4px -4px 8px rgba(255, 255, 255, 0.1);
}

/* 上传区域 */
.upload-section {
  padding: 60px 0;
  background: #f9f9f9;
  min-height: calc(100vh - 100px);
}

.upload-container {
  max-width: 1200px;
  margin: 0 auto;
  background: #f9f9f9;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.05),
    -8px -8px 16px rgba(255, 255, 255, 0.8);
  display: flex;
  gap: 30px;
}

.upload-title {
  font-size: 2rem;
  font-weight: 600;
  color: #000;
  margin: 0 0 10px 0;
  text-align: center;
}

.upload-description {
  color: #666;
  text-align: center;
  margin: 0 0 30px 0;
}

.logout-btn {
  display: inline-block;
  padding: 10px 20px;
  background: #fff;
  color: #000;
  text-decoration: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  border: none;
  cursor: pointer;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.08),
    -4px -4px 8px rgba(255, 255, 255, 0.9);
}

.logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.1),
    -6px -6px 12px rgba(255, 255, 255, 0.95);
}

.username {
  display: inline-block;
  padding: 10px 15px;
  background: #f0f0f0;
  color: #333;
  border-radius: 8px;
  font-size: 0.9rem;
  margin-right: 10px;
  box-shadow: 
    inset 2px 2px 4px rgba(0, 0, 0, 0.05),
    inset -2px -2px 4px rgba(255, 255, 255, 0.8);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 上传区域 */
.upload-area {
  border: 2px dashed #e0e0e0;
  border-radius: 12px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: #f5f5f5;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.05),
    inset -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.upload-area:hover {
  border-color: #000;
  background-color: #f0f0f0;
  box-shadow: 
    inset 6px 6px 12px rgba(0, 0, 0, 0.08),
    inset -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.upload-area.dragover {
  border-color: #000;
  background-color: #e8e8e8;
  box-shadow: 
    inset 6px 6px 12px rgba(0, 0, 0, 0.08),
    inset -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.upload-icon {
  margin-bottom: 20px;
}

.upload-area-title {
  font-size: 1.2rem;
  font-weight: 500;
  color: #000;
  margin: 0 0 10px 0;
}

.upload-area-subtitle {
  color: #777;
  margin: 0;
}

/* 左侧上传区域 */
.upload-left {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 右侧预览区域 */
.upload-right {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}

.upload-area {
  width: 100%;
  min-height: 400px;
}

/* 上传预览区域 */
.upload-preview-area,
.upload-success-left {
  width: 100%;
  min-height: 320px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 16px;
  box-shadow: 
    12px 12px 24px rgba(0, 0, 0, 0.08),
    -12px -12px 24px rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.3s ease;
}

.uploaded-image {
  width: 100%;
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f8f8f8;
  border-radius: 12px;
  box-shadow: 
    inset 6px 6px 12px rgba(0, 0, 0, 0.05),
    inset -6px -6px 12px rgba(255, 255, 255, 0.8);
  overflow: hidden;
  margin: 0;
  position: relative;
}

.uploaded-image .preview-image {
  width: auto;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
  border-radius: 6px;
}

.uploaded-image:hover .preview-image {
  transform: scale(1.05);
}

.upload-btn.secondary {
  background: #f5f5f5;
  color: #000;
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.08),
    -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.upload-btn.secondary:hover {
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.1),
    -8px -8px 16px rgba(255, 255, 255, 0.95);
  transform: translateY(-2px);
}

.upload-btn.secondary:active {
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.1),
    inset -4px -4px 8px rgba(255, 255, 255, 0.8);
  transform: translateY(0);
}

/* 预览区域 */
.preview-container {
  width: 100%;
  min-height: 400px;
  padding: 25px;
  background: #f9f9f9;
  border-radius: 10px;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.05),
    inset -4px -4px 8px rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.preview-title {
  font-size: 1.2rem;
  font-weight: 500;
  color: #333;
  margin: 0 0 20px 0;
}

.wallpaper-name-input {
  margin-bottom: 20px;
}

.name-label {
  display: block;
  font-weight: 500;
  color: #555;
  margin-bottom: 8px;
}

.name-input {
  width: 100%;
  padding: 12px 15px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  color: #333;
  transition: all 0.3s ease;
  background: #f9f9f9;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.05),
    inset -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.name-input:focus {
  outline: none;
  box-shadow: 
    inset 6px 6px 12px rgba(0, 0, 0, 0.08),
    inset -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.wallpaper-category-input {
  margin-bottom: 20px;
}

.category-label {
  display: block;
  font-weight: 500;
  color: #555;
  margin-bottom: 8px;
}

.category-options {
  display: flex;
  gap: 20px;
}

.category-option {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.category-option input[type="radio"] {
  width: 16px;
  height: 16px;
  accent-color: #000;
}

.category-option span {
  color: #333;
  font-size: 1rem;
}

.preview-content {
  display: flex;
  gap: 20px;
  align-items: center;
}

.preview-image {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.05),
    -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.file-info {
  flex: 1;
}

.file-info-item {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.file-info-item .label {
  font-weight: 500;
  color: #555;
  min-width: 80px;
}

.file-info-item .value {
  color: #333;
  word-break: break-all;
}

/* 上传操作 */
.upload-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.upload-btn.primary {
  background-color: #4CAF50;
}

.upload-btn.primary:hover {
  background-color: #45a049;
}

.cancel-btn {
  padding: 10px 20px;
  background-color: #f5f5f5;
  color: #333;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background-color: #e0e0e0;
}

/* 上传进度 */
.upload-progress {
  margin-top: 30px;
  text-align: center;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: #f9f9f9;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
  box-shadow: 
    inset 2px 2px 4px rgba(0, 0, 0, 0.05),
    inset -2px -2px 4px rgba(255, 255, 255, 0.8);
}

.progress-bar {
  height: 100%;
  background: #000;
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-text {
  color: #555;
  margin: 0;
}

/* 上传成功 */
.upload-success {
  margin-top: 0;
  text-align: center;
  padding: 20px;
  background: transparent;
  border-radius: 0;
  box-shadow: none;
}

.success-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320px;
}

.success-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #000;
  margin: 15px 0 20px 0;
}

.share-link-container {
  margin-bottom: 20px;
  text-align: left;
}

.share-link-label {
  display: block;
  font-weight: 500;
  color: #555;
  margin-bottom: 10px;
}

.share-link {
  display: flex;
  gap: 10px;
}

.share-link-input {
  flex: 1;
  padding: 12px 15px;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #333;
  background: #f9f9f9;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.05),
    inset -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.copy-btn {
  padding: 0 20px;
  background: #f9f9f9;
  color: #000;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.05),
    -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.copy-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.08),
    -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.copy-btn.copied {
  background: #f9f9f9;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.05),
    inset -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.success-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.back-btn {
  padding: 10px 20px;
  background-color: #f5f5f5;
  color: #333;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background-color: #e0e0e0;
}

/* 错误提示 */
.error-message {
  margin-top: 20px;
  padding: 15px;
  background-color: #ffebee;
  border-left: 4px solid #f44336;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.error-icon {
  flex-shrink: 0;
}

.error-message span {
  color: #c62828;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 15px;
    padding: 15px 0;
  }
  
  .nav {
    gap: 20px;
  }
  
  .upload-container {
    padding: 20px;
  }
  
  .upload-area {
    padding: 40px 10px;
  }
  
  .preview-content {
    flex-direction: column;
    text-align: center;
  }
  
  .file-info-item {
    justify-content: center;
  }
  
  .upload-actions {
    flex-direction: column;
  }
  
  .success-actions {
    flex-direction: column;
  }
  
  .share-link {
    flex-direction: column;
  }
  
  .share-link-input {
    width: 100%;
  }
  
  .copy-btn {
    padding: 10px 20px;
  }
}
</style>