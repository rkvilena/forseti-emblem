# Forsetiemblem Frontend

Next.js frontend for the Fire Emblem RAG chat application.

> For architecture, chat lifecycle, API integration, and design decisions, see [documentation/frontend.md](../documentation/frontend.md).

## Prerequisites

- **Node.js 18+** and npm
- A running backend — see [backend/README.md](../backend/README.md)

## Local Setup

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open **http://localhost:3000**.

### Environment Variables

| Name | Description | Default |
| ---- | ----------- | ------- |
| `NEXT_PUBLIC_API_URL` | Backend base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | Turnstile site key for the chat widget | value from Cloudflare |
| `NEXT_PUBLIC_CHAT_STORAGE_KEY` | Currently unused — the chat hook hardcodes `forsetiemblem_chat_history_v1` | — |

The canonical annotated list lives in `.env.example`.

## Commands

| Command | Description |
| ------- | ----------- |
| `npm run dev` | Start dev server with Turbopack |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Run TypeScript type checking |
| `npm run format` | Prettier formatting |

Or use `./start.sh`, which installs dependencies if needed and starts the dev server.

## Project Structure

```
frontend/
├── src/
│   ├── app/           # Next.js App Router pages
│   ├── components/    # React components
│   │   └── chat/      # Chat-specific components
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utilities and API client
│   ├── styles/        # Global styles and theme
│   └── types/         # TypeScript type definitions
└── public/            # Static assets
```

## Docker Development

```bash
# From repo root (requires backend/.env to exist)
docker compose -f infrastructure/compose/local.dev.yml up --build
```

> Note: the Compose `api` service references `backend/Dockerfile.dev`, which doesn't currently exist in this repository, so that build will fail — use the local setup above (and start the backend directly) for now.

## Troubleshooting

| Symptom | Cause and fix |
| ------- | ------------- |
| Chat fails to send / network errors | Backend not running or `NEXT_PUBLIC_API_URL` doesn't match it |
| Turnstile blocks sending | Backend has `TURNSTILE_ENABLED=true` but the site key is missing or wrong in `.env.local` |
| Chat history doesn't persist | Storage key is hardcoded (`forsetiemblem_chat_history_v1`); clearing the sidebar chat removes stored history |
| CORS errors | Backend `CORS_ALLOWED_ORIGIN` must match the frontend origin |

## Related Documentation

- [Frontend architecture](../documentation/frontend.md) — how the frontend works
- [Backend guide](../backend/README.md) — backend setup
- [Root README](../README.md) — whole-project overview and quick start
