/**
 * Chat-related TypeScript types
 *
 * Backend request/response contracts come from the checked-in OpenAPI types in
 * `generated-api.ts`. Regenerate them with `npm run generate:api-types`.
 */

import type { components } from "./generated-api";

export type ChatUsage = components["schemas"]["ChatUsage"];

export type SourceReference = components["schemas"]["SourceReference"];

export type ChatResponse = components["schemas"]["ChatResponse"];

export type ChatRequest = components["schemas"]["ChatRequest"];

export type RagChatRequest = components["schemas"]["RagChatRequest"];

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
  sources?: SourceReference[] | null;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}
