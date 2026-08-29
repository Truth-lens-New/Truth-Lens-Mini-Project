/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./popup.html", "./popup.js"],
    darkMode: 'class',
    theme: {
        extend: {
            fontFamily: { sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'system-ui', 'sans-serif'] },
            colors: {
                background: '#09090b',
                card: '#18181b',
                primary: '#14b8a6', // Teal
                secondary: '#27272a',
                foreground: '#fafafa',
            }
        }
    },
    plugins: [],
}
