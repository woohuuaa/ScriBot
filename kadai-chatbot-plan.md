# ScriBot - AI-Powered Documentation Chatbot

## 目標

建立一個結合課程技術的 AI Chatbot，目標投遞 Autodesk Internship：

- RAG-based Q&A Chatbot for KDAI documentation
- A/B Testing Framework（使用者可選擇不同 LLM Provider）
- Statistical Analysis（Latency、Cost、User Feedback）
- Personalization（儲存提問歷史）
- 採用課程教授的技術棧（Docker、EC2、GitHub Actions、DynamoDB）

---

## 技術棧（配合課程）

| 組件 | 選擇 | 對應課程內容 |
|------|------|--------------|
| Backend | FastAPI (Python) | Week 1: Microservices |
| Frontend | Vue.js widget | 前端開發 |
| LLM | Ollama + Groq + OpenAI | 三層容錯 |
| Embedding | nomic-embed-text | Ollama 官方推薦 |
| Vector DB | Qdrant | AI 向量資料庫 |
| Container | Docker | Week 5-7: Docker |
| Container Orchestration | docker compose | Week 10: docker compose |
| CI/CD | GitHub Actions | Week 3, 8: GitHub Actions |
| Deployment | AWS EC2 | Week 4: EC2 |
| Database | DynamoDB | Week 12: DynamoDB |
| Storage | Local | Week 11: S3 (可選) |
| IaC | - | Week 13: CloudFormation (可選) |

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
│                     (Embedded in Docs)                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │ SSE Stream
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (AWS EC2)                    │
│                         (Docker Container)                        │
│                                                                  │
│  POST /api/index      ← 索引 docs (33 MDX)                      │
│  POST /api/chat       ← SSE streaming 回覆                      │
│  GET  /api/health     ← 健康檢查                                │
│  GET  /api/stats      ← 監控統計                                │
│  POST /api/feedback   ← 使用者回饋                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Monitoring Layer ⭐                                      │    │
│  │  ├── Latency: 1.2s                                      │    │
│  │  ├── Cost: $0.00 (Ollama)                              │    │
│  │  ├── Tokens: 2048                                       │    │
│  │  └── Fallback count: 0                                   │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  A/B Testing Layer ⭐                                    │    │
│  │  ├── User selected: Ollama                              │    │
│  │  ├── Provider usage stats: {ollama: 60%, groq: 30%}     │    │
│  │  └── User feedback: 👍 85%                              │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│     Ollama      │   │      Groq       │   │     OpenAI     │
│   (Primary)     │   │    (Backup)     │   │    (Backup)    │
│   llama3.1:8b   │   │ llama-3.3-70b  │   │   gpt-4o-mini  │
│   你的 4060     │   │     免費        │   │   $5 credit    │
└─────────────────┘   └─────────────────┘   └─────────────────┘
                               │
┌─────────────────┐   ┌─────────────────┐
│     Qdrant      │   │    DynamoDB    │
│   (Vector DB)   │   │  (User History) │
└─────────────────┘   └─────────────────┘
```

---

## RAG Pipeline

```
Step 1: Index
  33 MDX → 解析 → 切 chunk (500 tokens) → nomic-embed-text → 存入 Qdrant

Step 2: Search
  問題 → 轉向量 → Qdrant cosine similarity → Top-3 chunks + 分數

Step 3: Generate
  問題 + chunks → Prompt → LLM → SSE streaming
                  │
                  ├── ⏱ Latency tracking
                  ├── 💰 Cost tracking
                  └── 📊 Token counting
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

## A/B Testing Framework ⭐

| 功能 | 說明 | 面試話題 |
|------|------|----------|
| Provider Selection | 使用者可以選擇用哪個 LLM | 了解 A/B Testing 概念 |
| Usage Statistics | 記錄每個 Provider 被選的次數 | 資料收集與分析 |
| User Feedback | 收集使用者 👍/👎 回饋 | Statistical Analysis |

### 使用者流程

```
1. 使用者打開聊天框
2. 看到 Provider 選項（Ollama / Groq / OpenAI）
3. 選擇一個後傳送問題
4. 回答後可以給 👍 或 👎
5. 系統記錄：選擇 + 回饋 + Latency + Cost
```

---

## Statistical Analysis ⭐

| 指標 | 說明 | 面試話題 |
|------|------|----------|
| Latency | 每個步驟耗時 | 如何優化模型延遲？ |
| Cost | 每次請求估計成本 | 如何控制 LLM 成本？ |
| Tokens | 輸入/輸出 token 數 | Token 怎麼計費？ |
| User Feedback | 👍/👎 回饋比率 | 如何衡量使用者滿意度？ |
| Provider Distribution | 各 Provider 被選次數 | A/B Testing 結果分析 |

---

## Personalization ⭐

| 功能 | 說明 | 面試話題 |
|------|------|----------|
| Query History | 儲存提問歷史到 DynamoDB | NoSQL 資料庫應用 |
| History Display | 顯示過去提問 | 使用者體驗優化 |

---

## 4 週時程

### Week 1: 核心架構 + Docker + docker compose

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1 | 建立專案結構 + Dockerfile | Docker 化 |
| 2 | 建立 docker-compose.yml | 多容器管理 |
| 3 | FastAPI 基本架構 | Microservices |
| 4 | 三個 LLM Provider 串接 | Ollama / Groq / OpenAI |
| 5-7 | 本地 Docker 測試成功 | 可運作的容器 |

**交付**: `docker compose up` 可啟動服務

---

### Week 2: RAG Pipeline + DynamoDB

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1-2 | Qdrant 串接 + Embedding | Vector DB 就緒 |
| 3-4 | DynamoDB 設定 + 存使用者歷史 | Personalization |
| 5-6 | Monitoring Layer (Latency/Cost) | Statistical Analysis |
| 7 | RAG Pipeline 完成 | 可問答的 Chatbot |

**交付**: RAG Pipeline 可正常運作

---

### Week 3: CI/CD + A/B Testing

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1-2 | GitHub Actions CI workflow | 自動化測試 |
| 3-4 | A/B Testing Framework | 使用者可選 Provider |
| 5-6 | User Feedback 收集 | Statistical Analysis |
| 7 | 基本 Widget | 可嵌入的聊天框 |

**交付**: GitHub Actions CI pipeline + A/B Testing

---

### Week 4: AWS EC2 部署 + CD Pipeline

| Day | 任務 | 交付物 |
|-----|------|--------|
| 1-2 | AWS EC2 設定 + 部署 | Live Demo |
| 3-4 | CD Pipeline (GitHub Actions) | 自動部署 |
| 5-6 | Personalization + 完善化 | 功能完整 |
| 7 | README + 面試準備 | 可放履歷 |

**交付**: Production-ready、可上線、Live Demo URL

---

## API Endpoints

| Method | Endpoint | 描述 |
|--------|----------|------|
| POST | `/api/index` | 索引所有 .mdx 文件 |
| POST | `/api/chat` | SSE streaming 回覆 |
| GET | `/api/health` | 健康檢查 |
| GET | `/api/stats` | 監控統計 |
| POST | `/api/feedback` | 提交使用者回饋 |
| GET | `/api/history` | 取得提問歷史 |
| POST | `/api/select-provider` | 選擇 LLM Provider |

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

## 專案結構

```
ScriBot/
├── docker-compose.yml         # 多容器管理
├── Dockerfile                  # Backend 容器化
├── requirements.txt
├── backend/
│   ├── main.py                # FastAPI 入口
│   ├── config.py              # 設定管理
│   ├── routers/
│   │   └── chat.py            # API endpoints
│   ├── services/
│   │   ├── llm_providers/     # LLM Provider 抽象層
│   │   │   ├── base.py
│   │   │   ├── ollama.py
│   │   │   ├── groq.py
│   │   │   └── openai.py
│   │   ├── embedder.py        # 向量化服務
│   │   ├── searcher.py        # Qdrant 搜尋
│   │   ├── generator.py        # LLM 生成
│   │   ├── monitor.py          # 監控服務
│   │   └── dynamodb.py         # DynamoDB 操作
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

## 履歷寫法

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

## 面試可說的點

1. **A/B Testing Framework**
   → 「我在 ScriBot 實作了 A/B Testing Framework，讓使用者可以選擇不同 LLM Provider 並記錄選擇」
   → 「這符合 Autodesk JD 要求的 A/B Testing 經驗」

2. **Statistical Analysis**
   → 「我有追蹤 Latency、Cost、User Feedback，並分析不同 Provider 的表現」
   → 「了解如何收集和分析資料來優化系統」

3. **DynamoDB (NoSQL)**
   → 「使用 DynamoDB 儲存使用者提問歷史」
   → 「Week 12 會在課程中學 DynamoDB，這是我的實際應用」

4. **Docker + docker compose**
   → 「用 Docker 容器化 Backend，用 docker compose 管理多個容器」
   → 「Week 5-7 會在課程中學 Docker，這是我的提前實作」

5. **GitHub Actions CI/CD**
   → 「用 GitHub Actions 做自動化測試和部署」
   → 「Week 3, 8 會在課程中學 GitHub Actions」

6. **AWS EC2 部署**
   → 「部署到 AWS EC2，學習雲端部署流程」
   → 「Week 4 會在課程中學 EC2」

7. **與 KDAI 的連結**
   → 參考 KDAI 的 Docker Compose 微服務架構
   → Ollama 本地 LLM 與 KDAI 一致
   → 補足 KDAI 欠缺的 semantic search 功能
