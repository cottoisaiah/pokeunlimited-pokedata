/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        // Pokemon theme colors
        'poke-blue': '#3b82f6',
        'poke-red': '#ef4444',
        'poke-yellow': '#fbbf24',
        pokemon: {
          electric: '#f7b731',
          fire: '#ea5455',
          water: '#0abde3',
          grass: '#10ac84',
          psychic: '#a55eea',
          ice: '#74b9ff',
          dragon: '#6c5ce7',
          dark: '#2d3436',
          fighting: '#fd79a8',
          poison: '#6c5ce7',
          ground: '#e17055',
          flying: '#74b9ff',
          bug: '#00b894',
          rock: '#636e72',
          ghost: '#6c5ce7',
          steel: '#636e72',
          fairy: '#fd79a8',
          normal: '#636e72',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'bounce-gentle': 'bounceGentle 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        bounceGentle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
      },
    },
  },
  plugins: [],
}