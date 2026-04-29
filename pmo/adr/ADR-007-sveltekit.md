# ADR-007 — Frontend Framework: SvelteKit over React / Vue

**Date:** April 2026
**Status:** Accepted

## Context

StreamForge needs a web UI for browsing datasets, executing SQL queries, viewing features, and monitoring ingestion. The UI is a supporting component — not the focal point of the project — so it must be fast to build, simple to structure, and responsive without heavy boilerplate.

## Decision

Use **SvelteKit** (with Vite) as the frontend framework.

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| React (Create React App / Vite) | More boilerplate for state management; hooks-based reactivity is more verbose than Svelte's reactive declarations for a data-display-heavy UI |
| Next.js | Server-side rendering features are unnecessary for a local-only analytics UI; adds framework complexity that doesn't benefit this use case |
| Vue 3 | Solid choice, but SvelteKit offers cleaner component syntax and faster build output for a project this size |
| Vanilla JS | Too low-level for building a table-heavy, API-driven UI efficiently as a solo developer |

## Consequences

**Benefits:**
- Svelte compiles to vanilla JS — no virtual DOM overhead, smaller bundle, fast initial load
- SvelteKit's file-based routing keeps page structure simple and navigable
- Reactive assignments (`$:`) make it easy to bind API responses to UI without Redux or Pinia boilerplate
- Vite provides fast hot-module reload during development
- TailwindCSS pairs well with Svelte for rapid UI styling

**Trade-offs:**
- Smaller ecosystem and community than React — fewer ready-made component libraries for complex data visualizations
- SvelteKit's server-side features (load functions, form actions) are not leveraged since the UI hits the FastAPI backend directly; this is a deliberate simplification
