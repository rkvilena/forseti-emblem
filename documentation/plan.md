# Improvement Plan

This list may change as priorities evolve.

## Planned

### Frontend and API

- Add a curated roadmap/“What’s New” page using repo-maintained notes; keep planned work distinct from shipped updates. Consider GitHub Releases integration later.
- Add frontend tests for chat persistence, retry, and error handling (later).

### Infrastructure

- Migrate production deployment to GitHub Actions.
- Refactor frontend code.

## Completed

### v0.2.0

- Adopted TanStack Query for API/server state, starting with the chapter list; kept Next.js routing and avoided adding Redux.
- Generated frontend API types from FastAPI's OpenAPI schema to avoid maintaining duplicate backend schemas by hand.
- Improved chapter browsing: added client-side search by game/chapter name and links to chapter source references. Exposed `source_url` in the chapters endpoint first.

### v0.2.1

- Refined linked chapter styling: white by default, gold on hover, with a visible keyboard-focus ring.
