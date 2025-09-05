#!/usr/bin/env python3
"""
Text Chunking Module for Claims Data
Handles intelligent text chunking for optimal embedding generation

Author: LLM Claims Processing Team
Version: 1.0
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    content: str
    chunk_id: str
    source_file: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: Dict[str, any] = None

class ClaimsTextChunker:
    """Intelligent text chunker optimized for insurance claims data"""
    
    def __init__(self, 
                 chunk_size: int = 512,
                 chunk_overlap: int = 50,
                 min_chunk_size: int = 100):
        """
        Initialize the text chunker
        
        Args:
            chunk_size: Target size for each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum size for a valid chunk
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.logger = logging.getLogger(__name__)
        
        # Patterns for identifying natural break points in claims data
        self.section_patterns = [
            r'\n\s*[A-Z][A-Z\s]+:\s*$',  # Section headers like "POLICY INFORMATION:"
            r'\n\s*\d+\.\s+[A-Z]',       # Numbered lists
            r'\n\s*[A-Z][a-z]+\s+[A-Z][a-z]+:',  # Field names like "Policy Number:"
            r'\n\s*---+\s*$',            # Separator lines
            r'\n\s*===+\s*$',            # Major separators
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.MULTILINE) for pattern in self.section_patterns]
    
    def chunk_text(self, text: str, source_file: str, file_metadata: Dict = None) -> List[TextChunk]:
        """
        Chunk text into optimal segments for embedding
        
        Args:
            text: The text to chunk
            source_file: Source file name for metadata
            file_metadata: Additional metadata about the file
            
        Returns:
            List of TextChunk objects
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            self.logger.warning(f"Text too short to chunk: {source_file}")
            return []
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        
        # Find natural break points
        break_points = self._find_break_points(cleaned_text)
        
        # Create chunks
        chunks = self._create_chunks(cleaned_text, break_points, source_file, file_metadata)
        
        self.logger.info(f"Created {len(chunks)} chunks from {source_file}")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better chunking"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        # Remove special characters that might interfere with chunking
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def _find_break_points(self, text: str) -> List[int]:
        """Find natural break points in the text"""
        break_points = set()
        
        # Add pattern-based break points
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                break_points.add(match.start())
        
        # Add sentence boundaries as break points
        sentence_endings = re.finditer(r'[.!?]+\s+', text)
        for match in sentence_endings:
            break_points.add(match.end())
        
        # Add paragraph boundaries
        paragraph_breaks = re.finditer(r'\n\s*\n', text)
        for match in paragraph_breaks:
            break_points.add(match.start())
        
        # Convert to sorted list
        break_points = sorted(list(break_points))
        
        # Add start and end points
        break_points = [0] + break_points + [len(text)]
        
        return break_points
    
    def _create_chunks(self, text: str, break_points: List[int], 
                      source_file: str, file_metadata: Dict) -> List[TextChunk]:
        """Create chunks from text using break points"""
        chunks = []
        chunk_index = 0
        start_pos = 0
        
        while start_pos < len(text):
            # Calculate end position
            end_pos = min(start_pos + self.chunk_size, len(text))
            
            # Try to find a good break point near the end
            best_break = self._find_best_break_point(text, start_pos, end_pos, break_points)
            if best_break > start_pos:
                end_pos = best_break
            
            # Extract chunk content
            chunk_content = text[start_pos:end_pos].strip()
            
            # Skip if chunk is too small
            if len(chunk_content) < self.min_chunk_size:
                start_pos = end_pos
                continue
            
            # Create chunk
            chunk_id = f"{Path(source_file).stem}_chunk_{chunk_index:03d}"
            chunk = TextChunk(
                content=chunk_content,
                chunk_id=chunk_id,
                source_file=source_file,
                chunk_index=chunk_index,
                start_char=start_pos,
                end_char=end_pos,
                metadata={
                    'file_metadata': file_metadata or {},
                    'chunk_size': len(chunk_content),
                    'is_complete_section': self._is_complete_section(chunk_content)
                }
            )
            
            chunks.append(chunk)
            chunk_index += 1
            
            # Move start position with overlap
            start_pos = max(start_pos + 1, end_pos - self.chunk_overlap)
        
        return chunks
    
    def _find_best_break_point(self, text: str, start: int, end: int, 
                              break_points: List[int]) -> int:
        """Find the best break point near the end of the chunk"""
        # Look for break points within the last 20% of the chunk
        search_start = max(start, end - (self.chunk_size // 5))
        
        for bp in reversed(break_points):
            if search_start <= bp <= end:
                return bp
        
        return end
    
    def _is_complete_section(self, chunk_content: str) -> bool:
        """Check if chunk contains a complete section"""
        # Check for common section indicators
        section_indicators = [
            r'^[A-Z][A-Z\s]+:\s*$',  # Section header
            r'^\d+\.\s+[A-Z]',       # Numbered item
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+:',  # Field name
        ]
        
        for pattern in section_indicators:
            if re.search(pattern, chunk_content, re.MULTILINE):
                return True
        
        return False
    
    def chunk_file(self, file_path: str) -> List[TextChunk]:
        """
        Chunk a single file
        
        Args:
            file_path: Path to the file to chunk
            
        Returns:
            List of TextChunk objects
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            file_metadata = {
                'file_path': file_path,
                'file_size': len(text),
                'file_type': Path(file_path).suffix
            }
            
            return self.chunk_text(text, Path(file_path).name, file_metadata)
            
        except Exception as e:
            self.logger.error(f"Error chunking file {file_path}: {str(e)}")
            return []
    
    def chunk_directory(self, directory_path: str, 
                       file_extensions: List[str] = None) -> List[TextChunk]:
        """
        Chunk all text files in a directory
        
        Args:
            directory_path: Path to directory containing files
            file_extensions: List of file extensions to process (default: ['.txt'])
            
        Returns:
            List of TextChunk objects from all files
        """
        if file_extensions is None:
            file_extensions = ['.txt']
        
        directory = Path(directory_path)
        all_chunks = []
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                self.logger.info(f"Chunking file: {file_path}")
                chunks = self.chunk_file(str(file_path))
                all_chunks.extend(chunks)
        
        self.logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks

def main():
    """Test the chunker with sample data"""
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize chunker
    chunker = ClaimsTextChunker(chunk_size=512, chunk_overlap=50)
    
    # Test with source output files
    source_dir = Path(__file__).parent.parent / "source_output_files"
    
    if source_dir.exists():
        chunks = chunker.chunk_directory(str(source_dir))
        
        print(f"\nCreated {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
            print(f"\nChunk {i+1}:")
            print(f"  ID: {chunk.chunk_id}")
            print(f"  Source: {chunk.source_file}")
            print(f"  Size: {len(chunk.content)} chars")
            print(f"  Preview: {chunk.content[:100]}...")
    else:
        print(f"Source directory not found: {source_dir}")

if __name__ == "__main__":
    main()
