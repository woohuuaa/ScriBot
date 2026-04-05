#!/usr/bin/env python3
"""
Test chunker functionality
"""
from pathlib import Path    # For file paths
import sys                  # To modify sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent)) # Add parent directory to path for imports
from services.chunker import chunker # Import the chunker instance
# Docs path - in Docker container, Docs is mounted at /app/Docs
# Docs path inside the Docker container. Docs is mounted at /app/Docs.
DOCS_PATH = Path("/app/Docs/src/content/docs")
def test_single_file():
    """Test chunking a single file"""
    print("=" * 60)
    print("Testing single file chunking")
    print("=" * 60)
    
    # Pick one file
    test_file = DOCS_PATH / "index.mdx"
    
    # Check if file exists
    if not test_file.exists():
        print(f"Error: {test_file} not found")
        return
    
    # Chunk the file
    chunks = chunker.chunk_file(test_file)
    
    print(f"\nFile: {test_file.name}")
    print(f"Chunks generated: {len(chunks)}\n")
    
    # Print details of each chunk
    for c in chunks:
        print(f"  [{c.id}]")
        print(f"    Title: {c.title[:50]}...")
        print(f"    Content: {c.content[:100]}...")
        print(f"    Length: {len(c.content)} chars")
        print()

        # For testing, we can also print the full content of the first chunk
        # if c.id == "index_chunk0":
        #     print(f"Full content of {c.id}:\n{c.content}\n")

# Test chunking entire directory
def test_directory():
    """Test chunking entire directory"""
    print("=" * 60)
    print("Testing directory chunking")
    print("=" * 60)

    # Chunk the entire directory
    chunks = chunker.chunk_directory(DOCS_PATH)
    
    print(f"\nTotal chunks: {len(chunks)}")
    
# Run tests
if __name__ == "__main__":
    test_single_file()
    print("\n")
    test_directory()
