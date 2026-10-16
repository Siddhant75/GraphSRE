/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./styles/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: "#090D16",
        surface: "#0F172A",
        surfaceBorder: "#1E293B",
        accentBlue: "#3B82F6",
        accentPurple: "#8B5CF6",
        accentEmerald: "#10B981",
        accentAmber: "#F59E0B",
        accentRed: "#EF4444"
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace']
      }
    },
  },
  plugins: [],
}
