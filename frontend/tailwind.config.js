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
          50: '#fef3e2',
          100: '#fde3b3',
          200: '#fcd180',
          300: '#fbbf4d',
          400: '#fab126',
          500: '#f9a30a',
          600: '#f59508',
          700: '#f08406',
          800: '#eb7404',
          900: '#e25802',
        },
      },
    },
  },
  plugins: [],
}
