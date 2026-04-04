from pathlib import Path
from services.agent.tools.base import Tool
from services.qdrant_client import qdrant_service
from qdrant_client.models import Filter, FieldCondition, MatchValue

# ─────────────────────────────────────────────────────────────
# Delete Doc Tool
# ─────────────────────────────────────────────────────────────

# Path to docs directory (in Docker container)
DOCS_PATH = Path("/app/Docs/src/content/docs")


class DeleteDocTool(Tool):
    """
    Tool for deleting documents from the knowledge base
    """
    
    @property
    def name(self) -> str:
        return "delete_doc"
    
    @property
    def description(self) -> str:
        return """Delete a document from the KDAI knowledge base.
Use this tool when the user wants to remove documentation.
This will remove the document file and all its indexed chunks from the vector database."""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename of the document to delete (e.g., 'old-guide.mdx')"
                }
            },
            "required": ["filename"]
        }
    
    async def execute(self, filename: str) -> str:
        """
        Delete a document and remove from index
        """
        try:
            # Note: MVP uses a fixed scroll limit because current docs are small.
            # If a document can exceed this number of chunks later, add pagination.
            # Validate filename
            if not filename.endswith(".mdx"):
                filename = filename + ".mdx"
            
            file_path = DOCS_PATH / filename
            
            # Step 1: Delete from Qdrant
            # First, count how many chunks will be deleted
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
                with_payload=False,
                with_vectors=False,
            )
            
            chunks_deleted = len(results)
            
            if chunks_deleted > 0:
                # Delete points by filter
                qdrant_service.client.delete(
                    collection_name=qdrant_service.collection_name,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key="source",
                                match=MatchValue(value=filename)
                            )
                        ]
                    ),
                )
            
            # Step 2: Delete physical file (if exists)
            file_deleted = False
            if file_path.exists():
                file_path.unlink()
                file_deleted = True
            
            # Format response
            if chunks_deleted == 0 and not file_deleted:
                return f"Document '{filename}' not found in the knowledge base or file system."
            
            response = f"Document '{filename}' deleted successfully!\n\n"
            if chunks_deleted > 0:
                response += f"**Chunks removed from index:** {chunks_deleted}\n"
            if file_deleted:
                response += f"**File deleted:** {file_path}\n"
            
            return response
            
        except Exception as e:
            return f"Error deleting document: {str(e)}"