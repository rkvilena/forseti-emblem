/**
 * Chat-related TypeScript types
 * Mirrors the backend Pydantic schemas
 */

export interface ChatUsage {
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
}

export interface ChatResponse {
  response: string;
  model: string;
  usage: ChatUsage | null;
}

export interface ChatRequest {
  message: string;
  system_prompt?: string | null;
  context?: string | null;
  temperature?: number;
}

export interface RagChatRequest {
  message: string;
  top_k?: number;
  temperature?: number;
  system_prompt?: string | null;
}

// Frontend-specific types for UI state
export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  usage?: ChatUsage | null;
  model?: string;
  isStreaming?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}
