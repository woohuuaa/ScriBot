from services.agent.tools.base import Tool
from services.rag import rag_service

# ─────────────────────────────────────────────────────────────
# Search Docs Tool
# ─────────────────────────────────────────────────────────────
#
# Wrap the RAG service as an Agent tool.
# The Agent can use natural language queries and receive relevant documentation chunks.
# ─────────────────────────────────────────────────────────────

class SearchDocsTool(Tool):
    """
    Tool for searching KDAI documentation
    """

    def __init__(self):
        self.last_sources: list[dict] = []
    
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
        """
        # Use RAG service to search
        result = await rag_service.query(query)
        self.last_sources = result["sources"]
        
        if not result["results"]:
            return "No relevant documentation found for this query."
        
        # Return formatted context
        return result["context"]
