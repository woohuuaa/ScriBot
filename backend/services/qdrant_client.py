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
# ─────────────────────────────────────────────────────────────
# 
# Qdrant Concepts:
#   - Collection: like a table (類似資料表)
#   - Point: { id, vector, payload } (一筆資料)
#   - Vector: 768-dim embedding from nomic-embed-text
#   - Payload: metadata like { source, title, content }
#   - Distance: Cosine similarity (方向相似度，不看長度)
# ─────────────────────────────────────────────────────────────


class QdrantService:
    """
    Qdrant vector database service for RAG
    """
    
    def __init__(self):
        """
        Initialize Qdrant client
        
        Connection: http://qdrant:6333 (Docker network)
        """
        self.client = QdrantClient(
            host=settings.qdrant_host,  # "qdrant" (Docker service name)
            port=settings.qdrant_port,  # 6333
        )
        self.collection_name = settings.qdrant_collection   # "kdai_docs"
        self.dimension = settings.embedding_dimension       # 768
    
    def create_collection(self, recreate: bool = False) -> bool:
        """
        Create vector collection if it doesn't exist
        
        Args:
            recreate: If True, delete existing collection first
        
        Returns:
            bool: True if created, False if already existed
        """
        # Check if collection exists
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections) 
        
        if exists and not recreate:
            print(f"Collection '{self.collection_name}' already exists, skipping...")
            return False
        
        if exists and recreate:
            print(f"Deleting existing collection '{self.collection_name}'...")
            self.client.delete_collection(self.collection_name)
        
        # Create new collection
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
        query_filter = None # Default: no filter (search all documents)
        # If source_filter is provided (e.g., "install.md"), we create a filter to match the "source" field in the payload
        if source_filter:
            query_filter = Filter( 
                must=[
                    FieldCondition( 
                        key="source",                           # Filter by "source" field in payload
                        match=MatchValue(value=source_filter),  # Exact match (e.g., "install.md"
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
        """Get collection statistics"""
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