import type { Config } from "tailwindcss";

/**
 * Forsetiemblem Theme Configuration
 *
 * Clean, modern design with Fire Emblem-inspired accent colors:
 * - Teal as the primary accent (unchanged between themes)
 * - Green/Lime for highlights and gradients
 * - Purple/Blue for secondary accents
 */
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // Brand palette from provided design
        brand: {
          purple: "rgb(var(--brand-purple) / <alpha-value>)",
          blue: "rgb(var(--brand-blue) / <alpha-value>)",
          teal: "rgb(var(--brand-teal) / <alpha-value>)",
          green: "rgb(var(--brand-green) / <alpha-value>)",
          lime: "rgb(var(--brand-lime) / <alpha-value>)",
          gold: "rgb(var(--brand-gold) / <alpha-value>)",
          goldDark: "rgb(var(--brand-gold-dark) / <alpha-value>)",
        },
        // Surfaces/text are themeable via CSS variables (light/dark)
        surface: {
          base: "rgb(var(--surface-base) / <alpha-value>)",
          elevated: "rgb(var(--surface-elevated) / <alpha-value>)",
          muted: "rgb(var(--surface-muted) / <alpha-value>)",
          border: "rgb(var(--surface-border) / <alpha-value>)",
        },
        text: {
          primary: "rgb(var(--text-primary) / <alpha-value>)",
          secondary: "rgb(var(--text-secondary) / <alpha-value>)",
          muted: "rgb(var(--text-muted) / <alpha-value>)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Cinzel", "Georgia", "serif"],
      },
      borderRadius: {
        sm: "0.25rem", // 4px
        DEFAULT: "0.375rem", // 6px
        md: "0.5rem", // 8px
        lg: "0.625rem", // 10px
        xl: "0.75rem", // 12px
      },
      animation: {
        "fade-in": "fadeIn 0.2s ease-out",
        "slide-up": "slideUp 0.2s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
