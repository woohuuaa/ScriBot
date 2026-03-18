# ScriBot

> RAG-based Q&A chatbot for KDAI documentation

## Overview

ScriBot is a side project that implements a full RAG (Retrieval-Augmented Generation) pipeline for the KDAI documentation website. It demonstrates end-to-end AI application development, from document indexing to streaming responses.

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
│      POST /api/index      ← Index docs (33 MDX files)       │
│      POST /api/chat       ← SSE streaming response          │
│      GET  /api/health     ← Health check                    │
└────────────────────────────┬────────────────────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
  ┌─────────────┐   ┌───────────────┐   ┌──────────────┐
  │   Ollama    │   │    Qdrant     │   │  .mdx files  │
  │ LLM + Emb   │   │  (Vector DB)  │   │ (33 files)   │
  └─────────────┘   └───────────────┘   └──────────────┘
```

## Tech Stack

| Component | Technology | Rationale |
|-----------|------------|------------|
| Backend | FastAPI (Python) | Async support, Pydantic validation, great AI ecosystem |
| LLM | Ollama (llama3.2:3b) | Local inference, zero API costs, consistent with KDAI |
| Embedding | nomic-embed-text | Ollama recommended, high quality embeddings |
| Vector DB | Qdrant | Industry standard, efficient similarity search |
| Frontend | Vue.js widget | Consistent with KDAI stack |
| Streaming | Server-Sent Events (SSE) | Real-time response, ChatGPT-style UX |
| Deployment | Docker Compose | Containerized, consistent with KDAI |

## RAG Pipeline

```
Step 1: Index
  MDX files → Parse → Chunk (500 tokens) → nomic-embed-text → Qdrant

Step 2: Search  
  Question → Embed → Cosine similarity → Top-3 chunks

Step 3: Generate
  Question + chunks → Prompt → Ollama → SSE streaming
```

## Key Features

- **Full RAG Implementation** — Hand-written pipeline, not using LangChain
- **Streaming Responses** — SSE for real-time, ChatGPT-style UX
- **Local LLM** — Zero API costs, privacy-friendly
- **Semantic Search** — Cosine similarity with Qdrant
- **Docker Deployment** — Consistent with KDAI architecture

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/index` | Index all .mdx files |
| POST | `/api/chat` | SSE streaming response |
| GET | `/api/health` | Health check |

## Project Structure

```
ScriBot/
├── docker-compose.yml      # Qdrant vector database
├── backend/                # FastAPI RAG service
│   ├── main.py
│   ├── routers/
│   ├── services/
│   │   ├── embedder.py     # Ollama embedding
│   │   ├── searcher.py     # Qdrant semantic search
│   │   └── generator.py   # LLM generation + SSE
│   └── scripts/
│       └── index_docs.py   # MDX parsing + indexing
└── chatbot_widget/         # Vue.js widget (in progress)
```

## Technical Decisions

1. **Why local LLM?** — Zero API costs, faster iteration, consistent with KDAI's Ollama usage
2. **Why hand-written RAG?** — Learning purpose, more control than LangChain
3. **Why SSE?** — Simpler than WebSocket, perfect for one-way streaming
4. **Why Qdrant?** — Industry standard for vector search, efficient filtering

## Connection to KDAI

- Uses same Ollama setup as KDAI
- Follows KDAI's Docker Compose microservices pattern
- Addresses KDAI's lack of semantic search functionality
- Python microservices architecture consistent with KDAI ATTS services

## Resume Description

```
KDAI Docs Chatbot (Side Project)
- RAG-based Q&A chatbot with SSE streaming
- FastAPI REST API + Vue.js embedded widget
- Ollama local LLM (llama3.2:3b) + Qdrant vector database
- Semantic search using cosine similarity (nomic-embed-text)
- Docker Compose deployment, GitHub Actions CI/CD
```

## License

MIT
