/**
 * API-related types
 *
 * Backend request/response contracts come from the checked-in OpenAPI types in
 * `generated-api.ts`. Regenerate them with `npm run generate:api-types`.
 * Types defined directly here are frontend-only or describe endpoints that the
 * backend does not model with a Pydantic schema.
 */

import type { components } from "./generated-api";

export interface HealthResponse {
  status: string;
  environment: string;
  database: string;
  pgvector: string;
}

export interface ApiError {
  detail: string;
}

export interface ConfigResponse {
  environment: string;
  database_host: string;
  database_port: number;
  database_name: string;
  openai_embedding_model: string;
  openai_chat_model: string;
  openai_api_key_set: boolean;
  debug: boolean;
  log_level: string;
}

export type ChapterSummary = components["schemas"]["ChapterSummary"];

export type GameChaptersGroup = components["schemas"]["GameChaptersGroup"];

export type ChapterListResponse = components["schemas"]["ChapterListResponse"];
