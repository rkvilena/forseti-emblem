"use client";

/**
 * ChatInput Component
 *
 * Text input area for composing and sending chat messages.
 * Features auto-resize textarea with max height and scrolling.
 */

import {
  useState,
  useRef,
  useCallback,
  useEffect,
  KeyboardEvent,
  FormEvent,
} from "react";
import { cn } from "@/lib/utils";
import { SendIcon } from "./icons";

interface ChatInputProps {
  /** Callback when message is submitted */
  onSend: (message: string, turnstileToken: string) => void;
  /** Callback when Turnstile token updates */
  onTokenChange?: (token: string | null) => void;
  /** Callback when Turnstile widget is created */
  onWidgetReady?: (widgetId: string) => void;
  /** External error message to display */
  externalError?: string | null;
  /** Whether the chat is currently loading */
  isLoading?: boolean;
  /** Placeholder text */
  placeholder?: string;
  /** Additional CSS classes */
  className?: string;
}

// Max height before showing scrollbar (approximately 4 lines)
const MAX_TEXTAREA_HEIGHT = 120;
const MAX_MESSAGE_CHARS = 300;

export function ChatInput({
  onSend,
  onTokenChange,
  onWidgetReady,
  externalError,
  isLoading = false,
  placeholder = "Ask about Fire Emblem chapters...",
  className,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileError, setTurnstileError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const turnstileRef = useRef<HTMLDivElement>(null);
  const turnstileWidgetIdRef = useRef<string | null>(null);

  const turnstileSiteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

  useEffect(() => {
    if (!turnstileSiteKey) return;

    let cancelled = false;
    let attempts = 0;

    const tryRender = () => {
      if (cancelled) return;
      if (!turnstileRef.current || turnstileWidgetIdRef.current) return;
      if (typeof window === "undefined" || !window.turnstile) {
        attempts += 1;
        if (attempts <= 20) {
          window.setTimeout(tryRender, 200);
        }
        return;
      }

      turnstileWidgetIdRef.current = window.turnstile.render(
        turnstileRef.current,
        {
          sitekey: turnstileSiteKey,
          callback: (token: string) => {
            setTurnstileToken(token);
            setTurnstileError(null);
            onTokenChange?.(token);
          },
          "expired-callback": () => {
            setTurnstileToken(null);
            onTokenChange?.(null);
          },
          "error-callback": () => {
            setTurnstileToken(null);
            setTurnstileError("Turnstile verification failed. Please retry.");
            onTokenChange?.(null);
          },
        },
      );

      if (turnstileWidgetIdRef.current) {
        onWidgetReady?.(turnstileWidgetIdRef.current);
      }
    };

    tryRender();

    return () => {
      cancelled = true;
      if (turnstileWidgetIdRef.current && window.turnstile) {
        window.turnstile.remove(turnstileWidgetIdRef.current);
        turnstileWidgetIdRef.current = null;
      }
    };
  }, [turnstileSiteKey]);

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
      if (!turnstileToken) {
        setTurnstileError("Please complete the Turnstile check to continue.");
        return;
      }

      onSend(trimmedMessage, turnstileToken);
      setMessage("");
      setTurnstileToken(null);
      onTokenChange?.(null);

      if (turnstileWidgetIdRef.current && window.turnstile) {
        window.turnstile.reset(turnstileWidgetIdRef.current);
      }

      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
        textareaRef.current.style.overflowY = "hidden";
      }
    },
    [message, isLoading, onSend, turnstileToken],
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

  const canSubmit =
    message.trim().length > 0 &&
    !isLoading &&
    Boolean(turnstileSiteKey) &&
    Boolean(turnstileToken);

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        "p-4 bg-surface-elevated border-t-4 border-brand-gold/70",
        className,
      )}
    >
      <div className="relative flex items-center gap-2 max-w-6xl mx-20">
        {/* Input container */}
        <div className="relative flex-1 flex">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => {
              const next = e.target.value.slice(0, MAX_MESSAGE_CHARS);
              setMessage(next);
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
            maxLength={MAX_MESSAGE_CHARS}
            style={{ maxHeight: `${MAX_TEXTAREA_HEIGHT}px` }}
          />
        </div>

        <div className="flex items-center gap-2">
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

          {turnstileSiteKey && (
            <>
              <div
                className={cn(
                  "flex items-center gap-3",
                  "rounded-md border border-surface-border bg-surface-elevated/70",
                  "px-3 py-2 text-xs",
                  turnstileToken ? "opacity-70" : "opacity-100",
                )}
              >
                <div className="flex items-center gap-2 text-text-secondary">
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full",
                      turnstileToken ? "bg-brand-green" : "bg-brand-gold",
                    )}
                    aria-hidden="true"
                  />
                  <span>
                    {turnstileToken ? "Verified" : "Human check required"}
                  </span>
                </div>
              </div>
              <div className="rounded-xl">
                <div ref={turnstileRef} />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Helper text */}
      <div className="text-xs text-text-secondary text-center mt-2 opacity-60 space-y-1">
        {!turnstileSiteKey && (
          <p>
            Turnstile site key is missing. Configure
            NEXT_PUBLIC_TURNSTILE_SITE_KEY.
          </p>
        )}
        {turnstileError && <p className="text-red-400">{turnstileError}</p>}
        {externalError && <p className="text-red-400">{externalError}</p>}
        <p>
          {message.length}/{MAX_MESSAGE_CHARS} characters &mdash; Press Enter to
          send, Shift+Enter for new line
        </p>
      </div>
    </form>
  );
}
