---
name: start-servers
description: >-
  Start ATLAS local development servers (Docker Compose backend stack + Vite
  frontend). Use when the user asks to fire up, start, or run the servers, dev
  environment, or local stack.
---

# Start ATLAS Dev Servers

## Prerequisites (first time only)

From repo root (`/Users/johnbelam/Dev/atlas`):

```bash
# Root env for API/worker (copy if missing)
cp .env.example .env
# Generate FERNET_KEY if still CHANGE_ME:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Frontend env
cp frontend/.env.example frontend/.env
cd frontend && npm install
```

Run migrations when schema changes:

```bash
cd backend && alembic upgrade head
```

## Start everything

**Terminal 1 — Infrastructure** (from repo root):

```bash
cd /Users/johnbelam/Dev/atlas
docker compose up -d postgres redis minio flower worker
```

**Terminal 2 — API** (local uvicorn with live code; preferred during dev):

```bash
cd /Users/johnbelam/Dev/atlas/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Do **not** `source ../.env` in the shell — pydantic reads `.env` from repo root and shell-export breaks `CORS_ORIGINS` JSON.

Verify:

```bash
curl -s http://127.0.0.1:8000/api/v1/health | jq '.data.status'   # expect "ok"
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/v1/datasets   # expect 200
```

**Alternative — Docker API** (only after rebuild when code changes):

```bash
docker compose build api worker && docker compose up -d api worker
```

**Terminal 3 — Frontend** (background or separate terminal):

```bash
cd /Users/johnbelam/Dev/atlas/frontend
npm run dev
```

## URLs

| Service | URL |
|---------|-----|
| Frontend (Vite) | http://localhost:5173 |
| API | http://127.0.0.1:8000/api/v1 |
| Health | http://127.0.0.1:8000/api/v1/health |
| Flower (Celery) | http://127.0.0.1:5555 |
| MinIO console | http://127.0.0.1:9001 |

## Stop

```bash
# Frontend: Ctrl+C in the Vite terminal

# Docker (from repo root)
docker compose down          # stop containers, keep volumes
docker compose down -v       # also remove postgres/minio data
```

## Troubleshooting

- **404 on `/datasets` (or other new routes) while `/sources` works**: Docker API image is stale. Stop it (`docker compose stop api`) and run local uvicorn, or `docker compose build api worker && docker compose up -d api worker`.
- **Worker exited** (`Exited (137)`): `docker compose up -d worker` restarts it.
- **API unhealthy**: check `docker compose logs api --tail 50`.
- **Port in use**: `lsof -i :8000` or `lsof -i :5173`.
- **Frontend can't reach API**: confirm `frontend/.env` has `VITE_API_URL=http://127.0.0.1:8000/api/v1`.
