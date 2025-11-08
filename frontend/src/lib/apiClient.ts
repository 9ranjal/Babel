import axios from 'axios';
import { API_BASE_URL } from './config';
import { supabase } from './supabase';

const baseURL = API_BASE_URL || undefined;

export const api = axios.create({
  baseURL,
  withCredentials: false,
});

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

