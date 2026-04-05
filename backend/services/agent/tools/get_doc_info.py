from services.agent.tools.base import Tool
from services.qdrant_client import qdrant_service
from qdrant_client.models import Filter, FieldCondition, MatchValue

# ─────────────────────────────────────────────────────────────
# Get Doc Info Tool
# ─────────────────────────────────────────────────────────────


class GetDocInfoTool(Tool):
    """
    Tool for getting detailed information about a specific document
    """
    
    @property
    def name(self) -> str:
        return "get_doc_info"
    
    @property
    def description(self) -> str:
        return """Get detailed information about a specific document in the knowledge base.
Use this tool when you need to know the structure or content of a specific document.
Returns: number of chunks, section titles, and content preview."""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The document filename (e.g., 'architecture.mdx')"
                }
            },
            "required": ["filename"]
        }
    
    async def execute(self, filename: str) -> str:
        """
        Get information about a specific document
        """
        try:
            # Note: MVP uses a fixed scroll limit because current docs are small.
            # If a document can exceed this number of chunks later, add pagination.
            # Filter by source filename
            results, _ = qdrant_service.client.scroll(
                collection_name=qdrant_service.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="source",
                            match=MatchValue(value=filename)
                        )
                    ]
                ),
                limit=100,
                with_payload=True,
                with_vectors=False,
            )
            
            if not results:
                return f"Document '{filename}' not found in the knowledge base."
            
            # Extract information
            chunks = []
            titles = set()
            
            # We assume each point's payload has "content" for the chunk text and "title" for the section title (if available).
            # We collect all chunks to count them and gather unique section titles.
            for point in results:
                payload = point.payload
                chunks.append(payload.get("content", ""))
                if payload.get("title"):
                    titles.add(payload["title"])
            
            # Format output
            output = f"## Document: {filename}\n\n"
            output += f"**Chunks:** {len(chunks)}\n\n"
            
            # Section titles (if any)
            # We show unique section titles to give an overview of the document structure.
            if titles:
                output += f"**Sections:**\n"
                for title in sorted(titles):
                    output += f"- {title}\n"
                output += "\n"
            
            # Content preview (first chunk)
            if chunks:
                preview = chunks[0][:300] + "..." if len(chunks[0]) > 300 else chunks[0]
                output += f"**Preview:**\n{preview}\n"
            
            return output
            
        except Exception as e:
            return f"Error getting document info: {str(e)}"