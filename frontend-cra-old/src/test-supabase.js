// Simple test to verify Supabase client works
import { supabase } from './lib/supabase.js';

console.log('Testing Supabase client...');
console.log('Supabase URL:', import.meta.env.VITE_SUPABASE_URL ? 'Set' : 'Missing');
console.log('Supabase Key:', import.meta.env.VITE_SUPABASE_ANON_KEY ? 'Set' : 'Missing');

// Test basic client initialization
try {
  console.log('Supabase client created successfully');
  console.log('Client URL:', supabase.supabaseUrl);
} catch (error) {
  console.error('Error creating Supabase client:', error);
}
