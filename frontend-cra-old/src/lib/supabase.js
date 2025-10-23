// src/lib/supabase.js
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

let supabase;

const isValidUrl = (url) => typeof url === 'string' && /^https?:\/\//i.test(url);

if (isValidUrl(supabaseUrl) && typeof supabaseAnonKey === 'string' && supabaseAnonKey.length > 0) {
  supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
} else {
  // Safe stub for development when env vars are missing
  // Provides just the methods our code calls
  // eslint-disable-next-line no-console
  console.warn('Supabase env not set; using no-op client');
  supabase = {
    auth: {
      async getSession() {
        return { data: { session: null } };
      },
    },
  };
}

export { supabase };
export default supabase;


