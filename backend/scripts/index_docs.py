#!/usr/bin/env python3
"""
Index KDAI documentation into Qdrant vector database

Usage:
    python -m scripts.index_docs
    python -m scripts.index_docs --recreate
"""

import asyncio      # For running async embedding generation
import argparse     # For command-line argument parsing
import uuid         # For generating Qdrant-compatible UUIDs from chunk IDs
import time         # For timing embedding generation
from pathlib import Path
from tqdm import tqdm  # For progress bar

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.chunker import chunker
from services.embedder import embedder
from services.qdrant_client import qdrant_service


# Path to KDAI documentation (in Docker container, this is mounted at /app/Docs)
DOCS_PATH = Path("/app/Docs/src/content/docs")


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
    
    # Build richer text for embedding so retrieval can use title/source clues.
    texts = [
        f"Source: {chunk.source}\nTitle: {chunk.title}\nContent: {chunk.content}"
        for chunk in chunks
    ]
    
    # Batch embed with progress bar and timing
    start_time = time.time()
    
    # Create progress bar for embedding process
    pbar = tqdm(total=len(chunks), desc="Embedding", unit="chunk")
    
    # Progress callback to update tqdm
    def update_progress():
        pbar.update(1)
    
    vectors = await embedder.embed_batch(
        texts, 
        max_concurrent=5,
        on_progress=update_progress
    )
    
    pbar.close()
    elapsed_time = time.time() - start_time
    
    # Calculate and display timing statistics
    avg_time_per_chunk = elapsed_time / len(chunks) if chunks else 0
    print(f"      Generated {len(vectors)} embeddings in {elapsed_time:.2f}s ({avg_time_per_chunk:.3f}s/chunk)")
    
    # Step 4: Upsert into Qdrant
    print("\n[4/4] Upserting into Qdrant...")
    
    # Convert string IDs to UUIDs (Qdrant only accepts unsigned int or UUID, not strings)
    # uuid5 is deterministic: same chunk.id always produces the same UUID
    ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.id)) for chunk in chunks]
    
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
    
    # Display collection statistics
    info = qdrant_service.get_collection_info()
    print(f"Collection: {info['name']}")
    if 'error' in info:
        print(f"Warning: Could not get stats - {info['error']}")
    else:
        print(f"Total points: {info['points_count']}")
        print(f"Status: {info['status']}")


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
