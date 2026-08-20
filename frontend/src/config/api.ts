import axios from 'axios';
import { ROUTES } from './routes';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        localStorage.removeItem('token');
        window.location.href = ROUTES.LOGIN;
        return Promise.reject(error);
      } catch (err) {
        localStorage.removeItem('token');
        window.location.href = ROUTES.LOGIN;
        return Promise.reject(err);
      }
    }

    // Retry mechanism for network errors or 503 Service Unavailable
    const isNetworkError = !error.response;
    const isServiceUnavailable = error.response?.status === 503;

    if ((isNetworkError || isServiceUnavailable) && originalRequest) {
      originalRequest._retryCount = originalRequest._retryCount || 0;
      
      if (originalRequest._retryCount < 3) {
        originalRequest._retryCount += 1;
        const delay = Math.pow(2, originalRequest._retryCount - 1) * 1000; // 1s, 2s, 4s
        await sleep(delay);
        return api(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
