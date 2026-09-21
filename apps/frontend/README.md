# QA Workspace frontend

React 19 + TypeScript + Vite. Currently the Vite template screen wrapped in the application foundation; there are no product screens yet.

## Run

Run everything through Docker Compose from the repository root (`docker compose up --build`). The app is served on http://localhost:5173. `VITE_API_URL` (the backend base URL, without `/api`) is set by `compose.yaml`; see `.env.example` for local overrides.

## Verify

From the repository root:

```
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run test
docker compose exec -T frontend npm run build
```

## Structure

- `src/app/`: `AppProviders.tsx` (providers), `router.tsx` (routes), `queryClient.ts`.
- `src/lib/api/client.ts`: `apiRequest` and `ApiError`, the single way to call the backend.
- `src/test/`: Vitest setup and the MSW server. Tests sit beside the code they cover.

Conventions and decisions: `docs/decisions.md` and the `qa-workspace-frontend-patterns` skill.
