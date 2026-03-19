# ScriBot - ML Inference Platform

## Goal

Build an ML Inference Platform with Production-ready features:
- RAG-based Q&A Chatbot for KDAI documentation
- Triple LLM Provider (Ollama / Groq / OpenAI) with automatic fallback
- Real-time model monitoring (Latency, Cost, Tokens)
- Citation Tracking (source attribution for AI responses)

---

## Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Backend | FastAPI (Python) | Know Python, great AI ecosystem |
| Frontend | Vue.js widget | Consistent with KDAI |
| LLM | Ollama + Groq + OpenAI | Triple redundancy, cost control |
| Embedding | nomic-embed-text | Ollama recommended |
| Vector DB | Qdrant Cloud | Managed service, free 1GB |
| Search | RAG (hand-written) | Semantic search, industry standard |
| Streaming | SSE | ChatGPT-style streaming |
| Monitoring | Custom (Latency/Cost/Tokens) | Real-time model performance |
| Citation | Custom (Source tracking) | RAG explainability |
| CI/CD | GitHub Actions | Automation |
| Deployment | Railway + Docker | Serverless container |

---

## Model Configuration

| Environment | Model | VRAM / Cost |
|-------------|-------|-------------|
| Laptop Dev | `llama3.2:3b` (Ollama) | ~2GB / $0 |
| Laptop Prod | `llama3.1:8b` (Ollama) | ~5GB / $0 |
| Cloud Backup | `llama-3.3-70b-specdec` (Groq) | - / Free tier |
| Final Backup | `gpt-4o-mini` (OpenAI) | - / $5 credit |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Vue.js Chat Widget                         │
│                     (Embedded in Docs)                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │ SSE Stream
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Railway)                    │
│                                                                  │
│  POST /api/index      ← Index docs (33 MDX files)                │
│  POST /api/chat       ← SSE streaming response                    │
│  GET  /api/health     ← Health check                             │
│  GET  /api/stats      ← Monitoring stats                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Monitoring Layer ⭐                                       │    │
│  │  ├── Latency: 1.2s                                        │    │
│  │  ├── Cost: $0.00 (Ollama)                                 │    │
│  │  ├── Tokens: 2048                                         │    │
│  │  └── Fallback count: 0                                    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Citation Layer ⭐                                        │    │
│  │  ├── [1] Installation/prerequisites.mdx (92%)            │    │
│  │  └── [2] Architecture.mdx (78%)                           │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     Ollama      │   │      Groq       │   │     OpenAI     │
│   (Primary)     │   │    (Backup)     │   │    (Backup)    │
│   llama3.1:8b   │   │ llama-3.3-70b  │   │   gpt-4o-mini  │
│   Your 4060    │   │     Free        │   │   $5 credit    │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │
         │ ngrok tunnel
         │ (Expose local resources to cloud)
         ▼
┌─────────────────┐
│    Qdrant       │
│     Cloud       │
└─────────────────┘
```

---

## RAG Pipeline

```
Step 1: Index
  33 MDX → Parse → Chunk (500 tokens) → nomic-embed-text → Store in Qdrant

Step 2: Search
  Question → Embed → Qdrant cosine similarity → Top-3 chunks + scores

Step 3: Generate + Monitor
  Question + chunks → Prompt → LLM → SSE streaming
                  │
                  ├── ⏱ Latency tracking
                  ├── 💰 Cost tracking
                  ├── 📊 Token counting
                  └── 🔗 Citation generation
```

---

## Fallback Logic

```
Request →
  Try Ollama (local) →
    Failed → Try Groq (cloud free) →
      Failed → Try OpenAI (paid backup) →
        All failed → Return error message
```

---

## Enhancement Features (Differentiation)

### 1. Model Monitoring

| Metric | Description | Interview Topic |
|--------|-------------|-----------------|
| Latency | Time per step (embedding/search/generation) | How to optimize model latency? |
| Cost | Estimated cost per request | How to control LLM costs? |
| Tokens | Input/output token count | How is token billing calculated? |
| Fallback count | Number of auto-switches | How to design fault tolerance? |

### 2. Citation Tracking

| Feature | Description | Interview Topic |
|---------|-------------|-----------------|
| Source linking | Attribution in answers | Why should RAG cite sources? |
| Similarity score | Display match percentage (92%, 78%) | How to ensure answer accuracy? |
| Document title | Show file names | How to implement Explainable AI? |

---

## 4-Week Timeline

### Week 1: Environment Setup + RAG Pipeline

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Ollama setup (`llama3.1:8b` + `nomic-embed-text`) | Local working |
| 2 | ngrok setup (expose Ollama to cloud) | Public URL |
| 3 | Railway deployment of FastAPI | Initial deployment |
| 4 | Qdrant Cloud setup | Vector DB ready |
| 5-6 | RAG Pipeline: Embedding + Search + Generate | Complete flow |
| 7 | **Live Demo** | Shareable URL |

**Deliverable**: `python scripts/index_docs.py`

---

### Week 2: Triple LLM Provider + Fault Tolerance

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Groq API integration | Dual Provider |
| 3-4 | OpenAI API integration | Triple Provider |
| 5-6 | Fallback logic implementation | Ollama → Groq → OpenAI |
| 7 | Fault tolerance testing | Stable version |

**Deliverable**: Three-layer LLM auto-switching

---

### Week 3: Enhancement Features + Frontend Widget

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Monitoring Layer (Latency/Cost/Tokens) | Model monitoring ⭐ |
| 3-4 | Citation Layer (Source/Citation tracking) | Citation tracking ⭐ |
| 5-6 | Vue.js widget init + SSE integration | Chat UI |
| 7 | Integrate monitoring + citation into widget | Complete frontend |

**Deliverable**: Chatbot widget with monitoring and citation

---

### Week 4: Testing + CI/CD + Documentation

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | pytest: API tests + Monitoring tests | Backend tests |
| 3 | Vitest: Widget tests | Frontend tests |
| 4 | GitHub Actions CI workflow | Auto testing |
| 5-6 | Railway CD pipeline | Auto deployment |
| 7 | README, architecture diagram, interview prep | Complete |

**Deliverable**: Production-ready, resume-worthy

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/index` | Index all .mdx files |
| POST | `/api/chat` | SSE streaming response (with citation) |
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Monitoring statistics |

---

## API Response Format

### /api/chat Response

```json
{
  "answer": "KDAI requires Docker and PostgreSQL.",
  "citations": [
    {"id": 1, "source": "Installation/prerequisites.mdx", "score": 0.92},
    {"id": 2, "source": "Architecture.mdx", "score": 0.78}
  ],
  "stats": {
    "provider": "ollama",
    "latency_ms": 1200,
    "tokens_used": 2048,
    "estimated_cost": 0.0
  }
}
```

---

## Project Structure

```
ScriBot/
├── docker-compose.yml         # Qdrant (local backup)
├── Dockerfile
├── requirements.txt
├── backend/
│   ├── main.py                # FastAPI entry
│   ├── config.py              # Configuration management
│   ├── routers/
│   │   └── chat.py            # /api/chat endpoint
│   ├── services/
│   │   ├── llm_providers/     # LLM Provider abstraction
│   │   │   ├── base.py
│   │   │   ├── ollama.py
│   │   │   ├── groq.py
│   │   │   └── openai.py
│   │   ├── embedder.py        # Embedding service
│   │   ├── searcher.py        # Qdrant search
│   │   ├── generator.py       # LLM generation
│   │   ├── monitor.py         # Monitoring service ⭐ NEW
│   │   └── citation.py        # Citation tracking ⭐ NEW
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   └── scripts/
│       └── index_docs.py      # MDX indexing
├── chatbot_widget/             # Vue.js widget
│   ├── ChatWidget.vue
│   └── ...
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Resume Description

```
ScriBot - ML Inference Platform (Side Project)
- RAG-based Q&A chatbot with real-time model monitoring (latency, cost, tokens)
- Source citation tracking for AI-generated responses
- Triple LLM provider architecture (Ollama/Groq/OpenAI) with automatic fallback
- FastAPI REST API + Vue.js embedded widget + SSE streaming
- Railway deployment with Docker containerization
```

---

## Interview Talking Points

1. **Triple LLM Provider + Fallback**
   → "How to design a fault-tolerant ML inference system?"
   → "How to control LLM costs?"

2. **Model Monitoring**
   → "How to ensure models are working after deployment?"
   → "How to track LLM latency and costs?"

3. **Citation Tracking**
   → "Why should RAG cite sources?"
   → "How to implement Explainable AI?"

4. **ngrok Local-to-Cloud**
   → "How to expose local resources to the cloud?"
   → "What are the security considerations?"

5. **Connection to KDAI**
   → Referenced KDAI's Docker Compose microservices architecture
   → Ollama local LLM consistent with KDAI's implementation
   → Addresses KDAI's missing semantic search functionality
   → Uses same Python microservices pattern as KDAI ATTS services
