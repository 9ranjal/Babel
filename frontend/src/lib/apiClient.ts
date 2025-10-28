import axios from 'axios';
import { supabase } from './supabase';

const baseURL = import.meta.env.VITE_API_BASE || 'http://localhost:5002';

export const api = axios.create({ baseURL, withCredentials: false });

api.interceptors.request.use(async (config) => {
  try {
    const { data } = await supabase.auth.getSession();
    const token = data && data.session ? data.session.access_token : undefined;
    if (token) config.headers.Authorization = `Bearer ${token}`;
  } catch (_) {
    // ignore
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => Promise.reject(err)
);

export default api;

