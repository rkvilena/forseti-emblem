# Forsetiemblem Frontend

Next.js frontend for the Fire Emblem RAG chat application.

## Features

- 🔥 **Next.js 15** with Turbopack for fast development
- 🎨 **Tailwind CSS** with custom Fire Emblem themed design system
- 💬 **Chat UI** optimized for RAG interactions
- 📱 **Responsive** mobile-first design
- 🔄 **Auto-scroll** and typing indicators
- 🎯 **TypeScript** for type safety

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Local Development

```bash
# Install dependencies
npm install

# Start development server (with Turbopack for fast refresh)
npm run dev

# Or use the start script
./start.sh
```

The app will be available at [http://localhost:3000](http://localhost:3000).

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Docker Development

```bash
# From repo root
docker compose -f infrastructure/compose/local.dev.yml up --build
```

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
├── public/            # Static assets
└── Dockerfile         # Production Docker image
```

## Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server with Turbopack |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | Run TypeScript type checking |

## Theme

The design system uses a Fire Emblem-inspired color palette:

- **Primary**: Royal blue tones (Forseti's wind magic)
- **Accent**: Sacred gold (nobility and crests)
- **Crimson**: Action highlights
- **Surface**: Dark parchment-like backgrounds

All colors are centralized in `tailwind.config.ts` and `src/styles/theme.ts`.
