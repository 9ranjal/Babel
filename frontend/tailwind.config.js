/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'bg-[#F0E68C]/20',
    'border-[#F0E68C]/40',
    'bg-[#F0E68C]',
    'hover:bg-[#E6D678]',
    'text-[#0E0F14]',
    'bg-[#F6F1EA]',
  ],
  theme: {
    extend: {
      colors: {
        'background': 'var(--color-background)',
        'panel-dark': 'var(--color-panel-dark)',
        'panel-neutral': 'var(--color-panel-neutral)',
        'input-area': 'var(--color-input-area)',
        'text-primary': 'var(--color-text-primary)',
        'text-white': 'var(--color-text-white)',
        'text-placeholder': 'var(--color-text-placeholder)',
        'text-label': 'var(--color-text-label)',
        'text-label-secondary': 'var(--color-text-label-secondary)',
        'khaki': 'var(--color-khaki)',
        'khaki-light': 'var(--color-khaki-light)',
        'khaki-border': 'var(--color-khaki-border)',
        'orange': 'var(--color-orange)',
        'orange-hover': 'var(--color-orange-hover)',
        'border-neutral': 'var(--color-border-neutral)',
        'border-zinc': 'var(--color-border-zinc)',
        'border-zinc-light': 'var(--color-border-zinc-light)',
        'faq-card-bg': 'var(--color-faq-card-bg)',
        'faq-card-border': 'var(--color-faq-card-border)',
      },
      fontFamily: {
        sans: ['"SN Pro"', 'Helvetica', 'ui-sans-serif', 'system-ui'],
      },
      backdropBlur: {
        'sm': '4px',
      },
    },
  },
  plugins: [],
}
