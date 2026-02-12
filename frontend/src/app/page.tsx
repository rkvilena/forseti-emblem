"use client";

/**
 * Main Chat Page
 *
 * Primary interface for the Fire Emblem RAG chat application.
 * Features a collapsible sidebar layout inspired by modern chat UIs.
 */

import { useCallback, useRef, useState } from "react";
import { useChat } from "@/hooks/use-chat";
import { Sidebar, ChatContainer, ChatInput } from "@/components/chat";
import { MainLogo } from "@/components/brand/main-logo";

export default function ChatPage() {
  const { messages, isLoading, sendMessage, clearMessages } = useChat({
    topK: 8,
    temperature: 0.3,
  });

  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileNotice, setTurnstileNotice] = useState<string | null>(null);
  const turnstileWidgetIdRef = useRef<string | null>(null);

  const handleSendMessage = useCallback(
    (content: string, turnstileToken: string) => {
      setTurnstileNotice(null);
      sendMessage(content, turnstileToken);
    },
    [sendMessage],
  );

  const handleSelectQuestion = useCallback(
    (question: string) => {
      if (!turnstileToken) {
        setTurnstileNotice("Please complete the Turnstile check to continue.");
        return;
      }

      setTurnstileNotice(null);
      sendMessage(question, turnstileToken);
      setTurnstileToken(null);

      if (turnstileWidgetIdRef.current && window.turnstile) {
        window.turnstile.reset(turnstileWidgetIdRef.current);
      }
    },
    [sendMessage, turnstileToken],
  );

  return (
    <div className="relative isolate flex h-screen max-h-screen overflow-hidden bg-surface-base parchment-bg">
      {/* Background layer (orbs + watermark) */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        {/* Gradient orbs */}
        <div className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 bg-brand-teal/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 bg-brand-green/5 rounded-full blur-3xl" />

        {/* Center watermark (only when conversation exists) */}
        {messages.length > 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <MainLogo
              variant="watermark"
              className="opacity-[0.12] scale-[1.35]"
            />
          </div>
        )}
      </div>

      {/* Sidebar */}
      <div className="relative z-10 parchment-panel">
        <Sidebar
          onSelectQuestion={handleSelectQuestion}
          onClearChat={clearMessages}
          hasMessages={messages.length > 0}
        />
      </div>

      {/* Main Content */}
      <main className="relative z-10 flex-1 flex flex-col min-w-0">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col min-h-0">
          <ChatContainer
            messages={messages}
            isLoading={isLoading}
            onSelectSuggestedQuestion={handleSelectQuestion}
          />
        </div>

        {/* Input Area */}
        <ChatInput
          onSend={handleSendMessage}
          onTokenChange={setTurnstileToken}
          onWidgetReady={(widgetId) => {
            turnstileWidgetIdRef.current = widgetId;
          }}
          externalError={turnstileNotice}
          isLoading={isLoading}
          placeholder="Ask about Fire Emblem chapters..."
        />
      </main>
    </div>
  );
}
