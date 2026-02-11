"use client";

/**
 * ChatMessage Component
 *
 * Renders individual chat messages with styling based on role.
 * Supports markdown rendering for assistant responses.
 */

import { memo } from "react";
import markdownit from "markdown-it";
import { cn, formatTimestamp } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types";
import { UserIcon, BotIcon } from "./icons";
import { TypingIndicator } from "./typing-indicator";

const md = markdownit({
  linkify: true,
  typographer: true,
  breaks: true,
});

function unwrapMarkdownFence(text: string) {
  const trimmed = text.trim();
  const match = trimmed.match(
    /^```(?:\s*(?:markdown|md))?\s*[\r\n]+([\s\S]*?)\r?\n```$/i,
  );
  if (!match) return text;
  return match[1];
}

function normalizeMarkdown(text: string) {
  const input = unwrapMarkdownFence(text);
  const lines = input.replace(/\r\n/g, "\n").split("\n");
  let inFence = false;
  let minIndent = Infinity;

  for (const line of lines) {
    if (line.trim() === "") continue;
    const fence = line.trimStart().startsWith("```");
    if (fence) {
      inFence = !inFence;
      continue;
    }
    if (inFence) continue;

    const match = line.match(/^[\t ]+/);
    if (!match) {
      minIndent = 0;
      break;
    }

    const indent = match[0].replace(/\t/g, "    ").length;
    minIndent = Math.min(minIndent, indent);
  }

  if (minIndent < 4 || minIndent === Infinity) return input;

  inFence = false;
  return lines
    .map((line) => {
      const fence = line.trimStart().startsWith("```");
      if (fence) {
        inFence = !inFence;
        return line;
      }
      if (inFence || line.trim() === "") return line;

      const expanded = line.replace(/\t/g, "    ");
      return expanded.startsWith(" ".repeat(minIndent))
        ? expanded.slice(minIndent)
        : line;
    })
    .join("\n");
}

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
  const showTyping = Boolean(isStreaming && !message.content);
  const renderedContent = isUser
    ? message.content
    : normalizeMarkdown(message.content);

  return (
    <div
      className={cn(
        "group flex gap-3 animate-fade-in",
        isUser ? "flex-row-reverse" : "flex-row",
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center",
          isUser
            ? "bg-brand-teal/20 text-brand-teal"
            : "bg-brand-green/20 text-brand-green",
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
          "relative max-w-[80%] px-4 py-3 text-text-primary",
          isUser ? "message-user" : "message-assistant",
        )}
      >
        {showTyping ? (
          <TypingIndicator />
        ) : (
          <>
            {/* Message text */}
            <div
              className={cn(
                isUser
                  ? "whitespace-pre-wrap break-words"
                  : [
                      "prose prose-sm max-w-none font-[inherit]",
                      "prose-p:my-2 prose-p:leading-relaxed prose-p:text-text-primary",
                      "prose-headings:text-text-primary prose-headings:font-brand",
                      "prose-strong:text-brand-teal",
                      "prose-code:text-brand-blue prose-code:bg-surface-muted prose-code:px-1 prose-code:rounded",
                      "prose-pre:bg-surface-base prose-pre:border prose-pre:border-surface-border",
                      "prose-ul:my-2 prose-li:my-0 prose-li:leading-relaxed prose-li:text-text-primary prose-li:marker:text-brand-teal",
                      "prose-ol:my-2 prose-ol:text-text-primary",
                      "prose-a:text-brand-blue prose-a:no-underline hover:prose-a:underline",
                      "dark:prose-invert",
                    ],
              )}
            >
              {isUser ? (
                <p className="whitespace-pre-wrap break-words text-text-primary">
                  {renderedContent}
                </p>
              ) : (
                <div
                  className="markdown-body"
                  dangerouslySetInnerHTML={{
                    __html: md.render(renderedContent),
                  }}
                />
              )}
            </div>

            {/* Metadata */}
            {showTimestamp && (
              <div
                className={cn(
                  "flex items-center gap-2 mt-2 text-xs text-text-muted",
                  "opacity-0 group-hover:opacity-100 transition-opacity",
                )}
              >
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
