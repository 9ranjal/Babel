// src/lib/apiClient.ts
import axios from 'axios';
import { supabase } from './supabase';

const baseURL = process.env.REACT_APP_API_BASE || 'http://localhost:5002';

export const api = axios.create({ baseURL, withCredentials: false });

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    // Optional: centralize error toast/logging
    return Promise.reject(err);
  }
);
