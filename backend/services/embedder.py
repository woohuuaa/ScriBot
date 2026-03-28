import httpx
import asyncio
from config import settings
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
        url = f"{self.base_url}/api/embeddings"
        
        # 使用 httpx 發送 POST 請求到 Ollama 的 embeddings API
        # 請求格式:
        # {
        #     "model": "nomic-embed-text",
        #     "prompt": "Your text here"
        # }
        # 回應格式:
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
        max_concurrent: int = 5
    ) -> list[list[float]]:
        """
        Embed multiple texts in parallel
        
        Args:
            texts: List of texts to embed
            max_concurrent: Max parallel requests to avoid Ollama overload (default: 5)                           (avoid Ollama overload)
        
        Returns:
            list[list[float]]: List of 768-dim vectors
            
        Example:
            vectors = await embedder.embed_batch(["Hello", "World"])
            len(vectors)     # 2
            len(vectors[0])  # 768
        """
        # usage: semaphore = asyncio.Semaphore(5)  # 計數器 = 5
        # async with semaphore:  # 每次最多 5 個任務同時執行
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def embed_with_semaphore(text: str) -> list[float]:
            async with semaphore:
                return await self.embed(text)
        
        # 並行執行所有 embedding 請求
        vectors = await asyncio.gather(
            *[embed_with_semaphore(text) for text in texts]
        )
        
        return list(vectors)
# ─────────────────────────────────────────────────────────────
# Singleton Instance (optional)
# ─────────────────────────────────────────────────────────────
embedder = Embedder()