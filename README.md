# ScriBot

> AI-Powered RAG Chatbot for KDAI Documentation

## Overview

ScriBot is a side project that implements a full RAG (Retrieval-Augmented Generation) pipeline for the KDAI documentation website. It demonstrates end-to-end AI application development with A/B testing, statistical analysis, and personalization features.

**Target:** Autodesk Internship application - aligned with course technologies (Docker, AWS EC2, GitHub Actions, DynamoDB).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Vue.js Chat Widget                         │
│                     (Embedded in Docs)                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │ SSE Stream
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (AWS EC2)                    │
│                       (Docker Container)                        │
│                                                                 │
│  POST /api/index          ← Index docs (33 MDX files)           │
│  POST /api/chat           ← SSE streaming response              │
│  GET  /api/health         ← Health check                        │
│  GET  /api/stats          ← Monitoring statistics               │
│  POST /api/feedback       ← User feedback                       │
│  GET  /api/history        ← Query history                       │
│  POST /api/select-provider← Select LLM Provider                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Monitoring Layer                                         │  │
│  │  ├── Latency tracking                                     │  │
│  │  ├── Cost estimation                                      │  │
│  │  ├── Token counting                                       │  │
│  │  └── Fallback count                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  A/B Testing Layer                                        │  │
│  │  ├── User provider selection                              │  │
│  │  ├── Provider usage stats                                 │  │
│  │  └── User feedback collection                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     Ollama      │   │      Groq       │   │     OpenAI      │
│   (Primary)     │   │    (Backup)     │   │    (Backup)     │
│   llama3.1:8b   │   │ llama-3.3-70b   │   │   gpt-4o-mini   │
│   Local/$0      │   │    Free tier    │   │   $5 credit     │
└─────────────────┘   └─────────────────┘   └─────────────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
┌─────────────────┐                         ┌─────────────────┐
│     Qdrant      │                         │    DynamoDB     │
│   (Vector DB)   │                         │  (User History) │
└─────────────────┘                         └─────────────────┘
```

## Tech Stack (Aligned with Course)

| Component | Technology | Course Week |
|-----------|------------|-------------|
| Backend | FastAPI (Python) | Week 1: Microservices |
| Frontend | Vue.js widget | Frontend development |
| LLM | Ollama + Groq + OpenAI | Triple redundancy |
| Embedding | nomic-embed-text | Ollama recommended |
| Vector DB | Qdrant | AI vector database |
| Container | Docker | Week 5-7: Docker |
| Orchestration | Docker Compose | Week 10: Docker Compose |
| CI/CD | GitHub Actions | Week 3, 8: GitHub Actions |
| Deployment | AWS EC2 | Week 4: EC2 |
| Database | DynamoDB | Week 12: DynamoDB |

## Key Features

- **Full RAG Implementation** - Hand-written pipeline (no LangChain)
- **Triple LLM Fallback** - Ollama → Groq → OpenAI for reliability
- **A/B Testing Framework** - User can select and compare LLM providers
- **Statistical Analysis** - Track latency, cost, tokens, and user feedback
- **Personalization** - Query history stored in DynamoDB
- **Streaming Responses** - SSE for real-time, ChatGPT-style UX
- **Local LLM** - Zero API costs with Ollama as primary

## RAG Pipeline

```
Step 1: Index
  33 MDX → Parse → Chunk (500 tokens) → nomic-embed-text → Qdrant

Step 2: Search
  Question → Embed → Cosine similarity → Top-3 chunks + scores

Step 3: Generate
  Question + chunks → Prompt → LLM → SSE streaming
                  │
                  ├── Latency tracking
                  ├── Cost tracking
                  └── Token counting
```

## Fallback Logic

```
Request →
  Try Ollama (local) →
    Failed → Try Groq (cloud free) →
      Failed → Try OpenAI (paid backup) →
        All failed → Return error message
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/index` | Index all .mdx files |
| POST | `/api/chat` | SSE streaming response |
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Monitoring statistics |
| POST | `/api/feedback` | Submit user feedback |
| GET | `/api/history` | Get query history |
| POST | `/api/select-provider` | Select LLM Provider |

## Project Structure

```
ScriBot/
├── docker-compose.yml         # Multi-container management
├── backend/
│   ├── Dockerfile             # Backend containerization
│   ├── main.py                # FastAPI entry
│   ├── config.py              # Configuration management
│   ├── routers/
│   │   └── chat.py            # API endpoints
│   ├── services/
│   │   ├── llm_providers/     # LLM Provider abstraction
│   │   │   ├── base.py
│   │   │   ├── ollama.py
│   │   │   ├── groq.py
│   │   │   └── openai.py
│   │   ├── embedder.py        # Embedding service
│   │   ├── searcher.py        # Qdrant search
│   │   ├── generator.py       # LLM generation
│   │   ├── monitor.py         # Monitoring service
│   │   └── dynamodb.py        # DynamoDB operations
│   ├── models/
│   │   └── schemas.py
│   └── scripts/
│       └── index_docs.py
├── chatbot_widget/            # Vue.js widget
├── Docs/                      # KDAI documentation (33 MDX files)
├── .github/
│   └── workflows/
│       ├── ci.yml             # CI pipeline
│       └── cd.yml             # CD pipeline
└── README.md
```

## Progress

### Week 1: Core Architecture + Docker (Completed)
- [x] Project structure + Dockerfile
- [x] docker-compose.yml (Ollama + Backend + Qdrant)
- [x] FastAPI basic architecture
- [x] Three LLM Provider integration (Ollama/Groq/OpenAI)
- [x] Basic `/api/chat` and `/api/health` endpoints
- [x] `docker compose up` successfully runs all services
- [ ] System prompt configuration (in progress)

### Week 2: RAG Pipeline + DynamoDB (Not Started)
- [ ] Qdrant integration + Embedding
- [ ] DynamoDB setup + user history
- [ ] Monitoring Layer (Latency/Cost)
- [ ] RAG Pipeline complete

### Week 3: CI/CD + A/B Testing (Not Started)
- [ ] GitHub Actions CI workflow
- [ ] A/B Testing Framework
- [ ] User Feedback collection
- [ ] Basic Widget

### Week 4: AWS EC2 Deployment (Not Started)
- [ ] AWS EC2 setup + deployment
- [ ] CD Pipeline (GitHub Actions)
- [ ] Personalization + polish

## Quick Start

```bash
# Start all services
docker compose up -d

# Check health
curl http://localhost:8000/api/health

# Chat (SSE streaming)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is KDAI?"}'
```

## Connection to KDAI

- Uses same Ollama setup as KDAI
- Follows KDAI's Docker Compose microservices pattern
- Addresses KDAI's lack of semantic search functionality
- Python microservices architecture consistent with KDAI ATTS services

## Resume Description

```
ScriBot - AI-Powered Documentation Chatbot (Side Project)

- RAG-based Q&A chatbot deployed on AWS EC2 with Docker containerization
- A/B testing framework for LLM provider comparison (Ollama/Groq/OpenAI)
- Statistical analysis: tracking latency, cost, and user feedback metrics
- Personalization: storing user query history in DynamoDB
- Full stack: FastAPI backend + Vue.js widget + Qdrant vector database
- CI/CD with GitHub Actions (automated testing and deployment)

Technologies: Python, FastAPI, Docker, AWS EC2, DynamoDB, GitHub Actions, Vue.js
```

## License

MIT
