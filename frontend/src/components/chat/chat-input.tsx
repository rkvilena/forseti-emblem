"use client";

/**
 * ChatInput Component
 *
 * Text input area for composing and sending chat messages.
 * Features auto-resize textarea with max height and scrolling.
 */

import { useState, useRef, useCallback, KeyboardEvent, FormEvent } from "react";
import { cn } from "@/lib/utils";
import { SendIcon } from "./icons";

interface ChatInputProps {
  /** Callback when message is submitted */
  onSend: (message: string) => void;
  /** Whether the chat is currently loading */
  isLoading?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Additional CSS classes */
  className?: string;
}

// Max height before showing scrollbar (approximately 4 lines)
const MAX_TEXTAREA_HEIGHT = 120;

export function ChatInput({
  onSend,
  isLoading = false,
  placeholder = "Ask about Fire Emblem chapters...",
  className,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content up to max height
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset to auto to measure actual content height
    textarea.style.height = "auto";
    const contentHeight = textarea.scrollHeight;

    // Apply height with max limit
    if (contentHeight <= MAX_TEXTAREA_HEIGHT) {
      textarea.style.height = `${contentHeight}px`;
      textarea.style.overflowY = "hidden";
    } else {
      textarea.style.height = `${MAX_TEXTAREA_HEIGHT}px`;
      textarea.style.overflowY = "auto";
    }
  }, []);

  const handleSubmit = useCallback(
    (e?: FormEvent) => {
      e?.preventDefault();

      const trimmedMessage = message.trim();
      if (!trimmedMessage || isLoading) return;

      onSend(trimmedMessage);
      setMessage("");

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
        textareaRef.current.style.overflowY = "hidden";
      }
    },
    [message, isLoading, onSend],
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Submit on Enter (without Shift)
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  const canSubmit = message.trim().length > 0 && !isLoading;

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        "p-4 bg-surface-elevated border-t-4 border-brand-gold/70",
        className,
      )}
    >
      <div className="relative flex items-end gap-2 max-w-3xl mx-auto">
        {/* Input container */}
        <div className="relative flex-1 flex items-end">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => {
              setMessage(e.target.value);
              adjustTextareaHeight();
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className={cn(
              "w-full resize-none rounded-lg",
              "px-4 py-3",
              "bg-surface-muted border border-surface-border",
              "text-text-primary placeholder:text-text-secondary",
              "focus:outline-none focus:border-brand-teal focus:ring-1 focus:ring-brand-teal",
              "transition-colors duration-200",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "min-h-[48px]",
            )}
            style={{ maxHeight: `${MAX_TEXTAREA_HEIGHT}px` }}
          />
        </div>

        {/* Send button - aligned with textarea bottom */}
        <button
          type="submit"
          disabled={!canSubmit}
          className={cn(
            "flex-shrink-0 h-12 w-12 flex items-center justify-center rounded-lg",
            "transition-all duration-200",
            canSubmit
              ? "bg-brand-teal text-white hover:bg-brand-green active:scale-95"
              : "bg-surface-muted text-text-secondary/70 cursor-not-allowed",
          )}
          aria-label="Send message"
        >
          <SendIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Helper text */}
      <p className="text-xs text-text-secondary text-center mt-2 opacity-60">
        Press Enter to send, Shift+Enter for new line
      </p>
    </form>
  );
}
