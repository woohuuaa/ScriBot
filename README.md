# ScriBot

> RAG-powered assistant for the KDAI documentation site.

ScriBot indexes the KDAI MDX docs in `Docs/`, serves chat and agent APIs from FastAPI, stores embeddings in Qdrant, and exposes a floating widget inside the Astro/Starlight frontend.

## What It Does

- answers KDAI documentation questions with retrieval-backed chat
- exposes an agent mode with structured steps and sources
- keeps public agent access read-only by default
- allows admin-only document mutation and hosted indexing with `x-admin-token`
- supports Ollama for local development, Groq for hosted use, and optional OpenAI backend configuration
- supports memory cache locally and Redis-backed cache for hosted deployments

## Repo Layout

```text
ScriBot/
├── backend/                    FastAPI API, RAG pipeline, agent, tests
├── Docs/                       KDAI documentation site and ScriBot widget
├── scribot-design-docs/        ScriBot-specific design notes and roadmaps
├── docker-compose.yml          Local Ollama + backend + Qdrant stack
├── Dockerfile.railway          Hosted backend image
├── railway.json                Railway deploy config
└── vercel.json                 Vercel config for Docs
```

## Main Endpoints

| Endpoint | Purpose |
|---|---|
| `POST /api/chat` | Streaming RAG chat |
| `POST /api/agent/run` | Agent run with structured steps and sources |
| `GET /api/providers` | Provider availability and model labels |
| `GET /api/health` | Health check |
| `POST /api/admin/index-docs` | Hosted indexing trigger, admin only |
| `GET /api/admin/index-docs/status` | Hosted indexing status, admin only |
| `GET /api/admin/cache/stats` | Cache stats, admin only |
| `POST /api/admin/cache/clear` | Cache clear, admin only |

Public `/api/agent/run` requests only get the read-only tools:

- `search_docs`
- `list_docs`
- `get_doc_info`

The write tools below require `x-admin-token`:

- `create_doc`
- `delete_doc`

## Local Development

Start the backend stack:

```bash
docker compose up -d
docker compose exec backend python -m scripts.index_docs
```

Start the docs frontend in another shell:

```bash
cd Docs
npm install
npm run dev
```

Local URLs:

- docs site: `http://localhost:4321`
- backend API: `http://localhost:8000`
- FastAPI docs: `http://localhost:8000/docs`

Notes:

- local compose mounts `Docs/` into the backend so the indexer reads the KDAI docs directly
- the frontend defaults to `http://localhost:8000` if `PUBLIC_SCRIBOT_API_BASE` is not set
- local cache is normally `memory`, not Redis

## Deployment

- frontend: deploy `Docs/` to Vercel
- backend: deploy `backend/` with `Dockerfile.railway` on Railway
- frontend hosted env example: `Docs/.env.railway.example`
- backend hosted env example: `backend/.env.railway.example`

Hosted profile expectations:

- use `Groq` as the default response provider
- use `FastEmbed` instead of Ollama for embeddings
- use `Redis` instead of memory cache
- set `ADMIN_TOKEN` if you need hosted indexing or admin endpoints

`Dockerfile.railway` copies both `backend/` and `Docs/` into the image so hosted indexing can still read the docs source.

## Validation

Backend tests:

```bash
cd backend
python -m unittest discover -s tests -v
```

Docs build:

```bash
cd Docs
npm run build
```

## Project Notes

- `Docs/` is the KDAI documentation project
- `scribot-design-docs/` is for ScriBot-specific planning and design records
- this repo is built to support the KDAI2 documentation experience

## License

MIT
