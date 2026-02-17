 # Frontend Documentation

 ## Overview

 The frontend is a Next.js 15 app that provides the Fire Emblem chat experience and supporting pages. It integrates Cloudflare Turnstile for human verification, calls the backend RAG API, and streams the assistant response on the client for a typing effect.

 Core entry points (paths are relative to repo root):
 - `frontend/src/app/layout.tsx` defines global layout, fonts, and loads Turnstile.
 - `frontend/src/app/page.tsx` is the main chat UI.

 ## Pages and Routing

 Pages live in `frontend/src/app` using the App Router.

 | Route       | File path                          | Purpose                                       |
 | ---------- | ----------------------------------- | --------------------------------------------- |
 | /          | `frontend/src/app/page.tsx`         | Chat UI and RAG conversation flow             |
 | /chapters  | `frontend/src/app/chapters/page.tsx` | Lists ingested chapters grouped by game       |
 | /about     | `frontend/src/app/about/page.tsx`   | About the project                             |
 | /disclaimer| `frontend/src/app/disclaimer/page.tsx` | Legal and safety disclaimer                 |
 | /settings  | `frontend/src/app/settings/page.tsx` | UI settings and user preferences             |

 ## Core Chat Flow

 1. User composes a message in ChatInput.
 2. Turnstile provides a token (required if enabled).
 3. useChat adds the user message and an assistant placeholder.
 4. apiClient calls POST /chat/rag with message, top_k, temperature, and token.
 5. The full response is streamed into the placeholder for a typing effect.
 6. Messages are persisted in localStorage for session restoration.

 Key modules (relative paths):
 - `frontend/src/hooks/use-chat.ts` manages message state, persistence, retries, and streaming.
 - `frontend/src/lib/api-client.ts` wraps backend requests and error handling.
 - `frontend/src/components/chat/` renders message list, input, and sidebar UI.

 ## Turnstile Integration

 - Turnstile script loads in RootLayout.
 - ChatInput renders a Turnstile widget using NEXT_PUBLIC_TURNSTILE_SITE_KEY.
 - The token is required to send messages when Turnstile is enabled in the backend.
 - Tokens are reset after a successful send.

 Relevant files:
 - `frontend/src/components/chat/chat-input.tsx`
 - `frontend/src/types/turnstile.d.ts`

 ## Data and Types

 - Types mirror backend Pydantic schemas for consistent payloads.
 - `frontend/src/types/api.ts` contains API responses.
 - `frontend/src/types/chat.ts` contains chat message shapes and RAG request types.

 ## API Usage from the Frontend

 | Method | Path       | Usage in frontend                       |
 | ------ | ---------- | ---------------------------------------- |
 | GET    | /health    | Health checks via `apiClient.health()`  |
 | POST   | /chat/rag  | Main chat API via `apiClient.chatRag()` |
 | GET    | /chapters  | Chapters list via `apiClient.listChapters()` |

 The base URL is `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000`.

 ## UI Structure and Behavior

 - Sidebar provides navigation and utility controls (theme, text size, clear chat).
 - ChatContainer renders the conversation and auto-scrolls.
 - ChatMessage supports markdown rendering for assistant responses.
 - Themes are applied using CSS variables and Tailwind classes.

 Key files:
 - `frontend/src/components/chat/sidebar.tsx`
 - `frontend/src/components/chat/chat-container.tsx`
 - `frontend/src/components/chat/chat-message.tsx`
 - `frontend/src/hooks/use-theme.ts`
 - `frontend/src/styles/globals.css`

 ## Environment Variables

 | Name                        | Description                                             | Example/default               |
 | --------------------------- | ------------------------------------------------------- | ----------------------------- |
 | NEXT_PUBLIC_API_URL         | Backend base URL                                        | `http://localhost:8000`       |
 | NEXT_PUBLIC_TURNSTILE_SITE_KEY | Turnstile site key for the widget                   | value from Cloudflare         |
 | NEXT_PUBLIC_CHAT_STORAGE_KEY | Reserved for client storage naming (currently unused) | `forsetiemblem-dev-chat-messages` |
 | NODE_ENV                    | Standard Next.js environment flag                       | `development` / `production`  |

 See `frontend/.env.example` for the canonical list.
