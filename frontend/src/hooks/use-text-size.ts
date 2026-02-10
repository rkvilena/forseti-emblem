"use client";

import { useCallback, useEffect, useState } from "react";

export type TextSize = "sm" | "md" | "lg" | "xl";

const STORAGE_KEY = "forsetiemblem.textSize";

const SIZE_TO_PX: Record<TextSize, string> = {
  sm: "15px",
  md: "18px",
  lg: "21px",
  xl: "24px",
};

function applyTextSizeToDocument(size: TextSize) {
  const root = document.documentElement;
  root.style.fontSize = SIZE_TO_PX[size];
  root.dataset.textSize = size;
}

export function useTextSize() {
  const [textSize, setTextSize] = useState<TextSize>("lg");

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY) as TextSize | null;
    if (saved === "sm" || saved === "md" || saved === "lg" || saved === "xl") {
      setTextSize(saved);
      applyTextSizeToDocument(saved);
      return;
    }

    applyTextSizeToDocument("lg");
  }, []);

  const setAndPersist = useCallback((next: TextSize) => {
    setTextSize(next);
    applyTextSizeToDocument(next);
    window.localStorage.setItem(STORAGE_KEY, next);
  }, []);

  return { textSize, setTextSize: setAndPersist };
}
