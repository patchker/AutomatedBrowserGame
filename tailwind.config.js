/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/*.{html,js}"],
  theme: {
    extend: {
      fontFamily: {
        'sanfrancisco': ['sanfrancisco', 'sans-serif'],
        'custom': ['masque', 'sans-serif']
      },
      // Dodaj swoje niestandardowe style tutaj
      right: {
        'checked': 'right-0'
      },
      backgroundColor: theme => ({
        ...theme('colors'),
        'checked': 'bg-green-400',
      }),
      borderColor: theme => ({
        ...theme('colors'),
        'checked': 'border-green-400',
      })
    }
  },
  plugins: [],
}
