 # Backend Documentation

 ## Overview

 The backend is a FastAPI service that ingests Fire Emblem chapter data from the Fire Emblem wiki, parses it into structured records, stores it in Postgres with pgvector embeddings, and exposes chat + ingestion APIs for the frontend and ops workflows.

 Core entry points (paths are relative to repo root):
 - `backend/app/main.py` sets up FastAPI, CORS, docs auth, and routes.
 - `backend/app/routes/` defines API endpoints.
 - `backend/app/controllers/` orchestrates ingestion and chat flows.

 ## High-Level Flow

 ### Ingestion (Wiki → DB)
 1. API calls MediaWiki to fetch HTML or wikitext.
 2. Parsers extract infobox, summary, sections, and tables.
 3. Ingestion builds Chapter + ChapterChunk records.
 4. Optional embeddings are created via OpenAI.
 5. Records are stored in Postgres, and pgvector holds embeddings.

 ### RAG Chat (User → Answer)
 1. The API validates limits, Turnstile, and rate limits.
 2. The user query is embedded with OpenAI.
 3. Similar ChapterChunks are retrieved via pgvector cosine distance.
 4. Context is built from chunk content + metadata.
 5. OpenAI chat completion generates the response.
 6. Response returns with model usage and filtered sources.

 ## Architecture and Key Modules

 ### Configuration
 - `backend/app/config.py` loads settings from .env files and environment variables.
 - `backend/.env.example` documents required settings, including OpenAI, DB, Redis, and Turnstile.

 ### Database
 - `backend/app/db.py` configures SQLAlchemy, checks DB connectivity, and enables pgvector.
 - `backend/app/models.py` defines Chapter and ChapterChunk tables.

 **Chapter**
 - pageid, title, infobox_title, game, objective, units_allowed, units_gained, boss
 - source_url and raw_infobox (JSON)

 **ChapterChunk**
 - chapter_id, section_title, kind (summary/infobox/section), chunk_index, text, embedding
 - unique constraint per chapter/kind/chunk_index

 ### Wiki Ingestion
 - `backend/app/mediawiki_client.py` fetches pages via the MediaWiki API.
 - `backend/app/parsers.py` extracts infobox fields, sections, summary, and tables from HTML or wikitext.
 - `backend/app/chapter_ingest.py` builds DB records and embeddings.
 - `backend/app/controllers/wiki_controller.py` ties API inputs to ingestion logic.

 ### RAG and OpenAI
 - `backend/app/rag_service.py` retrieves similar chunks and builds a bounded context string.
 - `backend/app/openai_service.py` wraps embeddings and chat completions.
 - `backend/app/controllers/chat_controller.py` runs plain or RAG chat and filters sources.

 ### Security and Limits
 - `backend/app/rate_limit.py` enforces IP limits, per-session quotas, and cooldowns via Redis.
 - `backend/app/security/turnstile.py` verifies Cloudflare Turnstile tokens.
 - `backend/app/docs_auth.py` protects `/docs` and `/redoc` in production or when enabled.

 ## API Endpoints

 ### System

 | Method | Path        | Description                                           |
 | ------ | ----------- | ----------------------------------------------------- |
 | GET    | /health     | Status, environment, DB status, pgvector availability |
 | GET    | /config     | Non-sensitive configuration for debugging            |

 ### Chat

 | Method | Path       | Body type     | Purpose                                                     |
 | ------ | ---------- | ------------ | ----------------------------------------------------------- |
 | POST   | /chat      | ChatRequest  | Direct OpenAI chat without RAG                              |
 | POST   | /chat/rag  | RagChatRequest | RAG chat with retrieval and contextualized completion      |

 **Common enforcement**

 | Control                 | Source            | Effect                                                  |
 | ----------------------- | ----------------- | ------------------------------------------------------- |
 | request_max_chars       | config            | Rejects messages that are too long (400 error)         |
 | rag_top_k_max           | config            | Clamps top_k for /chat/rag                             |
 | IP + session rate limit | Redis + rate_limit.py | 429 on overuse                                      |
 | Turnstile validation    | security/turnstile.py | Rejects when human verification fails or misconfigured |

 ### Wiki and Ingestion

 | Method | Path                          | Key query params                            | Description                                      |
 | ------ | ----------------------------- | ------------------------------------------- | ------------------------------------------------ |
 | GET    | /wiki/category/{category_name} | limit, include_html, as_markdown, raw      | Fetch category pages and optionally parsed tables |
 | GET    | /wiki/page/{title}           | include_html, raw                           | Parse chapter fields from HTML                   |
 | GET    | /wiki/page/{title}/wikitext  | raw                                         | Parse summary, infobox, sections from wikitext  |
 | POST   | /wiki/page/{title}/ingest    | generate_embeddings                          | Ingest chapter and create embeddings            |
 | POST   | /wiki/page/{title}/reingest  | generate_embeddings                          | Rebuild chapter and chunks for an existing page |
 | GET    | /chapters                    | –                                           | List all ingested chapters grouped by game      |

 ## Data and Retrieval Details

 - Chapter chunks are created from summary, infobox fields, and section lines.
 - Embeddings are generated in batches; failures store chunks without embeddings.
 - RAG retrieval uses pgvector cosine distance, sorted ascending and limited by top_k.
 - Sources are filtered to only return chapters whose title or game appears in the user message.

 ## Operational Notes

 - Postgres must have pgvector enabled; init_db() attempts to install it automatically.
 - Redis is required for rate limiting; missing REDIS_URL returns 500 for chat routes.
 - Turnstile requires TURNSTILE_SECRET_KEY; frontend provides the site key token.
 - Docs auth can be enabled via DOCS_AUTH_ENABLED or auto-enabled in production when username/password are set.
