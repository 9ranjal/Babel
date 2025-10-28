import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

let supabase: any;

const isValidUrl = (url?: string): boolean => 
  typeof url === 'string' && /^https?:\/\//i.test(url);

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

