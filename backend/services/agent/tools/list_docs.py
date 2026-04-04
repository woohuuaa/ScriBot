from services.agent.tools.base import Tool
from services.qdrant_client import qdrant_service

# ─────────────────────────────────────────────────────────────
# List Docs Tool
# ─────────────────────────────────────────────────────────────


class ListDocsTool(Tool):
    """
    Tool for listing all indexed documents
    """
    
    @property
    def name(self) -> str:
        return "list_docs"
    
    @property
    def description(self) -> str:
        return """List all documents in the KDAI knowledge base.
Use this tool when you need to know what documents are available,
or when the user asks about the documentation structure."""
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def execute(self) -> str:
        """
        List all unique document sources from Qdrant
        """
        # Get all points and extract unique sources
        # Note: MVP can use a single scroll call because the dataset is small.
        # If docs grow larger later, switch to paginated scroll.
        try:
            # Scroll through all points to get sources
            results, _ = qdrant_service.client.scroll(
                collection_name=qdrant_service.collection_name,
                limit=1000,  # Should be enough for our docs
                with_payload=True,
                with_vectors=False,
            )
            
            # Extract unique sources
            # We assume each point's payload has a "source" field indicating the document it came from.
            sources = set()
            for point in results:
                if "source" in point.payload:
                    sources.add(point.payload["source"])  # Add source to set for uniqueness
            
            if not sources:
                return "No documents found in the knowledge base."
            
            # Format output
            doc_list = sorted(sources)
            output = f"Found {len(doc_list)} documents in the knowledge base:\n\n"
            for doc in doc_list:
                output += f"- {doc}\n"
            
            return output
            
        except Exception as e:
            return f"Error listing documents: {str(e)}"