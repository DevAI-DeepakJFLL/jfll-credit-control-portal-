/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#F0F6FE',
          100: '#E1EDFE',
          500: '#1E3A8A',
          600: '#172554',
          900: '#0F172A',
        }
      }
    },
  },
  plugins: [],
}
