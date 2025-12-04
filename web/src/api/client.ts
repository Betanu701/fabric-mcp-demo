/**
 * API client configuration and initialization
 */
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Create axios instance with default configuration
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor to add tenant ID header
 */
apiClient.interceptors.request.use(
  (config) => {
    const tenantId = localStorage.getItem('tenant_id') || 'default';
    config.headers['X-Tenant-ID'] = tenantId;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 403) {
      console.error('Tenant access forbidden:', error.response.data);
    } else if (error.response?.status === 402) {
      console.error('Budget exceeded:', error.response.data);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
