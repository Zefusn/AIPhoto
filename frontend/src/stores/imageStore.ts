import { defineStore } from 'pinia';
import axios from 'axios';

const API_BASE_URL = '/api';

interface Image {
  file_id: string;
  original_filename: string;
  display_name: string;
  category: string;
  share_url: string;
  thumbnail_url: string;
  file_url: string;
  resolution: string;
  size: string;
  uploader: string;
}

interface ImageStore {
  images: Image[];
  currentImage: Image | null;
  loading: boolean;
  error: string | null;
  lastFetched: number | null;
  cacheExpiry: number; // 缓存过期时间（毫秒）
}

export const useImageStore = defineStore('image', {
  state: (): ImageStore => ({
    images: [],
    currentImage: null,
    loading: false,
    error: null,
    lastFetched: null,
    cacheExpiry: 10 * 60 * 1000, // 10分钟缓存
  }),
  
  getters: {
    isCacheValid: (state) => {
      if (!state.lastFetched) return false;
      return Date.now() - state.lastFetched < state.cacheExpiry;
    },
    
    getImageById: (state) => (fileId: string) => {
      return state.images.find(image => image.file_id === fileId) || null;
    },
  },
  
  actions: {
    async fetchImages() {
      // 如果缓存有效，直接返回
      if (this.isCacheValid && this.lastFetched) {
        console.log('使用缓存的图片列表，缓存时间:', new Date(this.lastFetched).toLocaleString());
        console.log('当前时间:', new Date().toLocaleString());
        console.log('缓存过期时间:', this.cacheExpiry / 1000 / 60, '分钟');
        return;
      }
      
      console.log('缓存无效，重新获取图片列表');
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get(`${API_BASE_URL}/images`);
        this.images = response.data.images;
        this.lastFetched = Date.now();
        console.log('重新获取图片列表成功，更新缓存时间:', new Date(this.lastFetched).toLocaleString());
      } catch (error) {
        console.error('获取图片列表失败:', error);
        this.error = '获取图片列表失败';
      } finally {
        this.loading = false;
      }
    },
    
    async fetchImageById(fileId: string) {
      // 先从缓存中查找
      const cachedImage = this.getImageById(fileId);
      if (cachedImage) {
        this.currentImage = cachedImage;
        console.log('使用缓存的图片信息');
        return cachedImage;
      }
      
      // 如果缓存中没有，重新获取所有图片
      await this.fetchImages();
      
      // 再次查找
      const foundImage = this.getImageById(fileId);
      if (foundImage) {
        this.currentImage = foundImage;
        return foundImage;
      }
      
      return null;
    },
    
    // 手动更新图片列表（例如上传新图片后）
    updateImages() {
      this.lastFetched = null; // 清除缓存
      return this.fetchImages();
    },
    
    // 清除缓存
    clearCache() {
      this.lastFetched = null;
      this.images = [];
      this.currentImage = null;
    },
  },
});
