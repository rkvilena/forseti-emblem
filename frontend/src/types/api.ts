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

export interface ChapterSummary {
  id: number;
  title: string;
  infobox_title: string | null;
  game: string | null;
}

export interface GameChaptersGroup {
  game: string | null;
  chapters: ChapterSummary[];
}

export interface ChapterListResponse {
  total_chapters: number;
  games: GameChaptersGroup[];
}
