# KDAI Docs Chatbot - Side Project Plan

## 目標
為 KDAI docs 網站建立 RAG chatbot，可嵌入網站作為 side project

## 時間
**4 週**

---

## 技術線

| 組件 | 選擇 | 理由 |
|------|------|------|
| Backend | FastAPI (Python) | 會 Python、AI 生態好 |
| Frontend | Vue.js widget | 與 KDAI 一致 |
| LLM | Ollama (llama3.2:3b / llama3.1:8b) | 與 KDAI 一致、本地運行 |
| Embedding | nomic-embed-text | Ollama 官方推薦 |
| Vector DB | Qdrant | AI 公司常用 |
| Search | RAG (手寫) | Semantic search、industry standard |
| Streaming | SSE | ChatGPT 風格逐字顯示 |
| 測試 | pytest + Vitest | API + Component 測試 |
| CI/CD | GitHub Actions | 自動化 |
| 部署 | Docker Compose | 與 KDAI 一致 |

---

## 模型配置

| 環境 | 模型 | VRAM |
|------|------|------|
| 筆電開發 | `llama3.2:3b` | ~2GB |
| 筆電正式 | `llama3.1:8b` | ~5GB |
| 學校 GPU | `mistral-nemo:12b` | ~8GB |

---

## 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                 Vue.js Chat Widget (SSE)                    │
│                      (內嵌 Docs)                            │
└────────────────────────────┬────────────────────────────────┘
                             │ SSE Stream
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI RAG Service                      │
│                                                             │
│  POST /api/index      ← 索引 docs (33 MDX)                  │
│  POST /api/chat       ← SSE streaming 回覆                  │
│  GET  /api/health     ← 健康檢查                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌─────────────┐   ┌───────────────┐   ┌──────────────┐
│   Ollama    │   │    Qdrant    │   │  .mdx files  │
│ LLM + Emb   │   │  (Vector DB) │   │  (33 files)  │
└─────────────┘   └───────────────┘   └──────────────┘
```

---

## RAG Pipeline（手寫）

```
Step 1: Index
  33 MDX → 解析 → 切 chunk (500 tokens) → nomic-embed-text → 存入 Qdrant

Step 2: Search
  問題 → 轉向量 → Qdrant cosine similarity → Top-3 chunks

Step 3: Generate
  問題 + chunks → prompt → Ollama → SSE streaming 回覆
```

---

## 4 週時程

### Week 1: 環境搭建 + RAG Pipeline

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1 | FastAPI scaffold、Docker Compose、Qdrant | 可啟動的專案 |
| 2 | Qdrant collection 設定、client 串接 | Qdrant 連接完成 |
| 3 | MDX parser、chunking 邏輯 | 切片程式完成 |
| 4-5 | Ollama embedding (`nomic-embed-text`) + 存入 Qdrant | Embedding pipeline |
| 6-7 | `/api/index` endpoint | CLI 可索引所有 docs |

**交付**: `python scripts/index_docs.py`

---

### Week 2: RAG API + Semantic Search

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1-2 | Semantic search（cosine similarity、top-k） | 搜尋完成 |
| 3-4 | `/api/chat` endpoint、prompt building、RAG 整合 | 基本 RAG API |
| 5-6 | Error handling、retry、fallback | Robust API |
| 7 | 測試 RAG quality | 品質驗證 |

**交付**: API 可接收問題、回傳 RAG 答案

---

### Week 3: SSE Streaming + Vue.js Widget

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1-2 | FastAPI SSE streaming 實作 | Streaming API |
| 3-4 | Vue.js widget 初始化、基本 UI | 聊天框外觀 |
| 5-6 | SSE client 串接、逐字顯示 | Streaming UI |
| 7 | Loading、error UI、樣式 | 完整 UI |

**交付**: 可嵌入的 chatbot widget

---

### Week 4: 測試 + CI/CD + 文檔

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1-2 | pytest：API tests | Backend 測試 |
| 3 | Vitest：Widget tests | 前端測試 |
| 4 | GitHub Actions CI workflow | 自動測試 |
| 5 | Docker Compose + CD pipeline | 自動部署 |
| 6-7 | README、架構圖、debug | 完整文檔 |

**交付**: Production-ready、可放履歷

---

## API Endpoints

| Method | Endpoint | 描述 |
|--------|----------|------|
| POST | `/api/index` | 索引所有 .mdx 文件 |
| POST | `/api/chat` | SSE streaming 回覆 |
| GET | `/api/health` | 健康檢查 |

---

## 專案結構

```
kadai-chatbot/
├── docker-compose.yml
├── Dockerfile
├── .github/
│   └── workflows/
│       └── ci.yml
├── rag_service/
│   ├── main.py
│   ├── routers/
│   │   └── chat.py
│   ├── services/
│   │   ├── embedder.py
│   │   ├── searcher.py
│   │   └── generator.py
│   ├── models/
│   │   └── schemas.py
│   └── scripts/
│       └── index_docs.py
├── chatbot_widget/
│   ├── src/
│   │   ├── ChatWidget.vue
│   │   └── ...
│   └── tests/
│       └── ChatWidget.test.ts
├── tests/
│   └── test_api.py
├── docs/
│   └── ARCHITECTURE.md
└── README.md
```

---

## 履歷寫法

```
KDAI Docs Chatbot (Side Project)
- RAG-based Q&A chatbot for internal documentation with SSE streaming
- FastAPI REST API + Vue.js embedded widget
- Ollama local LLM (llama3.1/llama3.2) + Qdrant vector database
- Semantic search using cosine similarity (nomic-embed-text)
- GitHub Actions CI/CD pipeline with Docker Compose deployment
```

---

## 面試可說的連結 KDAI 的點

1. 參考 KDAI 的 Docker Compose 微服務架構
2. Ollama 本地 LLM 與 KDAI 一致
3. 補足 KDAI 欠缺的 semantic search 功能
4. 使用與 KDAI ATTS 相同的 Python 微服務模式
