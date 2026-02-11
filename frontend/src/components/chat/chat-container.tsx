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
import { SwordIcon, BookIcon, MapIcon } from "./icons";

interface ChatContainerProps {
  /** Array of chat messages */
  messages: ChatMessageType[];
  /** Whether chat is loading */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
  onSelectSuggestedQuestion?: (question: string) => void;
}

export function ChatContainer({
  messages,
  isLoading = false,
  className,
  onSelectSuggestedQuestion,
}: ChatContainerProps) {
  const isEmpty = messages.length === 0;

  const { containerRef } = useAutoScroll<HTMLDivElement>({
    enabled: !isEmpty,
    dependencies: [messages.length, messages[messages.length - 1]?.content],
    smooth: true,
  });

  const EXAMPLE_QUESTIONS = [
    {
      icon: SwordIcon,
      text: "What happens in Chapter 1 of Fire Emblem?",
      shortText: "Chapter 1",
    },
    {
      icon: BookIcon,
      text: "Who are the main characters in the prologue?",
      shortText: "Characters",
    },
    {
      icon: MapIcon,
      text: "What are the objectives in Chapter 5?",
      shortText: "Objectives",
    },
  ];

  return (
    <div
      ref={containerRef}
      className={cn(
        "flex-1 overflow-y-auto",
        "scrollbar-thin scrollbar-thumb-surface-border",
        className,
      )}
    >
      {isEmpty ? (
        <div className="flex flex-col min-h-full">
          <EmptyState />
          <div className="w-full max-w-xl mx-auto px-4 pb-8">
            <p className="text-xs text-text-muted mb-2">Try asking:</p>
            <div className="grid gap-2 sm:grid-cols-2">
              {EXAMPLE_QUESTIONS.map((question) => {
                const Icon = question.icon;
                return (
                  <button
                    key={question.text}
                    type="button"
                    onClick={() => onSelectSuggestedQuestion?.(question.text)}
                    className="group flex items-center gap-3 border border-brand-gold/70 bg-surface-elevated/60 px-3 py-2.5 text-left text-sm text-text-secondary hover:text-text-primary hover:bg-surface-muted/60 transition-colors"
                  >
                    <Icon className="w-5 h-5 flex-shrink-0 text-brand-green" />
                    <div className="flex flex-col">
                      <span className="font-medium">{question.shortText}</span>
                      <span className="text-xs text-text-muted line-clamp-2">
                        {question.text}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
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
