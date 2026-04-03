#!/usr/bin/env python3
"""
Index KDAI documentation into Qdrant vector database

Usage:
    python -m scripts.index_docs
    python -m scripts.index_docs --recreate
"""

import asyncio      # For running async embedding generation
import argparse     # For command-line argument parsing
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.chunker import chunker
from services.embedder import embedder
from services.qdrant_client import qdrant_service


# Path to KDAI documentation
DOCS_PATH = Path(__file__).parent.parent.parent / "Docs" / "src" / "content" / "docs"


async def index_documents(recreate: bool = False):
    """
    Main indexing function
    
    Steps:
    1. Create/recreate Qdrant collection
    2. Read and chunk all MDX files
    3. Generate embeddings for each chunk
    4. Upsert into Qdrant
    """
    print("=" * 60)
    print("KDAI Documentation Indexer")
    print("=" * 60)
    
    # Step 1: Create collection
    print("\n[1/4] Creating Qdrant collection...")
    qdrant_service.create_collection(recreate=recreate)
    
    # Step 2: Chunk documents
    print("\n[2/4] Chunking documents...")
    if not DOCS_PATH.exists():
        print(f"Error: Docs path not found: {DOCS_PATH}")
        return
    
    chunks = chunker.chunk_directory(DOCS_PATH)
    
    if not chunks:
        print("Error: No chunks generated!")
        return
    
    # Step 3: Generate embeddings
    print(f"\n[3/4] Generating embeddings for {len(chunks)} chunks...")
    print("      (This may take a few minutes...)")
    
    # Extract content for batch embedding
    texts = [chunk.content for chunk in chunks]
    
    # Batch embed with progress indication
    vectors = await embedder.embed_batch(texts, max_concurrent=5) # Limit concurrency to avoid rate limits
    
    print(f"      Generated {len(vectors)} embeddings")
    
    # Step 4: Upsert into Qdrant
    print("\n[4/4] Upserting into Qdrant...")
    
    ids = [chunk.id for chunk in chunks]
    payloads = [
        {
            "source": chunk.source,
            "title": chunk.title,
            "content": chunk.content,
        }
        for chunk in chunks
    ]
    
    qdrant_service.upsert_points(ids, vectors, payloads)
    
    # Done!
    print("\n" + "=" * 60)
    print("Indexing complete!")
    print("=" * 60)
    
    info = qdrant_service.get_collection_info()
    print(f"Collection: {info['name']}")
    print(f"Total points: {info['points_count']}")


def main():
    parser = argparse.ArgumentParser(description="Index KDAI docs into Qdrant")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection (delete existing data)",
    )
    args = parser.parse_args()
    
    asyncio.run(index_documents(recreate=args.recreate))


if __name__ == "__main__":
    main()