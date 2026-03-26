# ScriBot - AI-Powered Documentation Chatbot

## Goal

Build an AI chatbot aligned with course technologies, targeting Autodesk Internship:

- RAG-based Q&A Chatbot for KDAI documentation
- A/B Testing Framework (user can select different LLM providers)
- Statistical Analysis (Latency, Cost, User Feedback)
- Personalization (storing query history)
- Using technologies taught in course (Docker, EC2, GitHub Actions, DynamoDB)

---

## Tech Stack (Aligned with Course)

| Component | Choice | Course Content |
|-----------|--------|----------------|
| Backend | FastAPI (Python) | Week 1: Microservices |
| Frontend | Vue.js widget | Frontend development |
| LLM | Ollama + Groq + OpenAI | Triple redundancy |
| Embedding | nomic-embed-text | Ollama recommended |
| Vector DB | Qdrant | AI vector database |
| Container | Docker | Week 5-7: Docker |
| Container Orchestration | docker compose | Week 10: docker compose |
| CI/CD | GitHub Actions | Week 3, 8: GitHub Actions |
| Deployment | AWS EC2 | Week 4: EC2 |
| Database | DynamoDB | Week 12: DynamoDB |
| Storage | Local | Week 11: S3 (optional) |
| IaC | - | Week 13: CloudFormation (optional) |

---

## Technology Selection Rationale

### Why Qdrant for Vector Database?

| Feature | Qdrant | Pinecone | Chroma | Milvus |
|---------|--------|----------|--------|--------|
| Open Source | ✅ Fully open | ❌ Closed SaaS | ✅ Open | ✅ Open |
| Self-hosted | ✅ One-line Docker | ❌ Cloud only | ✅ Lightweight | ✅ But heavy |
| Free | ✅ Completely free | ❌ Paid | ✅ Free | ✅ Free |
| Performance | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**Reasons:**
1. **One-line Docker setup** - Aligns with course Docker deployment
2. **Free + Open source** - Data stays on your machine, no account needed
3. **Great Python SDK** - `qdrant-client` is clean and intuitive
4. **Complete REST API** - Easy to debug and test
5. **Industry adoption** - Used by Notion, Podimo, etc.

### Why Ollama as Primary LLM?

| Feature | Ollama (Local) | Groq (Cloud) | OpenAI (Cloud) |
|---------|---------------|--------------|----------------|
| Cost | $0 | Free tier | Paid |
| Latency | Higher | Very low | Low |
| Privacy | ✅ Data stays local | ❌ Sent to cloud | ❌ Sent to cloud |
| Offline | ✅ Works offline | ❌ Needs internet | ❌ Needs internet |
| Reliability | Depends on hardware | High | High |

**Reasons:**
1. **Zero cost** - Runs locally, completely free
2. **Consistent with KDAI** - KDAI also uses Ollama
3. **Privacy-friendly** - Data never leaves your machine
4. **Learning value** - Understand local LLM deployment

**Fallback strategy:** Ollama (fail) → Groq (fail) → OpenAI

### Why FastAPI?

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Async Support | ✅ Native | ❌ Needs extension | ❌ Needs extension |
| Type Validation | ✅ Pydantic | ❌ Needs extension | ❌ Needs extension |
| Auto Docs | ✅ Swagger UI | ❌ Needs extension | ❌ Needs extension |
| Learning Curve | Low | Low | High |

**Reasons:**
1. **Native Async** - Perfect for LLM streaming and SSE
2. **Pydantic validation** - Automatic type checking
3. **Auto API docs** - `/docs` generates Swagger UI automatically
4. **AI ecosystem** - Most AI projects use FastAPI

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
│                      FastAPI Backend (AWS EC2)                    │
│                         (Docker Container)                        │
│                                                                  │
│  POST /api/index      ← Index docs (33 MDX files)              │
│  POST /api/chat       ← SSE streaming response                  │
│  GET  /api/health     ← Health check                            │
│  GET  /api/stats      ← Monitoring stats                        │
│  POST /api/feedback   ← User feedback                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Monitoring Layer ⭐                                      │    │
│  │  ├── Latency: 1.2s                                       │    │
│  │  ├── Cost: $0.00 (Ollama)                               │    │
│  │  ├── Tokens: 2048                                        │    │
│  │  └── Fallback count: 0                                    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  A/B Testing Layer ⭐                                     │    │
│  │  ├── User selected: Ollama                               │    │
│  │  ├── Provider usage stats: {ollama: 60%, groq: 30%}     │    │
│  │  └── User feedback: 👍 85%                               │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     Ollama      │   │      Groq       │   │     OpenAI     │
│   (Primary)     │   │    (Backup)     │   │    (Backup)    │
│   llama3.1:8b   │   │ llama-3.3-70b  │   │   gpt-4o-mini  │
│   Your 4060     │   │     Free        │   │   $5 credit    │
└─────────────────┘   └─────────────────┘   └─────────────────┘
                               │
┌─────────────────┐   ┌─────────────────┐
│     Qdrant      │   │    DynamoDB     │
│   (Vector DB)   │   │  (User History) │
└─────────────────┘   └─────────────────┘
```

---

## RAG Pipeline

```
Step 1: Index
  33 MDX → Parse → Chunk (500 tokens) → nomic-embed-text → Store in Qdrant

Step 2: Search
  Question → Embed → Qdrant cosine similarity → Top-3 chunks + scores

Step 3: Generate
  Question + chunks → Prompt → LLM → SSE streaming
                  │
                  ├── ⏱ Latency tracking
                  ├── 💰 Cost tracking
                  └── 📊 Token counting
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

## A/B Testing Framework ⭐

| Feature | Description | Interview Topic |
|---------|-------------|-----------------|
| Provider Selection | User can select which LLM to use | Understanding A/B Testing concepts |
| Usage Statistics | Record usage count for each Provider | Data collection and analysis |
| User Feedback | Collect 👍/👎 feedback | Statistical Analysis |

### User Flow

```
1. User opens chat
2. See Provider options (Ollama / Groq / OpenAI)
3. Select one and send question
4. After answer, give 👍 or 👎
5. System records: selection + feedback + Latency + Cost
```

---

## Statistical Analysis ⭐

| Metric | Description | Interview Topic |
|--------|-------------|-----------------|
| Latency | Time per step | How to optimize model latency? |
| Cost | Estimated cost per request | How to control LLM costs? |
| Tokens | Input/output token count | How is token billing calculated? |
| User Feedback | 👍/👎 feedback ratio | How to measure user satisfaction? |
| Provider Distribution | Usage count per Provider | A/B Testing result analysis |

---

## Personalization ⭐

| Feature | Description | Interview Topic |
|---------|-------------|-----------------|
| Query History | Store query history in DynamoDB | NoSQL database application |
| History Display | Show past queries | User experience optimization |

---

## 4-Week Timeline

### Week 1: Core Architecture + Docker + docker compose

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Project structure + Dockerfile | Dockerized |
| 2 | docker-compose.yml | Multi-container management |
| 3 | FastAPI basic structure | Microservices |
| 4 | Three LLM Provider integration | Ollama / Groq / OpenAI |
| 5-7 | Local Docker test successful | Working containers |

**Deliverable**: `docker compose up` can start services

---

### Week 2: RAG Pipeline + DynamoDB

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | Qdrant integration + Embedding | Vector DB ready |
| 3-4 | DynamoDB setup + Store user history | Personalization |
| 5-6 | Monitoring Layer (Latency/Cost) | Statistical Analysis |
| 7 | RAG Pipeline complete | Working Q&A Chatbot |

**Deliverable**: RAG Pipeline working

---

### Week 3: CI/CD + A/B Testing

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | GitHub Actions CI workflow | Automated testing |
| 3-4 | A/B Testing Framework | User can select Provider |
| 5-6 | User Feedback collection | Statistical Analysis |
| 7 | Basic Widget | Embeddable chat box |

**Deliverable**: GitHub Actions CI pipeline + A/B Testing

---

### Week 4: AWS EC2 Deployment + CD Pipeline

| Day | Task | Deliverable |
|-----|------|-------------|
| 1-2 | AWS EC2 setup + deployment | Live Demo |
| 3-4 | CD Pipeline (GitHub Actions) | Automated deployment |
| 5-6 | Personalization + polish | Feature complete |
| 7 | README + Interview prep | Resume-ready |

**Deliverable**: Production-ready, Live Demo URL

---

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

### /api/stats Response

```json
{
  "total_requests": 150,
  "provider_usage": {
    "ollama": 90,
    "groq": 45,
    "openai": 15
  },
  "avg_latency_ms": 1500,
  "total_cost": 0.05,
  "feedback_positive_rate": 0.85
}
```

---

## Project Structure

```
ScriBot/
├── docker-compose.yml         # Multi-container management
├── Dockerfile                  # Backend containerization
├── requirements.txt
├── backend/
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
│   │   ├── generator.py        # LLM generation
│   │   ├── monitor.py          # Monitoring service
│   │   └── dynamodb.py         # DynamoDB operations
│   ├── models/
│   │   └── schemas.py
│   └── scripts/
│       └── index_docs.py
├── chatbot_widget/             # Vue.js widget
│   └── ...
├── .github/
│   └── workflows/
│       ├── ci.yml             # CI pipeline
│       └── cd.yml             # CD pipeline
└── README.md
```

---

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

---

## Interview Talking Points

1. **A/B Testing Framework**
   → "I implemented an A/B Testing Framework where users can select different LLM providers and I record their choices"
   → "This aligns with Autodesk JD requirement for A/B Testing experience"

2. **Statistical Analysis**
   → "I track Latency, Cost, and User Feedback, and analyze performance across different providers"
   → "I understand how to collect and analyze data to optimize the system"

3. **DynamoDB (NoSQL)**
   → "I use DynamoDB to store user query history"
   → "Week 12 in my course teaches DynamoDB, this is my practical application"

4. **Docker + docker compose**
   → "I use Docker to containerize the Backend and docker compose to manage multiple containers"
   → "Week 5-7 in my course teaches Docker, this is my early implementation"

5. **GitHub Actions CI/CD**
   → "I use GitHub Actions for automated testing and deployment"
   → "Week 3, 8 in my course teaches GitHub Actions"

6. **AWS EC2 Deployment**
   → "I deploy to AWS EC2 and learn cloud deployment workflow"
   → "Week 4 in my course teaches EC2"

7. **Connection to KDAI**
   → Referenced KDAI's Docker Compose microservices architecture
   → Ollama local LLM consistent with KDAI's implementation
   → Addresses KDAI's missing semantic search functionality
