# QA Workspace

QA Workspace is a full-stack application for managing product requirements and the QA process in one place.

Users can create feature specifications, analyze requirements with AI, review detected ambiguities and missing details, generate acceptance criteria and test cases, and track test coverage for each requirement.

AI-generated content is always treated as a suggestion and must be reviewed by a user before approval.

The project is at an early scaffold stage: no product features exist yet.

## Run

```
docker compose up --build
```

Frontend: http://localhost:5173. Backend: http://localhost:8000 (`GET /health`). Postgres: `localhost:5432`.

## Documentation

- `docs/decisions.md`: accepted architecture and product decisions.
- `CLAUDE.md`: how AI-assisted development works here, and the verification commands.
- `docs/tasks/_template.md`: template for specifying a task.
- `apps/backend/README.md`, `apps/frontend/README.md`: per-app notes.
