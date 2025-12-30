"use client";

/**
 * useChat Hook
 * 
 * Manages chat state and API communication for the RAG chat interface.
 * Provides a clean interface for sending messages and managing conversation history.
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { apiClient, ApiClientError } from "@/lib/api-client";
import { generateId } from "@/lib/utils";
import type { ChatMessage, RagChatRequest, ChatUsage } from "@/types";

interface UseChatOptions {
  /** Number of chunks to retrieve for RAG (1-30) */
  topK?: number;
  /** Temperature for response generation (0-2) */
  temperature?: number;
  /** Custom system prompt override */
  systemPrompt?: string | null;
  /** Callback when an error occurs */
  onError?: (error: Error) => void;
}

interface UseChatReturn {
  /** Array of messages in the conversation */
  messages: ChatMessage[];
  /** Whether a message is currently being sent */
  isLoading: boolean;
  /** Current error if any */
  error: Error | null;
  /** Send a new message */
  sendMessage: (content: string) => Promise<void>;
  /** Clear all messages */
  clearMessages: () => void;
  /** Retry the last failed message */
  retryLastMessage: () => Promise<void>;
}

export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const {
    topK = 8,
    temperature = 0.3,
    systemPrompt = null,
    onError,
  } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  // Store last user message for retry functionality
  const lastUserMessageRef = useRef<string | null>(null);
  const streamTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (streamTimerRef.current) {
        window.clearInterval(streamTimerRef.current);
        streamTimerRef.current = null;
      }
    };
  }, []);

  const streamAssistantMessage = useCallback(
    async (args: {
      messageId: string;
      fullText: string;
      model?: string;
      usage?: ChatUsage | null;
    }) => {
      const { messageId, fullText, model, usage } = args;

      if (streamTimerRef.current) {
        window.clearInterval(streamTimerRef.current);
        streamTimerRef.current = null;
      }

      const text = fullText ?? "";
      const totalLength = text.length;

      // Keep updates bounded for long responses (~<=200 updates).
      const chunkSize = Math.min(64, Math.max(8, Math.ceil(totalLength / 200)));
      const tickMs = 100;

      return await new Promise<void>((resolve) => {
        let index = 0;

        const push = () => {
          index = Math.min(totalLength, index + chunkSize);
          const nextContent = text.slice(0, index);

          setMessages((prev: ChatMessage[]) =>
            prev.map((msg: ChatMessage) =>
              msg.id === messageId
                ? {
                    ...msg,
                    content: nextContent,
                    isStreaming: index < totalLength,
                    ...(index >= totalLength
                      ? {
                          model,
                          usage,
                        }
                      : null),
                  }
                : msg
            )
          );

          if (index >= totalLength) {
            if (streamTimerRef.current) {
              window.clearInterval(streamTimerRef.current);
              streamTimerRef.current = null;
            }
            resolve();
          }
        };

        // First tick quickly, so typing indicator doesn't linger.
        push();
        if (totalLength <= chunkSize) {
          resolve();
          return;
        }

        streamTimerRef.current = window.setInterval(push, tickMs);
      });
    },
    []
  );

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    setError(null);
    setIsLoading(true);
    lastUserMessageRef.current = content;

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev: ChatMessage[]) => [...prev, userMessage]);

    // Create placeholder for assistant response
    const assistantMessageId = generateId();
    const placeholderMessage: ChatMessage = {
      id: assistantMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev: ChatMessage[]) => [...prev, placeholderMessage]);

    try {
      const request: RagChatRequest = {
        message: content.trim(),
        top_k: topK,
        temperature,
        system_prompt: systemPrompt,
      };

      const response = await apiClient.chatRag(request);

      // Stream the assistant response on the client (backend can stay non-streaming).
      await streamAssistantMessage({
        messageId: assistantMessageId,
        fullText: response.response,
        model: response.model,
        usage: response.usage,
      });
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Unknown error occurred");
      
      // Remove the placeholder message on error
      setMessages((prev: ChatMessage[]) => prev.filter((msg: ChatMessage) => msg.id !== assistantMessageId));
      
      setError(error);
      onError?.(error);

      // Create an error message to display
      if (err instanceof ApiClientError) {
        const errorMessage: ChatMessage = {
          id: generateId(),
          role: "assistant",
          content: `⚠️ **Error**: ${err.detail || err.message}\n\nPlease try again or check if the backend is running.`,
          timestamp: new Date(),
        };
        setMessages((prev: ChatMessage[]) => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, topK, temperature, systemPrompt, onError, streamAssistantMessage]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
    lastUserMessageRef.current = null;
  }, []);

  const retryLastMessage = useCallback(async () => {
    if (lastUserMessageRef.current) {
      // Remove the last two messages (user + error/response)
      setMessages((prev: ChatMessage[]) => prev.slice(0, -2));
      await sendMessage(lastUserMessageRef.current);
    }
  }, [sendMessage]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    retryLastMessage,
  };
}
