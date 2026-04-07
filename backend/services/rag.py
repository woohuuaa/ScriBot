import re

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

    STOP_WORDS = {
        "a", "an", "and", "are", "does", "do", "for", "how", "in", "is", "kdai",
        "of", "the", "to", "what", "work", "works",
    }

    QUERY_EXPANSIONS = {
        "install": ["installation", "docker", "setup", "environment", "quick-start", "prerequisites"],
        "installation": ["install", "docker", "setup", "environment", "prerequisites"],
        "prerequisites": ["required", "requirements", "ports", "software"],
        "architecture": ["system", "services", "infrastructure", "components"],
        "whisperlive": ["atts", "transcription", "csp", "websocket"],
    }

    def _detect_response_language(self, question: str) -> str:
        if re.search(r"[\u4e00-\u9fff]", question):
            return "Chinese"

        dutch_markers = {
            "de", "het", "een", "wat", "hoe", "vergelijk", "vereisten", "functionele", "niet-functionele",
        }
        tokens = re.findall(r"[a-zA-Z]+", question.lower())
        if any(token in dutch_markers for token in tokens):
            return "Dutch"

        return "English"

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
        results = qdrant_service.search(query_vector, top_k=max(top_k, 50))
        reranked = self._rerank_results(query, results)
        return reranked[:top_k]

    def _rerank_results(self, query: str, results: list[dict]) -> list[dict]:
        """
        Apply a lightweight lexical reranking on top of vector search.
        """
        query_terms = self._extract_query_terms(query)
        if not query_terms:
            return results

        def rerank_score(result: dict) -> float:
            source_text = result["source"].lower()
            title_text = result["title"].lower()
            content_text = result["content"].lower()

            bonus = 0.0
            for term in query_terms:
                if term in source_text:
                    bonus += 0.08
                if term in title_text:
                    bonus += 0.12
                if term in content_text:
                    bonus += 0.04

            return float(result["score"]) + bonus

        return sorted(results, key=rerank_score, reverse=True)

    def _extract_query_terms(self, query: str) -> list[str]:
        """
        Extract meaningful query terms for lexical reranking.
        """
        terms = re.findall(r"[a-zA-Z0-9_-]+", query.lower())
        filtered_terms = [term for term in terms if len(term) > 2 and term not in self.STOP_WORDS]

        expanded_terms = []
        for term in filtered_terms:
            expanded_terms.append(term)
            expanded_terms.extend(self.QUERY_EXPANSIONS.get(term, []))

        # Preserve order while removing duplicates.
        return list(dict.fromkeys(expanded_terms))

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
        response_language = self._detect_response_language(question)

        return f"""Use the following KDAI documentation context to answer the user's question.
If the answer is not supported by the context, say you are not sure based on the documentation.
Answer in {response_language} only.
Do not switch to Dutch unless the user's question is in Dutch.
Do not copy the language of the documentation context if it differs from the user's question.

Context:
{context}

Question:
{question}
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

rag_service = RAGService()
