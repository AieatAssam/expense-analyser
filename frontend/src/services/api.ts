import axios from 'axios';

// Prefer Vite env vars in the frontend
const VITE_API_URL = (import.meta as any).env?.VITE_API_URL as string | undefined;
const originFallback = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000';
// Base origin for the API; versioning will be applied in an interceptor to avoid double-prefixing
const API_ORIGIN = `${(VITE_API_URL || originFallback).replace(/\/$/, '')}`;

const apiClient = axios.create({
  baseURL: API_ORIGIN,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    // Prefix /api/v1 for relative paths that don't already include it
    const url = config.url || '';
    const isAbsolute = /^https?:\/\//i.test(url);
    if (!isAbsolute) {
      const normalized = url.startsWith('/') ? url : `/${url}`;
      if (!normalized.startsWith('/api/v1')) {
        config.url = `/api/v1${normalized}`;
      } else {
        config.url = normalized; // ensure leading slash
      }
    }

    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Unauthorized, clear token and allow app to handle auth flow
      localStorage.removeItem('auth_token');
      // Do not force-navigate to a route that may not exist in SPA.
      // The Auth UI (e.g., LoginButton) should handle initiating login.
    }
    return Promise.reject(error);
  }
);

export const setAuthToken = (token: string): void => {
  localStorage.setItem('auth_token', token);
};

export const clearAuthToken = (): void => {
  localStorage.removeItem('auth_token');
};

// Optional helper for consumers that build absolute API URLs when needed
export const apiPath = (relative: string) => `${API_ORIGIN}/api/v1${relative.startsWith('/') ? '' : '/'}${relative}`;

export default apiClient;
