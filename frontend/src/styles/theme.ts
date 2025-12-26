/**
 * Forsetiemblem Design Tokens
 * 
 * Centralized theme constants for consistent styling across the application.
 * Import this file when you need access to theme values in TypeScript.
 */

export const theme = {
  colors: {
    primary: {
      50: "#e6f2ff",
      100: "#b3d9ff",
      200: "#80c0ff",
      300: "#4da6ff",
      400: "#268fff",
      500: "#0066cc",
      600: "#0052a3",
      700: "#003d7a",
      800: "#002952",
      900: "#001529",
      950: "#000a14",
    },
    accent: {
      50: "#fff9e6",
      100: "#ffedb3",
      200: "#ffe180",
      300: "#ffd54d",
      400: "#ffca26",
      500: "#f5b800",
      600: "#c49300",
      700: "#936e00",
      800: "#624900",
      900: "#312500",
    },
    crimson: {
      50: "#fef2f2",
      100: "#fee2e2",
      200: "#fecaca",
      300: "#fca5a5",
      400: "#f87171",
      500: "#dc2626",
      600: "#b91c1c",
      700: "#991b1b",
      800: "#7f1d1d",
      900: "#450a0a",
    },
    surface: {
      base: "#0d1117",
      elevated: "#161b22",
      muted: "#21262d",
      border: "#30363d",
    },
    text: {
      primary: "#f0f6fc",
      secondary: "#8b949e",
      muted: "#6e7681",
      inverse: "#0d1117",
    },
  },
  spacing: {
    xs: "0.25rem",
    sm: "0.5rem",
    md: "1rem",
    lg: "1.5rem",
    xl: "2rem",
    "2xl": "3rem",
  },
  borderRadius: {
    sm: "0.25rem",
    md: "0.5rem",
    lg: "0.75rem",
    xl: "1rem",
    full: "9999px",
  },
  fontSize: {
    xs: "0.75rem",
    sm: "0.875rem",
    base: "1rem",
    lg: "1.125rem",
    xl: "1.25rem",
    "2xl": "1.5rem",
    "3xl": "1.875rem",
    "4xl": "2.25rem",
  },
  animation: {
    fast: "150ms",
    normal: "200ms",
    slow: "300ms",
  },
} as const;

export type Theme = typeof theme;
