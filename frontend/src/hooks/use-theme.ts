"use client";

import { useCallback, useEffect, useState } from "react";

export type ThemeMode = "dark" | "light";

const STORAGE_KEY = "forsetiemblem.theme";

function applyThemeToDocument(theme: ThemeMode) {
  const root = document.documentElement;
  if (theme === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

export function useTheme() {
  const [theme, setTheme] = useState<ThemeMode>("dark");

  useEffect(() => {
    // Initialize from localStorage, otherwise prefer system
    const saved = window.localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
    if (saved === "dark" || saved === "light") {
      setTheme(saved);
      applyThemeToDocument(saved);
      return;
    }

    const prefersDark = window.matchMedia?.(
      "(prefers-color-scheme: dark)",
    ).matches;
    const initial: ThemeMode = prefersDark ? "dark" : "light";
    setTheme(initial);
    applyThemeToDocument(initial);
  }, []);

  const setAndPersist = useCallback((next: ThemeMode) => {
    setTheme(next);
    applyThemeToDocument(next);
    window.localStorage.setItem(STORAGE_KEY, next);
  }, []);

  const toggleTheme = useCallback(() => {
    setAndPersist(theme === "dark" ? "light" : "dark");
  }, [theme, setAndPersist]);

  return { theme, setTheme: setAndPersist, toggleTheme };
}
