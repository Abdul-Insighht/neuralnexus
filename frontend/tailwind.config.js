/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        parchment: {
          50: '#fbfaf8',
          100: '#f6f4ef',
          200: '#eee8dd',
          300: '#e1d5c2',
          400: '#d0bc9f',
          500: '#c2a581',
          600: '#b48f68',
          700: '#977454',
          800: '#7c6148',
          900: '#644e3b',
          950: '#35291f',
        },
        ink: {
          50: '#f4f6f8',
          100: '#e3e8ef',
          200: '#cdd7e3',
          300: '#aabed1',
          400: '#809eb9',
          500: '#6182a1',
          600: '#4d6986',
          700: '#3f546d',
          800: '#36475a',
          900: '#2f3c4c',
          950: '#1e2632',
        },
        crimson: {
          50: '#fcf4f4',
          100: '#fae6e6',
          200: '#f3d1d1',
          300: '#eaafaf',
          400: '#dd8282',
          500: '#cd5858',
          600: '#b73f3f',
          700: '#9a3030',
          800: '#802b2b',
          900: '#6a2828',
          950: '#391111',
        }
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Merriweather', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
