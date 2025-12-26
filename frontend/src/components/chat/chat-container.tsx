"use client";

/**
 * ChatContainer Component
 * 
 * Main container for the chat interface.
 * Handles message list display, auto-scrolling, and empty state.
 */

import { useAutoScroll } from "@/hooks/use-auto-scroll";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types";
import { ChatMessage } from "./chat-message";
import { EmptyState } from "./empty-state";

interface ChatContainerProps {
  /** Array of chat messages */
  messages: ChatMessageType[];
  /** Whether chat is loading */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function ChatContainer({
  messages,
  isLoading = false,
  className,
}: ChatContainerProps) {
  const { containerRef } = useAutoScroll<HTMLDivElement>({
    dependencies: [messages.length, messages[messages.length - 1]?.content],
    smooth: true,
  });

  const isEmpty = messages.length === 0;

  return (
    <div
      ref={containerRef}
      className={cn(
        "flex-1 overflow-y-auto",
        "scrollbar-thin scrollbar-thumb-surface-border",
        className
      )}
    >
      {isEmpty ? (
        <EmptyState />
      ) : (
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          
          {/* Scroll anchor */}
          <div className="h-4" aria-hidden="true" />
        </div>
      )}
    </div>
  );
}
