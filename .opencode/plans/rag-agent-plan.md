# ScriBot RAG + Agent 實作計劃

## 目標
在 5-6 天內完成 **簡化版 AI Agent**，包含 RAG 搜尋功能。

## 完成後可展示
```
User: "What is KDAI's architecture?"

Agent:
┌────────────────────────────────────────────────────────────┐
│ Thought: 用戶想了解 KDAI 架構，我需要搜尋文檔              │
│ Action: search_docs                                        │
│ Action Input: {"query": "KDAI architecture"}               │
│                                                            │
│ Observation: Found 3 relevant chunks...                    │
│                                                            │
│ Thought: 我有足夠資訊回答了                                │
│ Final Answer: KDAI uses a microservices architecture...    │
│                                                            │
│ Sources: architecture.mdx, services.mdx                    │
└────────────────────────────────────────────────────────────┘
```

---

## 文件結構

```
backend/services/
├── embedder.py              ✅ 已完成
├── qdrant_client.py         ✅ Day 1 完成
├── chunker.py               ✅ Day 1 完成
├── rag.py                   📋 Day 2
│
└── agent/                   🆕 Day 4-6
    ├── __init__.py
    ├── tools/
    │   ├── __init__.py
    │   ├── base.py          📋 Day 4
    │   └── search_docs.py   📋 Day 5
    ├── agent.py             📋 Day 4
    └── prompts.py           📋 Day 4

backend/scripts/
└── index_docs.py            📋 Day 2

backend/main.py              📋 Day 3 + Day 6
```

---

## Day 1: qdrant_client.py + chunker.py

### 狀態: ✅ 完成

### Task 1.1: qdrant_client.py

**位置:** `backend/services/qdrant_client.py`

**功能:**
- `create_collection()` - 創建 Qdrant collection
- `upsert_points()` - 插入/更新向量
- `search()` - 搜尋相似文檔
- `get_collection_info()` - 取得統計資訊

**Code:**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from config import settings
from typing import Optional

# ─────────────────────────────────────────────────────────────
# Qdrant Vector Database Service
# Qdrant 向量資料庫服務
# ─────────────────────────────────────────────────────────────
# 
# Qdrant Concepts (Qdrant 概念):
#   - Collection: like a table (類似資料表)
#   - Point: { id, vector, payload } (一筆資料)
#   - Vector: 768-dim embedding from nomic-embed-text
#   - Payload: metadata like { source, title, content }
#   - Distance: Cosine similarity (方向相似度，不看長度)
# ─────────────────────────────────────────────────────────────


class QdrantService:
    """
    Qdrant vector database service for RAG
    用於 RAG 的 Qdrant 向量資料庫服務
    """
    
    def __init__(self):
        """
        Initialize Qdrant client
        初始化 Qdrant 客戶端
        
        Connection: http://qdrant:6333 (Docker network)
        """
        self.client = QdrantClient(
            host=settings.qdrant_host,  # "qdrant" (Docker service name)
            port=settings.qdrant_port,  # 6333
        )
        self.collection_name = settings.qdrant_collection  # "kdai_docs"
        self.dimension = settings.embedding_dimension       # 768
    
    def create_collection(self, recreate: bool = False) -> bool:
        """
        Create vector collection if it doesn't exist
        如果不存在就創建向量集合
        
        Args:
            recreate: If True, delete existing collection first
                      如果為 True，先刪除現有集合
        
        Returns:
            bool: True if created, False if already existed
        """
        # Check if collection exists / 檢查集合是否存在
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if exists and not recreate:
            print(f"Collection '{self.collection_name}' already exists, skipping...")
            return False
        
        if exists and recreate:
            print(f"Deleting existing collection '{self.collection_name}'...")
            self.client.delete_collection(self.collection_name)
        
        # Create new collection / 創建新集合
        print(f"Creating collection '{self.collection_name}'...")
        
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.dimension,      # 768
                distance=Distance.COSINE, # Cosine similarity
            ),
        )
        
        print(f"Collection '{self.collection_name}' created!")
        return True
    
    def upsert_points(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict],
    ) -> None:
        """
        Insert or update points in the collection
        插入或更新集合中的點
        
        Args:
            ids: Unique IDs (e.g., "install_chunk0")
            vectors: 768-dim embedding vectors
            payloads: Metadata dicts with {source, title, content}
        """
        points = [
            PointStruct(id=id_, vector=vector, payload=payload)
            for id_, vector, payload in zip(ids, vectors, payloads)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        
        print(f"Upserted {len(points)} points")
    
    def search(
        self,
        query_vector: list[float],
        top_k: int = None,
        source_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for similar documents
        搜尋相似文檔
        
        Args:
            query_vector: 768-dim query embedding
            top_k: Number of results (default: settings.top_k_results)
            source_filter: Optional filter by source file
        
        Returns:
            list[dict]: Results with {id, score, source, title, content}
        """
        if top_k is None:
            top_k = settings.top_k_results  # Default: 3
        
        # Build optional filter
        query_filter = None
        if source_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source_filter),
                    )
                ]
            )
        
        # Execute search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )
        
        # Format results
        return [
            {
                "id": r.id,
                "score": r.score,
                **r.payload,
            }
            for r in results
        ]
    
    def get_collection_info(self) -> dict:
        """Get collection statistics / 獲取集合統計"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "status": info.status.name,
            }
        except Exception as e:
            return {"name": self.collection_name, "error": str(e)}


# Singleton instance
qdrant_service = QdrantService()
```

**關鍵概念解釋:**

1. **為什麼用 Cosine Distance?**
   - 文本 embedding 的「方向」代表語意
   - Cosine 比較方向，不比較長度
   - "KDAI uses Docker" 和 "Docker is used by KDAI" 方向相似

2. **Upsert vs Insert**
   - Upsert = Insert or Update
   - 如果 ID 已存在就更新，不存在就插入
   - 適合重複索引文檔

3. **Payload 結構**
   ```python
   {
       "source": "install.mdx",    # 來源文件
       "title": "Installation",    # 章節標題
       "content": "To install..."  # 實際內容
   }
   ```

---

### Task 1.2: chunker.py

**位置:** `backend/services/chunker.py`

**功能:**
- 解析 MDX 文件
- 移除 frontmatter (---...---)
- 移除 import 語句
- 移除 Mermaid 圖表
- 按標題 (## / ###) 分割成 chunks

**Code:**
```python
import re
from pathlib import Path
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────
# MDX Document Chunker
# MDX 文檔分塊器
# ─────────────────────────────────────────────────────────────
#
# Why chunking? (為什麼要分塊?)
#   - LLM has token limits (LLM 有 token 限制)
#   - Smaller chunks = more precise retrieval (小塊 = 更精確檢索)
#   - Each chunk should be self-contained (每塊應該自成一體)
#
# Strategy: Split by headings (## / ###)
#   - Preserves semantic boundaries (保留語意邊界)
#   - Each chunk has a clear topic (每塊有明確主題)
# ─────────────────────────────────────────────────────────────


@dataclass
class Chunk:
    """
    A chunk of document content
    文檔內容的一個片段
    """
    id: str           # Unique ID: "filename_chunk0"
    source: str       # Source file: "install.mdx"
    title: str        # Section title: "Installation"
    content: str      # Actual content


class Chunker:
    """
    MDX document chunker for RAG pipeline
    用於 RAG 的 MDX 文檔分塊器
    """
    
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 2000):
        """
        Args:
            min_chunk_size: Minimum characters per chunk (太短就合併)
            max_chunk_size: Maximum characters per chunk (太長就截斷)
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk_file(self, file_path: Path) -> list[Chunk]:
        """
        Read and chunk a single MDX file
        讀取並分塊單個 MDX 文件
        
        Args:
            file_path: Path to the MDX file
            
        Returns:
            list[Chunk]: List of chunks from this file
        """
        content = file_path.read_text(encoding="utf-8")
        filename = file_path.stem  # "install" from "install.mdx"
        
        # Step 1: Clean the content / 清理內容
        cleaned = self._clean_mdx(content)
        
        # Step 2: Split by headings / 按標題分割
        sections = self._split_by_headings(cleaned)
        
        # Step 3: Create chunks / 創建 chunks
        chunks = []
        for i, (title, text) in enumerate(sections):
            # Skip empty sections / 跳過空白段落
            if len(text.strip()) < self.min_chunk_size:
                continue
            
            # Truncate if too long / 太長就截斷
            if len(text) > self.max_chunk_size:
                text = text[:self.max_chunk_size] + "..."
            
            chunks.append(Chunk(
                id=f"{filename}_chunk{i}",
                source=file_path.name,
                title=title or filename,  # Use filename if no title
                content=text.strip(),
            ))
        
        return chunks
    
    def chunk_directory(self, dir_path: Path) -> list[Chunk]:
        """
        Chunk all MDX files in a directory
        分塊目錄中的所有 MDX 文件
        
        Args:
            dir_path: Path to directory containing MDX files
            
        Returns:
            list[Chunk]: All chunks from all files
        """
        all_chunks = []
        mdx_files = list(dir_path.glob("**/*.mdx"))
        
        print(f"Found {len(mdx_files)} MDX files")
        
        for file_path in mdx_files:
            chunks = self.chunk_file(file_path)
            all_chunks.extend(chunks)
            print(f"  {file_path.name}: {len(chunks)} chunks")
        
        print(f"Total: {len(all_chunks)} chunks")
        return all_chunks
    
    def _clean_mdx(self, content: str) -> str:
        """
        Remove MDX-specific content that doesn't help RAG
        移除對 RAG 沒幫助的 MDX 內容
        """
        # 1. Remove frontmatter (---...---)
        # 移除 YAML frontmatter
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
        
        # 2. Remove import statements
        # 移除 import 語句
        content = re.sub(r'^import\s+.*$', '', content, flags=re.MULTILINE)
        
        # 3. Remove Mermaid diagrams (```mermaid...```)
        # 移除 Mermaid 圖表
        content = re.sub(r'```mermaid\n.*?```', '', content, flags=re.DOTALL)
        
        # 4. Remove HTML comments
        # 移除 HTML 註解
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # 5. Remove excessive blank lines
        # 移除過多空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def _split_by_headings(self, content: str) -> list[tuple[str, str]]:
        """
        Split content by ## or ### headings
        按 ## 或 ### 標題分割內容
        
        Returns:
            list[tuple[str, str]]: List of (title, content) tuples
        """
        # Pattern: ## or ### at start of line
        # 模式：行首的 ## 或 ###
        pattern = r'^(#{2,3})\s+(.+)$'
        
        sections = []
        current_title = ""
        current_content = []
        
        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                # Save previous section / 保存前一個段落
                if current_content:
                    sections.append((
                        current_title,
                        '\n'.join(current_content)
                    ))
                
                # Start new section / 開始新段落
                current_title = match.group(2)
                current_content = []
            else:
                current_content.append(line)
        
        # Don't forget the last section / 別忘了最後一個段落
        if current_content:
            sections.append((
                current_title,
                '\n'.join(current_content)
            ))
        
        return sections


# Singleton instance
chunker = Chunker()
```

**關鍵概念解釋:**

1. **為什麼按標題分割?**
   - 標題通常代表語意邊界
   - 每個 chunk 有明確的主題
   - 比固定字數分割更有意義

2. **min_chunk_size / max_chunk_size**
   - 太短的 chunk 資訊不足
   - 太長的 chunk 超出 embedding 最佳範圍
   - 100-2000 字元是合理範圍

3. **Chunk ID 格式**
   ```
   "install_chunk0" = install.mdx 的第 0 個 chunk
   "install_chunk1" = install.mdx 的第 1 個 chunk
   ```

---

### Day 1 測試方式

創建完後，可以在 Python 中測試：

```python
# 測試 chunker
from services.chunker import chunker
from pathlib import Path

chunks = chunker.chunk_file(Path("../Docs/src/content/docs/install.mdx"))
for c in chunks:
    print(f"{c.id}: {c.title[:30]}... ({len(c.content)} chars)")

# 測試 qdrant (需要 docker compose up)
from services.qdrant_client import qdrant_service

qdrant_service.create_collection()
print(qdrant_service.get_collection_info())
```

---

## Day 2: index_docs.py + rag.py

### 狀態: ⬜ 未開始

### Task 2.1: index_docs.py

**位置:** `backend/scripts/index_docs.py`

**功能:**
- CLI 腳本，索引全部 33 個 MDX 文件
- 使用 chunker 分塊
- 使用 embedder 產生向量
- 使用 qdrant_service 存入資料庫

**Code:**
```python
#!/usr/bin/env python3
"""
Index KDAI documentation into Qdrant vector database
將 KDAI 文檔索引到 Qdrant 向量資料庫

Usage:
    python -m scripts.index_docs
    python -m scripts.index_docs --recreate  # 重建索引
"""

import asyncio
import argparse
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.chunker import chunker
from services.embedder import embedder
from services.qdrant_client import qdrant_service


# Path to KDAI documentation
DOCS_PATH = Path(__file__).parent.parent.parent / "Docs" / "src" / "content" / "docs"


async def index_documents(recreate: bool = False):
    """
    Main indexing function
    主要索引函數
    
    Steps:
    1. Create/recreate Qdrant collection
    2. Read and chunk all MDX files
    3. Generate embeddings for each chunk
    4. Upsert into Qdrant
    """
    print("=" * 60)
    print("KDAI Documentation Indexer")
    print("=" * 60)
    
    # Step 1: Create collection / 創建集合
    print("\n[1/4] Creating Qdrant collection...")
    qdrant_service.create_collection(recreate=recreate)
    
    # Step 2: Chunk documents / 分塊文檔
    print("\n[2/4] Chunking documents...")
    if not DOCS_PATH.exists():
        print(f"Error: Docs path not found: {DOCS_PATH}")
        return
    
    chunks = chunker.chunk_directory(DOCS_PATH)
    
    if not chunks:
        print("Error: No chunks generated!")
        return
    
    # Step 3: Generate embeddings / 產生嵌入向量
    print(f"\n[3/4] Generating embeddings for {len(chunks)} chunks...")
    print("      (This may take a few minutes...)")
    
    # Extract texts for batch embedding
    texts = [chunk.content for chunk in chunks]
    
    # Batch embed with progress indication
    vectors = await embedder.embed_batch(texts, max_concurrent=5)
    
    print(f"      Generated {len(vectors)} embeddings")
    
    # Step 4: Upsert into Qdrant / 插入 Qdrant
    print("\n[4/4] Upserting into Qdrant...")
    
    ids = [chunk.id for chunk in chunks]
    payloads = [
        {
            "source": chunk.source,
            "title": chunk.title,
            "content": chunk.content,
        }
        for chunk in chunks
    ]
    
    qdrant_service.upsert_points(ids, vectors, payloads)
    
    # Done! / 完成！
    print("\n" + "=" * 60)
    print("Indexing complete!")
    print("=" * 60)
    
    info = qdrant_service.get_collection_info()
    print(f"Collection: {info['name']}")
    print(f"Total points: {info['points_count']}")


def main():
    parser = argparse.ArgumentParser(description="Index KDAI docs into Qdrant")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection (delete existing data)",
    )
    args = parser.parse_args()
    
    asyncio.run(index_documents(recreate=args.recreate))


if __name__ == "__main__":
    main()
```

**執行方式:**
```bash
# 在 backend container 內執行
docker compose exec backend python -m scripts.index_docs

# 或重建索引
docker compose exec backend python -m scripts.index_docs --recreate
```

---

### Task 2.2: rag.py

**位置:** `backend/services/rag.py`

**功能:**
- `retrieve()` - 用問題搜尋相關文檔
- `build_context()` - 把搜尋結果組成 LLM context

**Code:**
```python
from services.embedder import embedder
from services.qdrant_client import qdrant_service
from config import settings

# ─────────────────────────────────────────────────────────────
# RAG (Retrieval-Augmented Generation) Service
# RAG 檢索增強生成服務
# ─────────────────────────────────────────────────────────────
#
# RAG Pipeline:
#   1. User query → Embed → 768-dim vector
#   2. Vector → Qdrant search → Top-k similar chunks
#   3. Chunks → Build context → Add to LLM prompt
#   4. LLM generates answer with context
#
# 為什麼用 RAG?
#   - LLM 不知道 KDAI 的最新文檔
#   - RAG 讓 LLM 可以「讀」我們的文檔
#   - 回答更準確，還能提供引用來源
# ─────────────────────────────────────────────────────────────


class RAGService:
    """
    RAG service for KDAI documentation
    KDAI 文檔的 RAG 服務
    """
    
    async def retrieve(
        self,
        query: str,
        top_k: int = None,
    ) -> list[dict]:
        """
        Retrieve relevant documents for a query
        為查詢檢索相關文檔
        
        Args:
            query: User's question
            top_k: Number of results (default: settings.top_k_results)
            
        Returns:
            list[dict]: Relevant chunks with {id, score, source, title, content}
        """
        if top_k is None:
            top_k = settings.top_k_results
        
        # Step 1: Embed the query / 嵌入查詢
        query_vector = await embedder.embed(query)
        
        # Step 2: Search Qdrant / 搜尋 Qdrant
        results = qdrant_service.search(query_vector, top_k=top_k)
        
        return results
    
    def build_context(self, results: list[dict]) -> str:
        """
        Build context string from search results
        從搜尋結果構建上下文字串
        
        Args:
            results: Search results from retrieve()
            
        Returns:
            str: Formatted context for LLM prompt
        """
        if not results:
            return "No relevant documentation found."
        
        context_parts = []
        
        for i, r in enumerate(results, 1):
            context_parts.append(
                f"[{i}] Source: {r['source']}\n"
                f"    Title: {r['title']}\n"
                f"    Content: {r['content']}\n"
            )
        
        return "\n".join(context_parts)
    
    def build_sources(self, results: list[dict]) -> list[dict]:
        """
        Extract source citations from results
        從結果提取來源引用
        
        Returns:
            list[dict]: Sources with {source, title, score}
        """
        return [
            {
                "source": r["source"],
                "title": r["title"],
                "score": round(r["score"], 3),
            }
            for r in results
        ]
    
    async def query(self, question: str, top_k: int = None) -> dict:
        """
        Full RAG query: retrieve + build context
        完整 RAG 查詢：檢索 + 構建上下文
        
        Args:
            question: User's question
            top_k: Number of results
            
        Returns:
            dict: {context, sources, results}
        """
        results = await self.retrieve(question, top_k)
        
        return {
            "context": self.build_context(results),
            "sources": self.build_sources(results),
            "results": results,
        }


# Singleton instance
rag_service = RAGService()
```

**關鍵概念:**

1. **RAG Pipeline 流程**
   ```
   User: "How to install KDAI?"
         ↓
   [1] Embed query → [0.12, 0.34, ..., 0.56] (768-dim)
         ↓
   [2] Qdrant search → Top 3 similar chunks
         ↓
   [3] Build context → "[1] Source: install.mdx..."
         ↓
   [4] LLM prompt = system_prompt + context + question
         ↓
   [5] LLM generates answer
   ```

2. **Context 格式**
   ```
   [1] Source: install.mdx
       Title: Installation
       Content: To install KDAI, first ensure Docker is installed...

   [2] Source: docker-setup.mdx
       Title: Docker Setup
       Content: Run docker compose up -d to start all services...
   ```

---

## Day 3: main.py 更新 + RAG 測試

### 狀態: ⬜ 未開始

### Task 3.1: 更新 main.py

**修改:** `backend/main.py`

**新增內容:**
```python
# 在現有 imports 後加入
from services.rag import rag_service

# 修改 /api/chat endpoint
@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with RAG
    帶有 RAG 的聊天端點
    """
    # Step 1: Retrieve relevant context / 檢索相關上下文
    rag_result = await rag_service.query(request.message)
    
    # Step 2: Build enhanced prompt / 構建增強提示
    enhanced_message = f"""Based on the following documentation:

{rag_result['context']}

User question: {request.message}

Please answer the question based on the documentation above. If the documentation doesn't contain relevant information, say so.
"""
    
    # Step 3: Get LLM response / 獲取 LLM 回應
    provider = get_llm_provider(request.provider)
    
    response_text = ""
    async for chunk in provider.chat_stream([
        {"role": "user", "content": enhanced_message}
    ]):
        response_text += chunk
    
    # Step 4: Return with sources / 返回包含來源
    return {
        "response": response_text,
        "sources": rag_result['sources'],
        "provider": request.provider or settings.default_provider.value,
    }
```

---

### Task 3.2: 測試 RAG

**測試腳本 (可選):**
```python
# backend/scripts/test_rag.py
import asyncio
from services.rag import rag_service

async def test():
    questions = [
        "How do I install KDAI?",
        "What is the architecture of KDAI?",
        "How does WhisperLive work?",
    ]
    
    for q in questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        print('='*60)
        
        result = await rag_service.query(q)
        
        print("\nSources:")
        for s in result['sources']:
            print(f"  - {s['source']} ({s['score']})")
        
        print("\nContext preview:")
        print(result['context'][:500] + "...")

asyncio.run(test())
```

---

## Day 4: Agent 核心架構

### 狀態: ⬜ 未開始

### Task 4.1: agent/tools/base.py

**位置:** `backend/services/agent/tools/base.py`

**Code:**
```python
from abc import ABC, abstractmethod
from typing import Any

# ─────────────────────────────────────────────────────────────
# Tool Base Class
# 工具基類
# ─────────────────────────────────────────────────────────────
#
# 為什麼用抽象基類?
#   - 統一所有 tool 的接口
#   - Agent 可以動態發現和調用 tools
#   - 容易擴展新的 tools
#
# 每個 Tool 需要實現:
#   - name: 工具名稱 (Agent 用這個名稱調用)
#   - description: 描述 (幫助 Agent 決定何時使用)
#   - parameters: 參數 schema (JSON Schema 格式)
#   - execute(): 實際執行邏輯
# ─────────────────────────────────────────────────────────────


class Tool(ABC):
    """
    Abstract base class for Agent tools
    Agent 工具的抽象基類
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Tool name for Agent to reference
        Agent 引用的工具名稱
        
        Example: "search_docs"
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """
        Description of what this tool does
        工具功能描述
        
        Example: "Search KDAI documentation for relevant information"
        """
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        JSON Schema for tool parameters
        工具參數的 JSON Schema
        
        Example:
        {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """
        Execute the tool with given parameters
        用給定參數執行工具
        
        Args:
            **kwargs: Parameters matching the schema
            
        Returns:
            str: Tool execution result (will be shown to Agent)
        """
        pass
    
    def to_dict(self) -> dict:
        """
        Convert tool to dict for LLM prompt
        轉換為字典供 LLM prompt 使用
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
```

---

### Task 4.2: agent/prompts.py

**位置:** `backend/services/agent/prompts.py`

**Code:**
```python
# ─────────────────────────────────────────────────────────────
# Agent System Prompts
# Agent 系統提示詞
# ─────────────────────────────────────────────────────────────


def build_agent_prompt(tools: list[dict]) -> str:
    """
    Build the agent system prompt with available tools
    構建帶有可用工具的 Agent 系統提示詞
    
    Args:
        tools: List of tool dicts from Tool.to_dict()
    """
    # Format tools for prompt / 格式化工具描述
    tools_desc = ""
    for tool in tools:
        tools_desc += f"""
### {tool['name']}
{tool['description']}

Parameters:
```json
{tool['parameters']}
```
"""
    
    return f"""You are ScriBot Agent, an AI assistant specialized in KDAI documentation.

## Available Tools
{tools_desc}

## Response Format

You MUST respond in ONE of these two formats:

### Format 1: When you need to use a tool
```
Thought: [your reasoning about what to do]
Action: [tool_name]
Action Input: {{"param1": "value1", "param2": "value2"}}
```

### Format 2: When you have the final answer
```
Thought: [your reasoning]
Final Answer: [your complete response to the user]
```

## Rules
1. Always start with "Thought:" to explain your reasoning
2. Use tools to gather information before answering
3. After receiving Observation, continue with another Thought
4. When you have enough information, provide Final Answer
5. Answer in the same language as the user's question
6. Include source citations in your Final Answer

## Example

User: What is KDAI?

Thought: The user wants to know about KDAI. I should search the documentation.
Action: search_docs
Action Input: {{"query": "what is KDAI overview introduction"}}

Observation: [1] Source: index.mdx
    Title: Introduction
    Content: KDAI (KamerDebat AI) is a real-time parliamentary debate transcription system...

Thought: I found relevant information about KDAI. I can now provide a complete answer.
Final Answer: KDAI (KamerDebat AI) is a real-time parliamentary debate transcription and question extraction system. It uses microservices architecture with Docker...

Sources:
- index.mdx: Introduction
"""
```

---

### Task 4.3: agent/agent.py

**位置:** `backend/services/agent/agent.py`

**Code:**
```python
import re
import json
from typing import Optional
from services.agent.tools.base import Tool
from services.agent.prompts import build_agent_prompt

# ─────────────────────────────────────────────────────────────
# ReAct Agent
# ReAct 代理
# ─────────────────────────────────────────────────────────────
#
# ReAct = Reasoning + Acting
#
# Loop:
#   1. Thought: Agent 思考要做什麼
#   2. Action: 選擇並調用 tool
#   3. Observation: 觀察 tool 返回結果
#   4. 重複直到 Final Answer
#
# 這個架構的優點:
#   - 透明的推理過程 (可以 debug)
#   - 可擴展的 tool 系統
#   - 多步驟任務處理能力
# ─────────────────────────────────────────────────────────────


class Agent:
    """
    ReAct Agent for KDAI documentation
    用於 KDAI 文檔的 ReAct Agent
    """
    
    def __init__(
        self,
        llm_provider,
        tools: list[Tool],
        max_steps: int = 10,
    ):
        """
        Args:
            llm_provider: LLM provider instance (e.g., GroqProvider)
            tools: List of available tools
            max_steps: Maximum reasoning steps (prevent infinite loops)
        """
        self.llm = llm_provider
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        
        # Build system prompt with tools
        tool_dicts = [tool.to_dict() for tool in tools]
        self.system_prompt = build_agent_prompt(tool_dicts)
    
    async def run(self, user_input: str) -> dict:
        """
        Run the agent loop
        執行 Agent 循環
        
        Args:
            user_input: User's question or request
            
        Returns:
            dict: {
                "answer": Final answer string,
                "steps": List of reasoning steps,
                "sources": List of sources (if any)
            }
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        
        steps = []  # Record all steps for transparency
        
        for step_num in range(self.max_steps):
            # Get LLM response / 獲取 LLM 回應
            response = await self._get_llm_response(messages)
            
            # Parse the response / 解析回應
            parsed = self._parse_response(response)
            
            # Record this step / 記錄這一步
            steps.append({
                "step": step_num + 1,
                "thought": parsed.get("thought", ""),
                "action": parsed.get("action"),
                "action_input": parsed.get("action_input"),
                "final_answer": parsed.get("final_answer"),
            })
            
            # Check if we have final answer / 檢查是否有最終答案
            if parsed.get("final_answer"):
                return {
                    "answer": parsed["final_answer"],
                    "steps": steps,
                    "sources": self._extract_sources(parsed["final_answer"]),
                }
            
            # Execute tool if action specified / 如果有 action 就執行 tool
            if parsed.get("action"):
                observation = await self._execute_tool(
                    parsed["action"],
                    parsed.get("action_input", {})
                )
                
                # Add assistant response and observation to messages
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Observation: {observation}"})
                
                # Update step with observation
                steps[-1]["observation"] = observation
            else:
                # No action and no final answer - something went wrong
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": "Please either use a tool (Action) or provide a Final Answer."
                })
        
        # Max steps reached / 達到最大步數
        return {
            "answer": "I apologize, but I couldn't complete the task within the allowed steps. Please try rephrasing your question.",
            "steps": steps,
            "sources": [],
        }
    
    async def _get_llm_response(self, messages: list[dict]) -> str:
        """Get response from LLM (non-streaming)"""
        response = ""
        async for chunk in self.llm.chat_stream(messages):
            response += chunk
        return response
    
    def _parse_response(self, response: str) -> dict:
        """
        Parse agent response to extract Thought, Action, Final Answer
        解析 Agent 回應，提取 Thought、Action、Final Answer
        """
        result = {}
        
        # Extract Thought / 提取 Thought
        thought_match = re.search(r'Thought:\s*(.+?)(?=Action:|Final Answer:|$)', response, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
        
        # Extract Final Answer / 提取 Final Answer
        final_match = re.search(r'Final Answer:\s*(.+)', response, re.DOTALL)
        if final_match:
            result["final_answer"] = final_match.group(1).strip()
            return result  # If final answer, don't need action
        
        # Extract Action / 提取 Action
        action_match = re.search(r'Action:\s*(\w+)', response)
        if action_match:
            result["action"] = action_match.group(1).strip()
        
        # Extract Action Input / 提取 Action Input
        input_match = re.search(r'Action Input:\s*(\{.+?\})', response, re.DOTALL)
        if input_match:
            try:
                result["action_input"] = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                result["action_input"] = {}
        
        return result
    
    async def _execute_tool(self, tool_name: str, params: dict) -> str:
        """Execute a tool and return observation"""
        tool = self.tools.get(tool_name)
        
        if not tool:
            return f"Error: Unknown tool '{tool_name}'. Available tools: {list(self.tools.keys())}"
        
        try:
            result = await tool.execute(**params)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def _extract_sources(self, answer: str) -> list[dict]:
        """Extract source citations from final answer"""
        sources = []
        
        # Look for "Sources:" section
        sources_match = re.search(r'Sources?:\s*\n((?:[-•]\s*.+\n?)+)', answer)
        if sources_match:
            source_lines = sources_match.group(1).strip().split('\n')
            for line in source_lines:
                # Extract filename from "- filename.mdx: description"
                match = re.match(r'[-•]\s*(\S+\.mdx)', line)
                if match:
                    sources.append({"source": match.group(1)})
        
        return sources
```

---

## Day 5: search_docs Tool

### 狀態: ⬜ 未開始

### Task 5.1: agent/tools/search_docs.py

**位置:** `backend/services/agent/tools/search_docs.py`

**Code:**
```python
from services.agent.tools.base import Tool
from services.rag import rag_service

# ─────────────────────────────────────────────────────────────
# Search Docs Tool
# 搜尋文檔工具
# ─────────────────────────────────────────────────────────────
#
# 這個 Tool 把 RAG service 包裝成 Agent 可以使用的工具
# Agent 可以用自然語言查詢，Tool 返回相關文檔片段
# ─────────────────────────────────────────────────────────────


class SearchDocsTool(Tool):
    """
    Tool for searching KDAI documentation
    搜尋 KDAI 文檔的工具
    """
    
    @property
    def name(self) -> str:
        return "search_docs"
    
    @property
    def description(self) -> str:
        return """Search KDAI documentation for relevant information.
Use this tool to find information about KDAI architecture, installation, 
configuration, troubleshooting, and other technical details.
Always search before answering questions about KDAI."""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant documentation"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, query: str) -> str:
        """
        Execute search and return formatted results
        執行搜尋並返回格式化結果
        """
        # Use RAG service to search / 使用 RAG service 搜尋
        result = await rag_service.query(query)
        
        if not result["results"]:
            return "No relevant documentation found for this query."
        
        # Return formatted context / 返回格式化的上下文
        return result["context"]
```

---

### Task 5.2: agent/__init__.py

**位置:** `backend/services/agent/__init__.py`

**Code:**
```python
from services.agent.agent import Agent
from services.agent.tools.search_docs import SearchDocsTool

__all__ = ["Agent", "SearchDocsTool"]
```

**位置:** `backend/services/agent/tools/__init__.py`

**Code:**
```python
from services.agent.tools.base import Tool
from services.agent.tools.search_docs import SearchDocsTool

__all__ = ["Tool", "SearchDocsTool"]
```

---

## Day 6: API Endpoint + 測試

### 狀態: ⬜ 未開始

### Task 6.1: 更新 main.py

**新增 endpoint:**
```python
from services.agent import Agent, SearchDocsTool
from pydantic import BaseModel

class AgentRequest(BaseModel):
    message: str
    provider: str = None

@app.post("/api/agent/run")
async def run_agent(request: AgentRequest):
    """
    Run the ReAct agent
    執行 ReAct Agent
    """
    # Get LLM provider
    provider = get_llm_provider(request.provider)
    
    # Create agent with tools
    agent = Agent(
        llm_provider=provider,
        tools=[SearchDocsTool()],
        max_steps=10,
    )
    
    # Run agent
    result = await agent.run(request.message)
    
    return {
        "answer": result["answer"],
        "steps": result["steps"],
        "sources": result["sources"],
        "provider": request.provider or settings.default_provider.value,
    }
```

---

### Task 6.2: 測試 Agent

**cURL 測試:**
```bash
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message": "What is KDAI and how do I install it?", "provider": "groq"}'
```

**預期回應:**
```json
{
  "answer": "KDAI (KamerDebat AI) is a real-time parliamentary debate transcription system...\n\nTo install KDAI:\n1. Clone the repository\n2. Run docker compose up -d\n...\n\nSources:\n- index.mdx: Introduction\n- install.mdx: Installation",
  "steps": [
    {
      "step": 1,
      "thought": "User wants to know about KDAI and installation...",
      "action": "search_docs",
      "action_input": {"query": "KDAI introduction overview"},
      "observation": "[1] Source: index.mdx..."
    },
    {
      "step": 2,
      "thought": "I found info about KDAI, now I need installation steps...",
      "action": "search_docs",
      "action_input": {"query": "KDAI installation setup"},
      "observation": "[1] Source: install.mdx..."
    },
    {
      "step": 3,
      "thought": "I have enough information to answer...",
      "final_answer": "KDAI (KamerDebat AI) is..."
    }
  ],
  "sources": [
    {"source": "index.mdx"},
    {"source": "install.mdx"}
  ],
  "provider": "groq"
}
```

---

## 完成後的 Bullet Point

> • **Built RAG-powered AI agent** using ReAct architecture with modular tool system, Qdrant vector database for semantic search, and multiple LLM providers (Ollama/Groq), enabling multi-step reasoning over 30+ technical documents with source citations

---

## Checklist

### Day 1
- [x] 創建 `backend/services/qdrant_client.py`
- [x] 創建 `backend/services/chunker.py`
- [x] 測試 Qdrant 連接
- [x] 測試 chunker 分塊 (33 MDX files → 639 chunks)

### Day 2
- [ ] 創建 `backend/scripts/index_docs.py`
- [ ] 執行索引 (33 個 MDX 文件)
- [ ] 創建 `backend/services/rag.py`
- [ ] 測試 RAG 搜尋

### Day 3
- [ ] 更新 `backend/main.py` (加入 RAG)
- [ ] End-to-end 測試 RAG chatbot

### Day 4
- [ ] 創建 `backend/services/agent/tools/base.py`
- [ ] 創建 `backend/services/agent/prompts.py`
- [ ] 創建 `backend/services/agent/agent.py`

### Day 5
- [ ] 創建 `backend/services/agent/tools/search_docs.py`
- [ ] 創建 `__init__.py` 文件

### Day 6
- [ ] 更新 `backend/main.py` (加入 `/api/agent/run`)
- [ ] End-to-end 測試 Agent
- [ ] 調整 prompt (如果需要)

---

## 有問題隨時問！

每個 Task 都有完整的 code 和解釋。你可以：
1. 一個一個實作
2. 遇到問題就問我
3. 需要更詳細解釋也可以問

祝你順利！💪
