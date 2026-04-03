from config import settings
from services.embedder import embedder
from services.qdrant_client import qdrant_service


# ─────────────────────────────────────────────────────────────
# RAG (Retrieval-Augmented Generation) Service
# ─────────────────────────────────────────────────────────────
#
# RAG Pipeline:
#   1. User query -> embed -> vector
#   2. Vector -> Qdrant search -> top-k chunks
#   3. Chunks -> context + sources for downstream prompt building
# RAG Concepts:
#   - Retrieval: Fetching relevant chunks from vector DB
#   - Augmentation: Using retrieved chunks to enhance LLM respons

# ─────────────────────────────────────────────────────────────


class RAGService:
    """
    RAG service for KDAI documentation
    """

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
    ) -> list[dict]:
        """
        Retrieve relevant chunks for a query

        Args:
            query: User question
            top_k: Number of search results

        Returns:
            list[dict]: Search results with {id, score, source, title, content}
        """
        if top_k is None:
            top_k = settings.top_k_results

        query_vector = await embedder.embed(query)
        return qdrant_service.search(query_vector, top_k=top_k)

    def build_context(self, results: list[dict]) -> str:
        """
        Build an LLM-friendly context string from search results
        """
        if not results:
            return "No relevant documentation found."

        context_parts = []
        for index, result in enumerate(results, start=1):
            context_parts.append(
                f"[{index}] Source: {result['source']}\n"
                f"    Title: {result['title']}\n"
                f"    Content: {result['content']}\n"
            )

        return "\n".join(context_parts)

    def build_sources(self, results: list[dict]) -> list[dict]:
        """
        Build lightweight source citations from search results
        """
        sources = []
        seen = set() # To avoid duplicate sources (same source file and title)

        for result in results:
            key = (result["source"], result["title"]) # Unique key for deduplication
            if key in seen: # Skip if we've already added this source
                continue

            seen.add(key) # Mark this source as seen to prevent duplicates
            sources.append(
                {
                    "source": result["source"],     # e.g., "install.md"
                    "title": result["title"],       # e.g., "Installation Guide"
                    "score": round(result["score"], 3),  # Rounded relevance score for display
                }
            )

        return sources

    def build_prompt(self, question: str, context: str) -> str:
        """
        Build the final prompt string for the selected LLM provider
        """
        return f"""Use the following KDAI documentation context to answer the user's question.
If the answer is not supported by the context, say you are not sure based on the documentation.

Context:
{context}

Question:
{question}

Answer in the same language as the user's question.
"""

    async def query(self, question: str, top_k: int = None) -> dict:
        """
        Full RAG query: retrieve + build context + build sources + build prompt for LLM

        Returns:
            dict: {context, prompt, sources, results}
        """
        results = await self.retrieve(question, top_k)
        context = self.build_context(results)

        return {
            "context": context,
            "prompt": self.build_prompt(question, context),
            "sources": self.build_sources(results),
            "results": results,
        }


# Singleton instance
rag_service = RAGService()
