<template>
  <div class="home">
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
              v-model="searchQuery"
              @keyup.enter="searchWallpapers"
            />
            <button class="search-btn" @click="searchWallpapers">搜索</button>
          </div>
          <div class="header-actions">
            <template v-if="auth.isLoggedIn.value">
              <router-link to="/upload" class="upload-btn">上传壁纸</router-link>
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
          </div>
        </div>
      </div>
    </header>
    
    <!-- 分类标签 -->
    <section class="categories-section">
      <div class="container">
        <div class="categories">
          <button 
            v-for="category in categories" 
            :key="category"
            class="category-tag"
            :class="{ active: selectedCategory === category }"
            @click="selectCategory(category)"
          >
            {{ category }}
          </button>
        </div>
      </div>
    </section>
    
    <!-- 壁纸展示区域 -->
    <section class="wallpapers-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">{{ selectedCategory }} ({{ filteredImages.length }})</h2>
          <div class="sort-options">
            <button 
              v-for="option in sortOptions" 
              :key="option.value"
              class="sort-btn"
              :class="{ active: selectedSort === option.value }"
              @click="selectSort(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>
        
        <div class="wallpapers-grid" v-if="filteredImages.length > 0">
          <div 
            v-for="image in filteredImages" 
            :key="image.file_id" 
            class="wallpaper-card"
            :class="{ 'phone': image.category === '手机' }"
          >
            <div class="wallpaper-preview">
              <img 
                :src="getOptimizedThumbnailUrl(image)" 
                :alt="image.original_filename" 
                class="wallpaper-image"
                @error="handleImageError"
                @click="viewWallpaper(image)"
                loading="lazy"
              />
              <div class="wallpaper-overlay">
                <div class="overlay-actions">
                  <template v-if="auth.isLoggedIn.value">
                    <button 
                      @click="downloadOriginalImage(image)" 
                      class="action-btn download"
                      title="下载"
                    >
                      <span class="btn-icon">↓</span>
                    </button>
                    <button @click="copyImageLink(image.share_url)" class="action-btn share" title="分享">
                      <span class="btn-icon">↑</span>
                    </button>
                    <button 
                      v-if="auth.isAdmin.value" 
                      @click="deleteImage(image.file_id)" 
                      class="action-btn delete"
                      title="删除"
                    >
                      <span class="btn-icon">🗑</span>
                    </button>
                  </template>
                  <button @click="viewWallpaper(image)" class="action-btn view" title="查看">
                    <span class="btn-icon">👁</span>
                  </button>
                </div>
              </div>
            </div>
            <div class="wallpaper-info">
              <span class="file-name">{{ image.display_name || image.original_filename }}</span>
              <div class="wallpaper-meta">
                <span class="resolution">{{ image.resolution || '未知' }}</span>
                <span class="size">{{ image.size || '未知' }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>没有找到壁纸</p>
          <router-link to="/upload" class="upload-btn">立即上传</router-link>
        </div>
      </div>
    </section>
    
    <!-- 分页 -->
    <section class="pagination-section" v-if="totalPages > 1">
      <div class="container">
        <div class="pagination">
          <button 
            class="page-btn"
            :disabled="currentPage === 1"
            @click="changePage(currentPage - 1)"
          >
            上一页
          </button>
          <span class="page-info">
            {{ currentPage }} / {{ totalPages }}
          </span>
          <button 
            class="page-btn"
            :disabled="currentPage === totalPages"
            @click="changePage(currentPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </section>
    
    <!-- 消息提示 -->
    <div class="message" v-if="message">
      {{ message }}
    </div>
    
    <!-- 壁纸查看模态框 -->
    <div class="modal" v-if="showModal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <button class="close-btn" @click="closeModal">×</button>
        <div class="modal-body">
          <img 
            :src="`${API_BASE_URL}${selectedImage?.share_url}`" 
            :alt="selectedImage?.original_filename" 
            class="modal-image"
          />
          <div class="modal-info">
              <h3>{{ selectedImage?.display_name || selectedImage?.original_filename }}</h3>
              <div class="modal-meta">
                <span class="resolution">{{ selectedImage?.resolution || '未知' }}</span>
                <span class="size">{{ selectedImage?.size || '未知' }}</span>
              </div>
              <div class="modal-actions">
                <a 
                  :href="`${API_BASE_URL}${selectedImage?.share_url}`" 
                  target="_blank" 
                  class="download-btn"
                  download
                >
                  下载原图
                </a>
                <button @click="copyImageLink(selectedImage?.share_url)" class="share-btn">
                  复制链接
                </button>
              </div>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue';
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
const images = ref([]);
const message = ref('');
const searchQuery = ref('');
const showUserMenu = ref(false);

// 切换用户菜单
const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value;
};

// 获取优化的预览图URL（使用后端缩略图接口）
const getOptimizedThumbnailUrl = (image) => {
  if (!image) return '';
  
  // 直接使用后端缩略图接口，确保返回带签名的HTTPS URL
  return `${API_BASE_URL}/thumbnail/${image.file_id}`;
};

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  const userProfile = document.querySelector('.user-profile');
  if (userProfile && !userProfile.contains(event.target)) {
    showUserMenu.value = false;
  }
};

// IntersectionObserver 用于懒加载
let imageObserver = null;

// 初始化懒加载
const initLazyLoad = () => {
  // 如果浏览器支持 IntersectionObserver
  if ('IntersectionObserver' in window) {
    imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          const src = img.dataset.src;
          if (src) {
            img.src = src;
            img.removeAttribute('data-src');
            img.classList.remove('lazy');
          }
          observer.unobserve(img);
        }
      });
    }, {
      rootMargin: '50px 0px', // 提前50px开始加载
      threshold: 0.01
    });

    // 观察所有懒加载图片
    const lazyImages = document.querySelectorAll('img.lazy');
    lazyImages.forEach(img => imageObserver.observe(img));
  } else {
    // 降级方案：直接加载所有图片
    const lazyImages = document.querySelectorAll('img.lazy');
    lazyImages.forEach(img => {
      const src = img.dataset.src;
      if (src) {
        img.src = src;
        img.removeAttribute('data-src');
        img.classList.remove('lazy');
      }
    });
  }
};

// 监听滚动事件（备用）
const handleLazyLoad = () => {
  const lazyImages = document.querySelectorAll('img.lazy');
  
  lazyImages.forEach(img => {
    const rect = img.getBoundingClientRect();
    if (rect.top <= window.innerHeight + 100 && rect.bottom >= -100) {
      const src = img.dataset.src;
      if (src) {
        img.src = src;
        img.removeAttribute('data-src');
        img.classList.remove('lazy');
      }
    }
  });
};

// 监听滚动事件
onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  // 只使用IntersectionObserver，移除滚动事件监听器以减少性能消耗
  if ('IntersectionObserver' in window) {
    initLazyLoad();
  } else {
    // 降级方案：只在需要时调用
    window.addEventListener('scroll', handleLazyLoad, { passive: true });
    window.addEventListener('resize', handleLazyLoad, { passive: true });
    handleLazyLoad();
  }
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  window.removeEventListener('scroll', handleLazyLoad);
  window.removeEventListener('resize', handleLazyLoad);
  if (imageObserver) {
    imageObserver.disconnect();
  }
});
const selectedCategory = ref('手机');
const selectedSort = ref('latest');
const currentPage = ref(1);
const itemsPerPage = 20;
const showModal = ref(false);

// 后端API基础URL
const API_BASE_URL = '/api';

// 分类列表
const categories = ['手机', '电脑'];

// 排序选项
const sortOptions = [
  { label: '最新', value: 'latest' },
  { label: '热门', value: 'popular' },
  { label: '随机', value: 'random' }
];

// 页面加载时获取已上传的图片列表
onMounted(() => {
  fetchImages();
});

// 获取已上传的图片列表
const fetchImages = async () => {
  try {
    // 先尝试从缓存获取
    const cachedImages = localStorage.getItem('cachedImages');
    const cachedExpiry = localStorage.getItem('cachedImagesExpiry');
    
    if (cachedImages && cachedExpiry && Date.now() < parseInt(cachedExpiry)) {
      images.value = JSON.parse(cachedImages);
      // 缓存加载后也初始化懒加载
      if ('IntersectionObserver' in window) {
        setTimeout(initLazyLoad, 100);
      } else {
        setTimeout(handleLazyLoad, 100);
      }
    }
    
    // 然后后台刷新数据
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API_BASE_URL}/images`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    
    // 使用后端返回的真实数据
    if (response.data && Array.isArray(response.data.images)) {
      images.value = response.data.images.map(image => {
        return {
          ...image,
          category: image.category || '电脑' // 使用后端返回的分类
        };
      });
    } else {
      console.error('获取图片列表失败: 响应数据格式不正确', response.data);
      images.value = [];
    }
    
    // 缓存数据（10分钟过期，减少请求频率）
    localStorage.setItem('cachedImages', JSON.stringify(images.value));
    localStorage.setItem('cachedImagesExpiry', Date.now() + 10 * 60 * 1000);
    
    // 数据更新后重新初始化懒加载
    if ('IntersectionObserver' in window) {
      setTimeout(initLazyLoad, 100);
    } else {
      setTimeout(handleLazyLoad, 100);
    }
  } catch (error) {
    console.error('获取图片列表失败:', error);
    message.value = '获取图片列表失败';
  }
};

// 过滤后的图片列表
const filteredImages = computed(() => {
  let result = [...images.value];
  
  // 按分类过滤
  result = result.filter(image => image.category === selectedCategory.value);
  
  // 按搜索词过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(image => 
      (image.display_name || image.original_filename).toLowerCase().includes(query)
    );
  }
  
  // 排序
  switch (selectedSort.value) {
    case 'latest':
      // 假设按file_id排序（实际项目中应该按上传时间）
      result.sort((a, b) => b.file_id.localeCompare(a.file_id));
      break;
    case 'popular':
      // 模拟热门排序
      result.sort(() => Math.random() - 0.5);
      break;
    case 'random':
      result.sort(() => Math.random() - 0.5);
      break;
  }
  
  // 分页
  const start = (currentPage.value - 1) * itemsPerPage;
  const end = start + itemsPerPage;
  return result.slice(start, end);
});

// 总页数
const totalPages = computed(() => {
  return Math.ceil(images.value.length / itemsPerPage);
});

// 选择分类
const selectCategory = (category) => {
  selectedCategory.value = category;
  currentPage.value = 1;
};

// 选择排序
const selectSort = (sort) => {
  selectedSort.value = sort;
  currentPage.value = 1;
};

// 搜索壁纸
const searchWallpapers = () => {
  currentPage.value = 1;
};

// 切换页码
const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
  }
};

// 查看壁纸
const viewWallpaper = (image) => {
  router.push(`/preview/${image.file_id}`);
};

// 关闭模态框
const closeModal = () => {
  showModal.value = false;
  selectedImage.value = null;
};

// 复制图片链接
const copyImageLink = (shareUrl) => {
  if (!shareUrl) return;
  
  const fullUrl = `${API_BASE_URL}${shareUrl}`;
  navigator.clipboard.writeText(fullUrl).then(() => {
    message.value = '链接已复制到剪贴板';
    // 3秒后自动清除消息
    setTimeout(() => {
      message.value = '';
    }, 3000);
  }).catch(err => {
    console.error('复制失败:', err);
    message.value = '复制失败，请手动复制';
    setTimeout(() => {
      message.value = '';
    }, 3000);
  });
};

// 下载原图
const downloadOriginalImage = async (image) => {
  try {
    const token = localStorage.getItem('token');
    
    // 使用fetch API进行流式下载
    const response = await fetch(`${API_BASE_URL}${image.share_url}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : ''
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // 获取文件名
    const contentDisposition = response.headers.get('content-disposition');
    let filename = image.original_filename || `image_${Date.now()}`;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch) {
        filename = filenameMatch[1];
      }
    }
    
    // 获取文件大小
    const contentLength = response.headers.get('content-length');
    const totalSize = contentLength ? parseInt(contentLength) : 0;
    
    // 使用流式读取
    const reader = response.body.getReader();
    const chunks = [];
    let receivedSize = 0;
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      chunks.push(value);
      receivedSize += value.length;
      
      // 可以在这里添加进度显示
      if (totalSize > 0) {
        const progress = (receivedSize / totalSize * 100).toFixed(1);
        console.log(`下载进度: ${progress}%`);
      }
    }
    
    // 合并所有chunks
    const allChunks = new Uint8Array(receivedSize);
    let position = 0;
    for (const chunk of chunks) {
      allChunks.set(chunk, position);
      position += chunk.length;
    }
    
    // 创建Blob并下载
    const blob = new Blob([allChunks]);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // 释放URL对象
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
    }, 100);
  } catch (error) {
    console.error('下载失败:', error);
    message.value = '下载失败：' + (error.message || '未知错误');
    setTimeout(() => {
      message.value = '';
    }, 3000);
  }
};

// 处理图片加载错误
const handleImageError = (e) => {
  // 当缩略图加载失败时，显示默认占位符
  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMTAwIiBjeT0iMTAwIiByPSIxMCIgZmlsbD0iI2U4ZThlOCIvPjx0ZXh0IHg9IjEwMCIgeT0iMTA1IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiM4ODgiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkltYWdlIFJlcG9ydDwvdGV4dD48L3N2Zz4=';
};

// 退出登录
const handleLogout = async () => {
  await auth.logout();
  router.push('/');
};

// 删除图片
const deleteImage = async (fileId) => {
  if (!confirm('确定要删除这张壁纸吗？')) return;
  
  try {
    const token = localStorage.getItem('token');
    const url = `${API_BASE_URL}/image/${fileId}`;
    
    const response = await axios.delete(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    // 刷新列表
    await fetchImages();
    alert('删除成功');
  } catch (error) {
    console.error('删除失败:', error);
    alert('删除失败：' + (error.response?.data?.detail || '未知错误'));
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
  background: #f9f9f9;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.05),
    -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.search-input {
  flex: 1;
  padding: 12px 15px;
  border: none;
  font-size: 0.9rem;
  outline: none;
  background: #f9f9f9;
  box-shadow: 
    inset 2px 2px 4px rgba(0, 0, 0, 0.05),
    inset -2px -2px 4px rgba(255, 255, 255, 0.8);
  border-radius: 8px 0 0 8px;
}

.search-btn {
  padding: 0 20px;
  background: #000;
  color: white;
  border: none;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 
    2px 2px 4px rgba(0, 0, 0, 0.2),
    -2px -2px 4px rgba(255, 255, 255, 0.1);
  border-radius: 0 8px 8px 0;
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.3),
    -4px -4px 8px rgba(255, 255, 255, 0.15);
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
  margin-right: 5px;
}

.upload-btn, .login-btn, .logout-btn {
  display: inline-block;
  padding: 8px 16px;
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

.upload-btn {
  background: #000;
  color: white;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.2),
    -4px -4px 8px rgba(255, 255, 255, 0.1);
}

.login-btn, .logout-btn {
  background: #f5f5f5;
  color: #000;
}

.upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -6px -6px 12px rgba(255, 255, 255, 0.15);
}

.login-btn:hover, .logout-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.1),
    -6px -6px 12px rgba(255, 255, 255, 0.95);
}

/* 用户头像 */
.user-profile {
  position: relative;
  margin-left: 10px;
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

/* 分类标签 */
.categories-section {
  padding: 20px 0;
  background: #f9f9f9;
}

.categories {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.category-tag {
  padding: 10px 20px;
  background: #f9f9f9;
  border: none;
  border-radius: 25px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #333;
  font-weight: 500;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.05),
    -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.category-tag:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.08),
    -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.category-tag.active {
  background: #000;
  color: white;
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -6px -6px 12px rgba(255, 255, 255, 0.15);
  font-weight: 600;
}

/* 壁纸展示区域 */
.wallpapers-section {
  padding: 40px 0;
  background: #f9f9f9;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.section-title {
  font-size: 1.8rem;
  font-weight: 600;
  color: #000;
  margin: 0;
}

.sort-options {
  display: flex;
  gap: 10px;
}

.sort-btn {
  padding: 8px 16px;
  background: #f9f9f9;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #333;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.05),
    -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.sort-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.08),
    -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.sort-btn.active {
  background: #000;
  color: white;
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.3),
    -6px -6px 12px rgba(255, 255, 255, 0.15);
  font-weight: 600;
}

.wallpapers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.wallpaper-card {
  background: #f9f9f9;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 
    8px 8px 16px rgba(0, 0, 0, 0.05),
    -8px -8px 16px rgba(255, 255, 255, 0.8);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.wallpaper-card:hover {
  transform: translateY(-3px);
  box-shadow: 
    12px 12px 24px rgba(0, 0, 0, 0.08),
    -12px -12px 24px rgba(255, 255, 255, 0.9);
}

/* 电脑壁纸布局 */
.wallpaper-card:not(.phone) {
  display: flex;
  flex-direction: column;
}

.wallpaper-preview {
  position: relative;
  height: 180px;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f0f0;
  border-radius: 8px;
  margin: 10px;
  box-shadow: 
    inset 4px 4px 8px rgba(0, 0, 0, 0.05),
    inset -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.wallpaper-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
  border-radius: 6px;
}

.wallpaper-card:hover .wallpaper-image {
  transform: scale(1.05);
}

.wallpaper-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 8px;
}

.wallpaper-card:hover .wallpaper-overlay {
  opacity: 1;
}

.overlay-actions {
  display: flex;
  gap: 15px;
}

.action-btn {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  background: #f9f9f9;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.1),
    -4px -4px 8px rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: #f0f0f0;
  transform: scale(1.1);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.15),
    -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.btn-icon {
  font-size: 18px;
  color: #000;
}

.wallpaper-info {
  padding: 10px 15px;
  text-align: center;
}

.file-name {
  display: block;
  font-size: 0.95rem;
  color: #000;
  margin-bottom: 8px;
  word-break: break-all;
  font-weight: 500;
}

.wallpaper-meta {
  display: flex;
  justify-content: center;
  gap: 10px;
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 10px;
}

/* 手机壁纸布局 */
.wallpaper-card.phone {
  display: flex;
  flex-direction: column;
  height: 400px;
  padding: 10px;
}

.wallpaper-card.phone .wallpaper-preview {
  height: 320px;
  margin: 0;
}

.wallpaper-card.phone .wallpaper-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.wallpaper-card.phone .wallpaper-info {
  padding: 10px;
  text-align: center;
}

.wallpaper-card.phone .file-name {
  margin-bottom: 8px;
}

.wallpaper-card.phone .wallpaper-meta {
  justify-content: center;
  gap: 10px;
  margin-bottom: 10px;
}

.wallpaper-card.phone .wallpaper-actions {
  padding: 0 10px;
}

/* 卡片底部按钮 */
.wallpaper-actions {
  display: flex;
  gap: 10px;
  padding: 0 15px 15px;
}

.card-action-btn {
  flex: 1;
  padding: 10px 12px;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  text-align: center;
  display: inline-block;
  background: #f9f9f9;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.05),
    -4px -4px 8px rgba(255, 255, 255, 0.8);
  color: #000;
}

.card-action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.08),
    -6px -6px 12px rgba(255, 255, 255, 0.9);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #777;
  font-size: 1.1rem;
}

.empty-state .upload-btn {
  margin-top: 20px;
}

/* 分页 */
.pagination-section {
  padding: 30px 0;
  background: #f9f9f9;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}

.page-btn {
  padding: 10px 18px;
  background: #f9f9f9;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: #000;
  box-shadow: 
    4px 4px 8px rgba(0, 0, 0, 0.05),
    -4px -4px 8px rgba(255, 255, 255, 0.8);
}

.page-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 
    6px 6px 12px rgba(0, 0, 0, 0.08),
    -6px -6px 12px rgba(255, 255, 255, 0.9);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.page-info {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
}

/* 消息提示 */
.message {
  position: fixed;
  top: 100px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 6px;
  background-color: #e3f2fd;
  color: #1976d2;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 模态框 */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: white;
  border-radius: 10px;
  max-width: 90vw;
  max-height: 90vh;
  overflow: auto;
  position: relative;
  animation: scaleIn 0.3s ease;
}

@keyframes scaleIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.close-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.1);
  border: none;
  font-size: 20px;
  cursor: pointer;
  z-index: 10;
}

.modal-body {
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.modal-image {
  max-width: 100%;
  max-height: 70vh;
  margin: 0 auto;
  border-radius: 8px;
}

.modal-info {
  margin-top: 20px;
}

.modal-info h3 {
  font-size: 1.2rem;
  color: #333;
  margin-bottom: 10px;
}

.modal-meta {
  display: flex;
  gap: 20px;
  font-size: 0.9rem;
  color: #777;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  gap: 10px;
}

.modal-actions .download-btn, .modal-actions .share-btn {
  flex: 1;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  text-align: center;
}

.modal-actions .download-btn {
  background-color: #4CAF50;
  color: white;
}

.modal-actions .download-btn:hover {
  background-color: #45a049;
}

.modal-actions .share-btn {
  background-color: #2196F3;
  color: white;
}

.modal-actions .share-btn:hover {
  background-color: #1976D2;
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
  
  .wallpapers-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 10px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .sort-options {
    width: 100%;
    overflow-x: auto;
    padding-bottom: 10px;
  }
  
  .modal-body {
    padding: 10px;
  }
  
  .modal-actions {
    flex-direction: column;
  }
}
</style>