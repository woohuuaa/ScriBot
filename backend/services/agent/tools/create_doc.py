from pathlib import Path
import uuid
from services.agent.tools.base import Tool
from services.chunker import chunker
from services.embedder import embedder
from services.qdrant_client import qdrant_service

# ─────────────────────────────────────────────────────────────
# Create Doc Tool
# 創建文檔工具
# ─────────────────────────────────────────────────────────────
#
# 這個 Tool 會：
# 1. 將內容寫入 MDX 文件
# 2. 對文件進行分塊 (chunking)
# 3. 對每個 chunk 生成 embedding
# 4. 將 chunks 存入 Qdrant
# ─────────────────────────────────────────────────────────────

# Path to docs directory (in Docker container)
# 文檔目錄路徑（在 Docker 容器中）
DOCS_PATH = Path("/app/Docs/src/content/docs")


class CreateDocTool(Tool):
    """
    Tool for creating new documents in the knowledge base
    在知識庫中創建新文檔的工具
    """
    
    @property
    def name(self) -> str:
        return "create_doc"
    
    @property
    def description(self) -> str:
        return """Create a new document and add it to the KDAI knowledge base.
Use this tool when the user wants to add new documentation.
The document will be automatically chunked, embedded, and indexed for search.
Content should be in Markdown format."""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename for the new document (e.g., 'new-guide.mdx')"
                },
                "title": {
                    "type": "string",
                    "description": "Document title for the frontmatter"
                },
                "content": {
                    "type": "string",
                    "description": "Document content in Markdown format"
                }
            },
            "required": ["filename", "title", "content"]
        }
    
    async def execute(self, filename: str, title: str, content: str) -> str:
        """
        Create a new document and index it
        """
        try:
            # Validate filename
            if not filename.endswith(".mdx"):
                filename = filename + ".mdx"
            
            file_path = DOCS_PATH / filename
            
            # Check if file already exists
            if file_path.exists():
                return f"Error: Document '{filename}' already exists. Use delete_doc first or choose a different name."
            
            # Create MDX content with frontmatter
            mdx_content = f"""---
title: {title}
description: {title}
---

{content}
"""
            
            # Step 1: Write file
            file_path.write_text(mdx_content, encoding="utf-8")
            
            # Step 2: Chunk the file
            chunks = chunker.chunk_file(file_path)
            
            if not chunks:
                return f"Warning: Document '{filename}' created but no chunks generated (content may be too short)."
            
            # Step 3: Generate embeddings
            # We create a text representation for each chunk that includes source, title, and content.
            texts = [
                f"Source: {chunk.source}\nTitle: {chunk.title}\nContent: {chunk.content}"
                for chunk in chunks
            ]
            vectors = await embedder.embed_batch(texts, max_concurrent=5)
            
            # Step 4: Upsert to Qdrant
            # Qdrant point IDs must be uint or UUID, not arbitrary strings.
            ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.id)) for chunk in chunks]
            payloads = [
                {
                    "source": chunk.source,
                    "title": chunk.title,
                    "content": chunk.content,
                }
                for chunk in chunks
            ]
            
            qdrant_service.upsert_points(ids, vectors, payloads)
            
            return f"""Document created successfully!

**File:** {filename}
**Title:** {title}
**Chunks indexed:** {len(chunks)}

The document is now searchable in the knowledge base."""
            
        except Exception as e:
            return f"Error creating document: {str(e)}"