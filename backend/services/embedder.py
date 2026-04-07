import httpx
import asyncio
from typing import Callable, Optional
from config import settings
from fastembed import TextEmbedding
# ─────────────────────────────────────────────────────────────
# Embedder Service
# ─────────────────────────────────────────────────────────────
class Embedder:
    """
    Embedding service using Ollama's nomic-embed-text model
    
    Usage:
        embedder = Embedder()
        vector = await embedder.embed("Hello world")
        vectors = await embedder.embed_batch(["Hello", "World"])
    """
    
    def __init__(self):
        self.base_url = settings.ollama_base_url    # base_url = "http://ollama:11434"
        self.model = settings.ollama_embedding_model    # model = "nomic-embed-text"
        self.provider = settings.embedding_provider.lower()
        self._fastembed_model: TextEmbedding | None = None

    def _get_fastembed_model(self) -> TextEmbedding:
        if self._fastembed_model is None:
            self._fastembed_model = TextEmbedding(model_name=settings.fastembed_model)
        return self._fastembed_model

    async def _embed_with_fastembed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_fastembed_model()

        batch_size = max(1, settings.fastembed_batch_size)

        def run_embeddings() -> list[list[float]]:
            vectors: list[list[float]] = []
            for start in range(0, len(texts), batch_size):
                batch = texts[start : start + batch_size]
                vectors.extend(vector.tolist() for vector in model.embed(batch))
            return vectors

        return await asyncio.to_thread(run_embeddings)
    
    async def embed(self, text: str) -> list[float]:
        """
        Embed a single text into a 768-dim vector
        
        Args:
            text: The text to embed
            
        Returns:
            list[float]: 768-dimensional vector
            
        Example:
            vector = await embedder.embed("What is KDAI?")
            len(vector)  # 768
        """
        if self.provider == "fastembed":
            vectors = await self._embed_with_fastembed([text])
            return vectors[0]

        url = f"{self.base_url}/api/embeddings"
        
        # Send a POST request to the Ollama embeddings API using httpx.
        # Request format:
        # {
        #     "model": "nomic-embed-text",
        #     "prompt": "Your text here"
        # }
        # Response format:
        # {
        #     "embedding": [0.123, 0.456, ..., 0.789]  # 768-dim vector
        # }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            return response.json()["embedding"]
    
    async def embed_batch(
        self, 
        texts: list[str], 
        max_concurrent: int = 5,
        on_progress: Optional[Callable[[], None]] = None
    ) -> list[list[float]]:
        """
        Embed multiple texts in parallel
        
        Args:
            texts: List of texts to embed
            max_concurrent: Max parallel requests to avoid Ollama overload (default: 5)                           (avoid Ollama overload)
            on_progress: Optional callback called after each embedding completes
                         Optional callback used to update progress.
        
        Returns:
            list[list[float]]: List of 768-dim vectors
            
        Example:
            vectors = await embedder.embed_batch(["Hello", "World"])
            len(vectors)     # 2
            len(vectors[0])  # 768
        """
        if self.provider == "fastembed":
            vectors = await self._embed_with_fastembed(texts)
            if on_progress:
                for _ in texts:
                    on_progress()
            return vectors

        # Example: semaphore = asyncio.Semaphore(5)
        # async with semaphore limits concurrent tasks.
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def embed_with_semaphore(text: str) -> list[float]:
            async with semaphore:
                result = await self.embed(text)
                # Call progress callback if provided
                # Call the progress callback if provided.
                if on_progress:
                    on_progress()
                return result
        
        # Run all embedding requests concurrently.
        vectors = await asyncio.gather(
            *[embed_with_semaphore(text) for text in texts]
        )
        
        return list(vectors)
# ─────────────────────────────────────────────────────────────
# Singleton Instance (optional)
# ─────────────────────────────────────────────────────────────
embedder = Embedder()
