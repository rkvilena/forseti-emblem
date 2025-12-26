"use client";

/**
 * ChatMessage Component
 * 
 * Renders individual chat messages with styling based on role.
 * Supports markdown rendering for assistant responses.
 */

import { memo } from "react";
import ReactMarkdown from "react-markdown";
import { cn, formatTimestamp } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types";
import { UserIcon, BotIcon } from "./icons";
import { TypingIndicator } from "./typing-indicator";

interface ChatMessageProps {
  message: ChatMessageType;
  /** Whether to show timestamp */
  showTimestamp?: boolean;
}

export const ChatMessage = memo(function ChatMessage({
  message,
  showTimestamp = true,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isStreaming = message.isStreaming;

  return (
    <div
      className={cn(
        "group flex gap-3 animate-fade-in",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center",
          isUser 
            ? "bg-primary-600/20 text-primary-400" 
            : "bg-accent-500/20 text-accent-400"
        )}
      >
        {isUser ? (
          <UserIcon className="w-5 h-5" />
        ) : (
          <BotIcon className="w-5 h-5" />
        )}
      </div>

      {/* Message content */}
      <div
        className={cn(
          "relative max-w-[80%] px-4 py-3",
          isUser ? "message-user" : "message-assistant"
        )}
      >
        {isStreaming ? (
          <TypingIndicator />
        ) : (
          <>
            {/* Message text */}
            <div className={cn(
              "prose prose-invert prose-sm max-w-none",
              "prose-p:my-2 prose-p:leading-relaxed",
              "prose-headings:text-text-primary prose-headings:font-display",
              "prose-strong:text-accent-400",
              "prose-code:text-primary-300 prose-code:bg-surface-muted prose-code:px-1 prose-code:rounded",
              "prose-pre:bg-surface-base prose-pre:border prose-pre:border-surface-border",
              "prose-ul:my-2 prose-li:my-0",
              "prose-a:text-primary-400 prose-a:no-underline hover:prose-a:underline"
            )}>
              {isUser ? (
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
              ) : (
                <ReactMarkdown>{message.content}</ReactMarkdown>
              )}
            </div>

            {/* Metadata */}
            {showTimestamp && (
              <div className={cn(
                "flex items-center gap-2 mt-2 text-xs text-text-muted",
                "opacity-0 group-hover:opacity-100 transition-opacity"
              )}>
                <span>{formatTimestamp(message.timestamp)}</span>
                {message.model && !isUser && (
                  <>
                    <span>•</span>
                    <span className="font-mono">{message.model}</span>
                  </>
                )}
                {message.usage?.total_tokens && !isUser && (
                  <>
                    <span>•</span>
                    <span>{message.usage.total_tokens} tokens</span>
                  </>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
});
