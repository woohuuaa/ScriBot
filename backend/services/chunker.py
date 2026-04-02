import re
from pathlib import Path
from dataclasses import dataclass

# ─────────────────────────────────────────────────────────────
# MDX Document Chunker
# ─────────────────────────────────────────────────────────────
#
# Why chunking?
#   - LLM has token limits
#   - Smaller chunks = more precise retrieval
#   - Each chunk should be self-contained
#
# Strategy: Split by headings (## / ###)
#   - Preserves semantic boundaries
#   - Each chunk has a clear topic
# ─────────────────────────────────────────────────────────────


@dataclass
class Chunk:
    """
    A chunk of document content
    """
    id: str           # Unique ID: "filename_chunk0"
    source: str       # Source file: "install.mdx"
    title: str        # Section title: "Installation"
    content: str      # Actual content


class Chunker:
    """
    MDX document chunker for RAG pipeline
    """
    
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 2000):
        """
        Args:
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk_file(self, file_path: Path) -> list[Chunk]:
        """
        Read and chunk a single MDX file
        
        Args:
            file_path: Path to the MDX file
            
        Returns:
            list[Chunk]: List of chunks from this file
        """
        content = file_path.read_text(encoding="utf-8")
        filename = file_path.stem  # "install" from "install.mdx"
        
        # Step 1: Clean the content
        cleaned = self._clean_mdx(content)
        
        # Step 2: Split by headings
        sections = self._split_by_headings(cleaned)
        
        # Step 3: Create chunk
        chunks = []
        for i, (title, text) in enumerate(sections):
            # Skip empty sections
            if len(text.strip()) < self.min_chunk_size:
                continue
            
            # Truncate if too long
            if len(text) > self.max_chunk_size:
                text = text[:self.max_chunk_size] + "..."
            
            chunks.append(Chunk(
                id=f"{filename}_chunk{i}",
                source=file_path.name,
                title=title or filename,  # Use filename if no title
                content=text.strip(),
            ))
        
        return chunks
    
    def chunk_directory(self, dir_path: Path) -> list[Chunk]:
        """
        Chunk all MDX files in a directory
        
        Args:
            dir_path: Path to directory containing MDX files
            
        Returns:
            list[Chunk]: All chunks from all files
        """
        all_chunks = []
        mdx_files = list(dir_path.glob("**/*.mdx")) # Find all .mdx files recursively
        
        print(f"Found {len(mdx_files)} MDX files")
        
        for file_path in mdx_files:                 # Process each file
            chunks = self.chunk_file(file_path)     # Chunk the file
            all_chunks.extend(chunks)               # Add to total list
            print(f"  {file_path.name}: {len(chunks)} chunks")  # Print chunk count per file
        
        print(f"Total: {len(all_chunks)} chunks")   
        return all_chunks
    
    def _clean_mdx(self, content: str) -> str:
        """
        Remove MDX-specific content that doesn't help RAG
        """
        # 1. Remove frontmatter (---...---)
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
        
        # 2. Remove import statements
        content = re.sub(r'^import\s+.*$', '', content, flags=re.MULTILINE)
        
        # 3. Remove Mermaid diagrams (```mermaid...```)
        content = re.sub(r'```mermaid\n.*?```', '', content, flags=re.DOTALL)
        
        # 4. Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # 5. Remove excessive blank lines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def _split_by_headings(self, content: str) -> list[tuple[str, str]]: 
        """
        Split content by ## or ### headings
        
        Returns:
            list[tuple[str, str]]: List of (title, content) tuples
        """
        # Pattern: ## or ### at start of line
        pattern = r'^(#{2,3})\s+(.+)$'
        
        sections = []
        current_title = ""
        current_content = []
        
        for line in content.split('\n'):    # Iterate through lines
            match = re.match(pattern, line) # Check if line is a heading
            if match:
                # If it's a heading, save the previous section (if exists) and start a new one                       # If it's a heading, save the previous section (if exists) and start a new one
                if current_content:
                    sections.append(( 
                        current_title,
                        '\n'.join(current_content)
                    ))
                
                # Start new section
                current_title = match.group(2)
                current_content = []
            else:
                current_content.append(line)
        
        # Don't forget the last section
        if current_content:
            sections.append((
                current_title,
                '\n'.join(current_content)
            ))
        
        return sections


# Singleton instance
chunker = Chunker()