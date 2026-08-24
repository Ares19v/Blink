/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        cyber: {
          bg: "#0B0E14",
          card: "#121722",
          cardHover: "#182030",
          border: "#1E293B",
          cyan: "#00F5FF",
          cyanDark: "#00B4D8",
          emerald: "#10B981",
          amber: "#F59E0B",
          rose: "#EF4444",
          text: "#E2E8F0",
          muted: "#94A3B8"
        }
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'blink-ping': 'blink-ping 0.8s ease-out',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 15px rgba(0, 245, 255, 0.4)' },
          '50%': { opacity: '0.6', boxShadow: '0 0 5px rgba(0, 245, 255, 0.1)' },
        },
        'blink-ping': {
          '0%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.15)', opacity: '0.8' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
