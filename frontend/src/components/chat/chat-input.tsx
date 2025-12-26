"use client";

/**
 * ChatInput Component
 * 
 * Text input area for composing and sending chat messages.
 * Features auto-resize textarea and keyboard shortcuts.
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

export function ChatInput({
  onSend,
  isLoading = false,
  placeholder = "Ask about Fire Emblem chapters...",
  className,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
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
      }
    },
    [message, isLoading, onSend]
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Submit on Enter (without Shift)
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const canSubmit = message.trim().length > 0 && !isLoading;

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        "relative flex items-end gap-3 p-4",
        "bg-surface-elevated border-t border-surface-border",
        className
      )}
    >
      {/* Decorative ember effect on focus */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1/2 h-px bg-gradient-to-r from-transparent via-primary-500/50 to-transparent" />
      </div>

      <div className="relative flex-1">
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
            "w-full resize-none rounded-xl",
            "px-4 py-3 pr-12",
            "bg-surface-muted border border-surface-border",
            "text-text-primary placeholder:text-text-muted",
            "focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500",
            "transition-colors duration-200",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "min-h-[48px] max-h-[200px]"
          )}
        />
        
        {/* Character count indicator */}
        {message.length > 0 && (
          <span className="absolute bottom-3 right-14 text-xs text-text-muted">
            {message.length}
          </span>
        )}
      </div>

      <button
        type="submit"
        disabled={!canSubmit}
        className={cn(
          "flex-shrink-0 p-3 rounded-xl",
          "transition-all duration-200",
          canSubmit
            ? "bg-primary-600 text-white hover:bg-primary-500 hover:shadow-glow-primary active:bg-primary-700"
            : "bg-surface-muted text-text-muted cursor-not-allowed"
        )}
        aria-label="Send message"
      >
        <SendIcon className="w-5 h-5" />
      </button>
    </form>
  );
}
