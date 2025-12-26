/**
 * API-related types
 */

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
