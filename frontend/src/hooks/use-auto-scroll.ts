"use client";

/**
 * useAutoScroll Hook
 * 
 * Automatically scrolls to the bottom of a container when content changes.
 * Useful for chat interfaces where new messages should be visible.
 */

import { useRef, useEffect, useCallback } from "react";

interface UseAutoScrollOptions {
  /** Whether auto-scroll is enabled */
  enabled?: boolean;
  /** Smooth scroll behavior */
  smooth?: boolean;
  /** Dependency array to trigger scroll */
  dependencies?: unknown[];
}

export function useAutoScroll<T extends HTMLElement>(
  options: UseAutoScrollOptions = {}
) {
  const { enabled = true, smooth = true, dependencies = [] } = options;
  
  const containerRef = useRef<T>(null);
  const shouldAutoScrollRef = useRef(true);

  // Handle user scroll to detect if they've scrolled up
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
    
    shouldAutoScrollRef.current = isAtBottom;
  }, []);

  // Scroll to bottom
  const scrollToBottom = useCallback(() => {
    if (!containerRef.current || !enabled || !shouldAutoScrollRef.current) return;

    containerRef.current.scrollTo({
      top: containerRef.current.scrollHeight,
      behavior: smooth ? "smooth" : "instant",
    });
  }, [enabled, smooth]);

  // Auto-scroll when dependencies change
  useEffect(() => {
    scrollToBottom();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);

  // Add scroll listener
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener("scroll", handleScroll);
    return () => container.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  return {
    containerRef,
    scrollToBottom,
  };
}
