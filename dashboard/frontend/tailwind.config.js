/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: "#09090e",
          800: "#11111d",
          700: "#18182c",
          600: "#22223b"
        }
      }
    },
  },
  plugins: [],
}
