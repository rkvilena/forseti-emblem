import type { Config } from "tailwindcss";

/**
 * Forsetiemblem Theme Configuration
 * 
 * Inspired by Fire Emblem's medieval fantasy aesthetics:
 * - Deep royal blues and midnight tones for primary
 * - Golden/amber accents reminiscent of crests and nobility  
 * - Crimson for emphasis and interaction states
 * - Parchment-like neutrals for content areas
 */
const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary palette - Royal Blue (Forseti's wind magic theme)
        primary: {
          50: "#e6f2ff",
          100: "#b3d9ff",
          200: "#80c0ff",
          300: "#4da6ff",
          400: "#268fff",
          500: "#0066cc", // Main primary
          600: "#0052a3",
          700: "#003d7a",
          800: "#002952",
          900: "#001529",
          950: "#000a14",
        },
        // Accent palette - Sacred Gold
        accent: {
          50: "#fff9e6",
          100: "#ffedb3",
          200: "#ffe180",
          300: "#ffd54d",
          400: "#ffca26",
          500: "#f5b800", // Main accent
          600: "#c49300",
          700: "#936e00",
          800: "#624900",
          900: "#312500",
        },
        // Crimson - For actions and emphasis
        crimson: {
          50: "#fef2f2",
          100: "#fee2e2",
          200: "#fecaca",
          300: "#fca5a5",
          400: "#f87171",
          500: "#dc2626", // Main crimson
          600: "#b91c1c",
          700: "#991b1b",
          800: "#7f1d1d",
          900: "#450a0a",
        },
        // Background tones - Parchment/Medieval
        surface: {
          base: "#0d1117",      // Deep background
          elevated: "#161b22",  // Cards, modals
          muted: "#21262d",     // Subtle backgrounds
          border: "#30363d",    // Borders
        },
        // Text colors
        text: {
          primary: "#f0f6fc",
          secondary: "#8b949e",
          muted: "#6e7681",
          inverse: "#0d1117",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Cinzel", "Georgia", "serif"], // Medieval-style display font
      },
      boxShadow: {
        "glow-primary": "0 0 20px rgba(0, 102, 204, 0.3)",
        "glow-accent": "0 0 20px rgba(245, 184, 0, 0.3)",
        "glow-crimson": "0 0 20px rgba(220, 38, 38, 0.3)",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
