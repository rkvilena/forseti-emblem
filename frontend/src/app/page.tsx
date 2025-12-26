"use client";

/**
 * Main Chat Page
 * 
 * Primary interface for the Fire Emblem RAG chat application.
 */

import { useCallback } from "react";
import { useChat } from "@/hooks/use-chat";
import { 
  Header, 
  ChatContainer, 
  ChatInput,
  EmptyState 
} from "@/components/chat";

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
    <main className="flex flex-col h-screen max-h-screen overflow-hidden">
      {/* Header */}
      <Header 
        onClearChat={clearMessages} 
        hasMessages={messages.length > 0} 
      />

      {/* Chat Area */}
      <div className="flex-1 flex flex-col min-h-0">
        {messages.length === 0 ? (
          <EmptyState onSelectQuestion={handleSelectQuestion} />
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

      {/* Background decoration */}
      <div className="fixed inset-0 pointer-events-none -z-10 overflow-hidden">
        {/* Gradient orbs */}
        <div className="absolute -top-1/4 -right-1/4 w-1/2 h-1/2 bg-primary-600/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 -left-1/4 w-1/2 h-1/2 bg-accent-500/5 rounded-full blur-3xl" />
        
        {/* Grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)
            `,
            backgroundSize: "50px 50px",
          }}
        />
      </div>
    </main>
  );
}
