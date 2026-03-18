# ScriBot

AI Chatbot for KamerDebat AI Documentation

## About

ScriBot is a RAG-based (Retrieval-Augmented Generation) Q&A chatbot for the KDAI (KamerDebat AI) documentation website. It uses semantic search to find relevant documentation and generates accurate answers using local LLMs.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Vue.js Chat Widget (SSE)                    │
│                     (Embedded in Docs)                      │
└────────────────────────────┬────────────────────────────────┘
                             │ SSE Stream
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI RAG Service                      │
│                                                             │
│  POST /api/index      ← Index docs (33 MDX files)           │
│  POST /api/chat       ← SSE streaming response              │
│  GET  /api/health     ← Health check                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌─────────────┐   ┌───────────────┐   ┌──────────────┐
│   Ollama    │   │    Qdrant     │   │  .mdx files  │
│ LLM + Emb   │   │  (Vector DB)  │   │ (33 files)   │
└─────────────┘   └───────────────┘   └──────────────┘
```
## Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Backend | FastAPI (Python) | Know Python, great AI ecosystem |
| Frontend | Vue.js widget | Consistent with KDAI |
| LLM | Ollama (llama3.2:3b / llama3.1:8b) | Consistent with KDAI, runs locally |
| Embedding | nomic-embed-text | Ollama recommended |
| Vector DB | Qdrant | Industry standard for AI |
| Search | RAG (hand-written) | Semantic search, industry standard |
| Streaming | SSE | ChatGPT-style streaming |
| CI/CD | GitHub Actions | Automation |
| Deployment | Docker Compose | Consistent with KDAI |

## Model Configuration

| Environment | Model | VRAM |
|-------------|-------|------|
| Laptop Dev | `llama3.2:3b` | ~2GB |
| Laptop Prod | `llama3.1:8b` | ~5GB |
| School GPU | `mistral-nemo:12b` | ~8GB |

## Features

- Semantic search on documentation using cosine similarity
- ChatGPT-style streaming responses
- Embeddable chat widget
- Local LLM inference (no API costs)
- Full RAG pipeline implementation

## Project Structure

```
ScriBot/
├── docker-compose.yml      # Qdrant vector database
├── README.md
├── kadai-chatbot-plan.md   # Project plan (Chinese)
├── kadai-chatbot-plan-en.md # Project plan (English)
├── Docs/                   # Astro documentation site (deployed to Vercel)
├── backend/                # FastAPI RAG service (in progress)
│   ├── main.py
│   ├── routers/
│   ├── services/
│   └── scripts/
└── chatbot_widget/         # Vue.js widget (in progress)
```

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Ollama
- Python 3.10+

### 1. Start Qdrant

```bash
docker compose up -d
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Pull Ollama Models

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 4. Index Documentation

```bash
python scripts/index_docs.py
```

### 5. Run API

```bash
uvicorn main:app --reload --port 8000
```

### 6. Test

```bash
curl http://localhost:8000/api/health
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/index` | Index all .mdx files |
| POST | `/api/chat` | SSE streaming response |
| GET | `/api/health` | Health check |

## RAG Pipeline

```
Step 1: Index
  33 MDX → Parse → Chunk (500 tokens) → nomic-embed-text → Store in Qdrant

Step 2: Search
  Question → Embed → Qdrant cosine similarity → Top-3 chunks

Step 3: Generate
  Question + chunks → Prompt → Ollama → SSE streaming response
```

## Deployment

| Component | Platform |
|-----------|----------|
| Docs (Astro) | Vercel |
| Backend (FastAPI) | Docker Compose / Railway |
| Qdrant | Docker Compose |

## Resume Description

```
KDAI Docs Chatbot (Side Project)
- RAG-based Q&A chatbot for internal documentation with SSE streaming
- FastAPI REST API + Vue.js embedded widget
- Ollama local LLM (llama3.1/llama3.2) + Qdrant vector database
- Semantic search using cosine similarity (nomic-embed-text)
- GitHub Actions CI/CD pipeline with Docker Compose deployment
```

## Interview Talking Points

1. Referenced KDAI's Docker Compose microservices architecture
2. Ollama local LLM consistent with KDAI's implementation
3. Addresses KDAI's missing semantic search functionality
4. Uses same Python microservices pattern as KDAI ATTS services

## License

MIT License - 2026 Wan Hua (Momo) Wu
