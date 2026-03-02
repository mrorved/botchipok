/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Onest', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        ink: {
          50: '#f5f5f0',
          100: '#e8e8e0',
          200: '#d0d0c0',
          300: '#b0b09a',
          400: '#8a8a72',
          500: '#6b6b52',
          600: '#525240',
          700: '#3d3d30',
          800: '#282821',
          900: '#141410',
          950: '#0a0a08',
        },
        amber: {
          400: '#fbbf24',
          500: '#f59e0b',
        }
      }
    }
  },
  plugins: []
}
