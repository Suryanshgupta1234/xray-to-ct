import axios from 'axios';

// Get base URL from environment, or default to relative '/api/v1'
const rawBaseURL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').trim();

// Normalize URL: If the user provides a bare host e.g. "https://xray-to-ct.onrender.com"
// without "/api/v1", automatically append "/api/v1".
const getNormalizedBaseURL = (url) => {
  if (!url) return '/api/v1';
  const clean = url.replace(/\/+$/, '');
  if (clean.endsWith('/api/v1')) {
    return clean;
  }
  if (clean.endsWith('/api')) {
    return `${clean}/v1`;
  }
  return `${clean}/api/v1`;
};

const api = axios.create({
  baseURL: getNormalizedBaseURL(rawBaseURL),
  timeout: 120000, // 2 minutes for CPU-based heavy inference fallback
});

// Request Interceptor: Attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('xray_ct_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Extract standard envelope and handle auth expiration
api.interceptors.response.use(
  (response) => {
    return response.data; // Return the standard envelope { success, data, message }
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('xray_ct_token');
      localStorage.removeItem('xray_ct_user');
      if (window.location.pathname !== '/login' && window.location.pathname !== '/register' && window.location.pathname !== '/') {
        window.location.href = '/login';
      }
    }
    const errorData = error.response?.data?.error || {
      code: 'NETWORK_ERROR',
      message: error.message || 'Unable to communicate with the server.',
    };
    return Promise.reject(errorData);
  }
);

export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (email, password, full_name) => api.post('/auth/register', { email, password, full_name }),
  getMe: () => api.get('/auth/me'),
};

export const inferenceAPI = {
  submitTranslation: (file, modelVersion, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    if (modelVersion) {
      formData.append('model_version', modelVersion);
    }
    return api.post('/inference', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
  },
  getJob: (id) => api.get(`/inference/${id}`),
  getReport: (id) => api.get(`/inference/${id}/report`),
  getSlices: (id) => api.get(`/inference/${id}/slices`),
  getClinicalSamples: () => api.get('/inference/samples/clinical'),
  getHistory: (page = 1, pageSize = 10) => api.get(`/inference/history?page=${page}&page_size=${pageSize}`),
  deleteJob: (id) => api.delete(`/inference/${id}`),
};

export const modelAPI = {
  listModels: () => api.get('/models'),
  getAdminStats: () => api.get('/models/admin/stats'),
};

export const healthAPI = {
  getHealth: () => api.get('/health'),
};

export default api;
