"use client";

/**
 * Main Chat Page
 * 
 * Primary interface for the Fire Emblem RAG chat application.
 * Features a collapsible sidebar layout inspired by modern chat UIs.
 */

import { useCallback } from "react";
import { useChat } from "@/hooks/use-chat";
import { 
  Sidebar, 
  ChatContainer, 
  ChatInput,
  EmptyState 
} from "@/components/chat";
import { MainLogo } from "@/components/brand/main-logo";

export default function ChatPage() {
  const { 
    messages, 
    isLoading, 
    sendMessage, 
    clearMessages
  } = useChat({
    topK: 8,
    temperature: 0.3,
  });

  const handleSendMessage = useCallback(
    (content: string) => {
      sendMessage(content);
    },
    [sendMessage]
  );

  const handleSelectQuestion = useCallback(
    (question: string) => {
      sendMessage(question);
    },
    [sendMessage]
  );

  return (
    <div className="relative isolate flex h-screen max-h-screen overflow-hidden bg-surface-base">
      {/* Background layer (orbs + watermark) */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        {/* Gradient orbs */}
        <div className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 bg-brand-teal/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 bg-brand-green/5 rounded-full blur-3xl" />

        {/* Center watermark (only when conversation exists) */}
        {messages.length > 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <MainLogo variant="watermark" className="opacity-[0.12] scale-[1.35]" />
          </div>
        )}
      </div>

      {/* Sidebar */}
      <div className="relative z-10">
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
          {messages.length === 0 ? (
            <EmptyState />
          ) : (
            <ChatContainer 
              messages={messages} 
              isLoading={isLoading} 
            />
          )}
        </div>

        {/* Input Area */}
        <ChatInput 
          onSend={handleSendMessage} 
          isLoading={isLoading}
          placeholder="Ask about Fire Emblem chapters..."
        />
      </main>
    </div>
  );
}
