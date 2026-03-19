# ScriBot - ML Inference Platform

## 目標

建立一個具有 Production 要素的 ML Inference Platform，包含：
- RAG-based Q&A Chatbot for KDAI documentation
- Triple LLM Provider (Ollama / Groq / OpenAI) 自動切換
- 即時模型監控（Latency、Cost、Tokens）
- Citation Tracking（答案標註來源）

---

## 技術棧

| 組件 | 選擇 | 理由 |
|------|------|------|
| Backend | FastAPI (Python) | 會 Python、AI 生態好 |
| Frontend | Vue.js widget | 與 KDAI 一致 |
| LLM | Ollama + Groq + OpenAI | 三層容錯、成本控制 |
| Embedding | nomic-embed-text | Ollama 官方推薦 |
| Vector DB | Qdrant Cloud | Managed service、免費 1GB |
| Search | RAG (手寫) | Semantic search、industry standard |
| Streaming | SSE | ChatGPT 風格逐字顯示 |
| Monitoring | Custom (Latency/Cost/Tokens) | 即時監控模型效能 |
| Citation | Custom (Source tracking) | RAG 可解釋性 |
| CI/CD | GitHub Actions | 自動化 |
| 部署 | Railway + Docker | Serverless container |

---

## 模型配置

| 環境 | 模型 | VRAM / 成本 |
|------|------|--------------|
| 筆電開發 | `llama3.2:3b` (Ollama) | ~2GB / $0 |
| 筆電正式 | `llama3.1:8b` (Ollama) | ~5GB / $0 |
| 雲端備用 | `llama-3.3-70b-specdec` (Groq) | - / 免費額度 |
| 最終備用 | `gpt-4o-mini` (OpenAI) | - / $5 credit |

---

## 架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                      Vue.js Chat Widget                         │
│                     (Embedded in Docs)                           │
└──────────────────────────────┬──────────────────────────────────┘
                               │ SSE Stream
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Railway)                    │
│                                                                  │
│  POST /api/index      ← 索引 docs (33 MDX)                       │
│  POST /api/chat       ← SSE streaming 回覆                       │
│  GET  /api/health     ← 健康檢查                                 │
│  GET  /api/stats      ← 監控統計                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Monitoring Layer ⭐                                      │    │
│  │  ├── Latency: 1.2s                                       │    │
│  │  ├── Cost: $0.00 (Ollama)                                │    │
│  │  ├── Tokens: 2048                                        │    │
│  │  └── Fallback count: 0                                   │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Citation Layer ⭐                                       │    │
│  │  ├── [1] Installation/prerequisites.mdx (92%)           │    │
│  │  └── [2] Architecture.mdx (78%)                         │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     Ollama      │   │      Groq       │   │     OpenAI     │
│   (Primary)     │   │    (Backup)     │   │    (Backup)    │
│   llama3.1:8b   │   │ llama-3.3-70b   │   │   gpt-4o-mini  │
│   你的 4060     │   │     免費        │   │   $5 credit    │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │
         │ ngrok tunnel
         │ (暴露本地資源給雲端)
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
  33 MDX → 解析 → 切 chunk (500 tokens) → nomic-embed-text → 存入 Qdrant

Step 2: Search
  問題 → 轉向量 → Qdrant cosine similarity → Top-3 chunks + 分數

Step 3: Generate + Monitor
  問題 + chunks → Prompt → LLM → SSE streaming
                  │
                  ├── ⏱ Latency tracking
                  ├── 💰 Cost tracking
                  ├── 📊 Token counting
                  └── 🔗 Citation generation
```

---

## Fallback 邏輯

```
Request →
  嘗試 Ollama (本機) →
    失敗 → 嘗試 Groq (雲端免費) →
      失敗 → 嘗試 OpenAI (付費備用) →
        全部失敗 → 回傳錯誤訊息
```

---

## 強化功能（差異化）

### 1. 模型監控 (Monitoring)

| 指標 | 說明 | 面試話題 |
|------|------|----------|
| Latency | 每個步驟耗時（embedding/search/generation） | 如何優化模型延遲？ |
| Cost | 每次請求估計成本 | 如何控制 LLM 成本？ |
| Tokens | 輸入/輸出 token 數 | Token 怎麼計費？ |
| Fallback count | 自動切換次數 | 如何設計容錯機制？ |

### 2. Citation Tracking

| 功能 | 說明 | 面試話題 |
|------|------|----------|
| Source linking | 標註答案來源 | 為什麼 RAG 要標註來源？ |
| Similarity score | 顯示相似度（92%、78%）| 如何確保答案正確性？ |
| Document title | 顯示文件名稱 | 如何實現可解釋 AI？ |

---

## 4 週時程

### Week 1: 環境建置 + RAG Pipeline

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1 | Ollama 設定 (`llama3.1:8b` + `nomic-embed-text`) | 本機可運行 |
| 2 | ngrok 設定（暴露 Ollama 給雲端）| 公開 URL |
| 3 | Railway 部署 FastAPI | 初步上線 |
| 4 | Qdrant Cloud 串接 | 向量資料庫就緒 |
| 5-6 | RAG Pipeline: Embedding + Search + Generate | 完整流程 |
| 7 | **Live Demo 完成** | 可分享 URL |

**交付**: `python scripts/index_docs.py`

---

### Week 2: Triple LLM Provider + 容錯機制

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1-2 | Groq API 串接 | 雙 Provider |
| 3-4 | OpenAI API 串接 | 三重 Provider |
| 5-6 | Fallback 邏輯實作 | Ollama → Groq → OpenAI |
| 7 | 測試容錯機制 | 穩定版本 |

**交付**: 三層 LLM 自動切換

---

### Week 3: 強化功能 + Frontend Widget

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1-2 | Monitoring Layer (Latency/Cost/Tokens) | 模型監控 ⭐ |
| 3-4 | Citation Layer (Source/Citation tracking) | 引用追蹤 ⭐ |
| 5-6 | Vue.js widget 初始化 + SSE 串接 | 聊天 UI |
| 7 | 整合監控 + Citation 到 widget | 完整前端 |

**交付**: 包含監控和引用的 chatbot widget

---

### Week 4: 測試 + CI/CD + 文檔

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1-2 | pytest: API tests + Monitoring tests | Backend 測試 |
| 3 | Vitest: Widget tests | 前端測試 |
| 4 | GitHub Actions CI workflow | 自動測試 |
| 5-6 | Railway CD pipeline | 自動部署 |
| 7 | README、架構圖、面試準備 | 完成 |

**交付**: Production-ready、可放履歷

---

## API Endpoints

| Method | Endpoint | 描述 |
|--------|----------|------|
| POST | `/api/index` | 索引所有 .mdx 文件 |
| POST | `/api/chat` | SSE streaming 回覆（含 citation）|
| GET | `/api/health` | 健康檢查 |
| GET | `/api/stats` | 監控統計 |

---

## API Response 格式

### /api/chat Response

```json
{
  "answer": "KDAI 需要 Docker 和 PostgreSQL。",
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

## 專案結構

```
ScriBot/
├── docker-compose.yml         # Qdrant (本地備用)
├── Dockerfile
├── requirements.txt
├── backend/
│   ├── main.py                # FastAPI 入口
│   ├── config.py              # 設定管理
│   ├── routers/
│   │   └── chat.py            # /api/chat endpoint
│   ├── services/
│   │   ├── llm_providers/     # LLM Provider 抽象層
│   │   │   ├── base.py
│   │   │   ├── ollama.py
│   │   │   ├── groq.py
│   │   │   └── openai.py
│   │   ├── embedder.py        # 向量化服務
│   │   ├── searcher.py       # Qdrant 搜尋
│   │   ├── generator.py      # LLM 生成
│   │   ├── monitor.py         # 監控服務 ⭐ NEW
│   │   └── citation.py        # 引用追蹤 ⭐ NEW
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   └── scripts/
│       └── index_docs.py      # MDX indexing
├── chatbot_widget/            # Vue.js widget
│   ├── ChatWidget.vue
│   └── ...
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 履歷寫法

```
ScriBot - ML Inference Platform (Side Project)
- RAG-based Q&A chatbot with real-time model monitoring (latency, cost, tokens)
- Source citation tracking for AI-generated responses
- Triple LLM provider architecture (Ollama/Groq/OpenAI) with automatic fallback
- FastAPI REST API + Vue.js embedded widget + SSE streaming
- Railway deployment with Docker containerization
```

---

## 面試可說的點

1. **Triple LLM Provider + Fallback**
   → 「如何設計 fault-tolerant 的 ML inference 系統？」
   → 「如何控制 LLM 的成本？」

2. **模型監控 (Monitoring)**
   → 「模型上線後如何確保它正常運作？」
   → 「如何追蹤 LLM 的延遲和成本？」

3. **Citation Tracking**
   → 「RAG 為什麼要標註來源？」
   → 「如何實現可解釋的 AI？」

4. **ngrok 暴露本地資源**
   → 「如何把本地服務雲端化？」
   → 「這涉及哪些網路安全考量？」

5. **與 KDAI 的連結**
   → 參考 KDAI 的 Docker Compose 微服務架構
   → Ollama 本地 LLM 與 KDAI 一致
   → 補足 KDAI 欠缺的 semantic search 功能
   → 使用與 KDAI ATTS 相同的 Python 微服務模式
