#!/usr/bin/env python3
"""
Local Vector Database Implementation using FAISS
Provides local vector storage without requiring external API keys

Author: LLM Claims Processing Team
Version: 1.0
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Union, Any
from pathlib import Path
import pickle
import json
from dataclasses import dataclass
import os

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

@dataclass
class SearchResult:
    """Represents a search result from local vector database"""
    chunk_id: str
    content: str
    source_file: str
    score: float
    metadata: Dict[str, Any]

class LocalVectorDB:
    """Local vector database using FAISS for similarity search"""
    
    def __init__(self, index_path: str = "local_vector_index"):
        """
        Initialize local vector database
        
        Args:
            index_path: Path to store the FAISS index and metadata
        """
        self.logger = logging.getLogger(__name__)
        self.index_path = Path(index_path)
        self.index_path.mkdir(exist_ok=True)
        
        if not FAISS_AVAILABLE:
            raise ImportError("faiss-cpu package is required. Install with: pip install faiss-cpu")
        
        self.index = None
        self.metadata = {}
        self.dimension = None
        self.is_trained = False
        
        # Try to load existing index
        self._load_index()
        
        self.logger.info("Local vector database initialized")
    
    def create_index(self, index_name: str = None, dimension: int = None, **kwargs) -> bool:
        """
        Create a new FAISS index
        
        Args:
            index_name: Index name (ignored for local DB)
            dimension: Embedding dimension
            **kwargs: Additional parameters (ignored for local DB)
            
        Returns:
            True if successful
        """
        try:
            self.dimension = dimension
            
            # Create FAISS index (IndexFlatIP for inner product, IndexFlatL2 for L2 distance)
            # Using IndexFlatIP with normalized vectors gives cosine similarity
            self.index = faiss.IndexFlatIP(dimension)
            self.is_trained = True
            
            self.logger.info(f"Created local FAISS index with dimension {dimension}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create local index: {str(e)}")
            return False
    
    def delete_index(self, index_name: str = None) -> bool:
        """
        Delete the local index
        
        Args:
            index_name: Index name (ignored for local DB)
            
        Returns:
            True if successful
        """
        try:
            # Remove index files
            index_file = self.index_path / "faiss_index.bin"
            metadata_file = self.index_path / "metadata.pkl"
            
            if index_file.exists():
                index_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            
            self.index = None
            self.metadata = {}
            self.is_trained = False
            
            self.logger.info("Local index deleted")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete local index: {str(e)}")
            return False
    
    def upsert_embeddings(self, embeddings: List, index_name: str = None) -> bool:
        """
        Insert or update embeddings in the local index
        
        Args:
            embeddings: List of EmbeddingResult objects
            index_name: Index name (ignored for local DB)
            
        Returns:
            True if successful
        """
        try:
            if not self.is_trained:
                if not embeddings:
                    return False
                self.create_index(dimension=embeddings[0].embedding_dim)
            
            # Prepare vectors and metadata
            vectors = []
            for emb in embeddings:
                vectors.append(emb.embedding.astype('float32'))
                
                # Store metadata
                self.metadata[emb.chunk_id] = {
                    'source_file': emb.source_file,
                    'content': emb.content,
                    'model_name': emb.model_name,
                    'embedding_dim': emb.embedding_dim,
                    **emb.metadata
                }
            
            # Convert to numpy array
            vectors_array = np.vstack(vectors).astype('float32')
            
            # Add vectors to index
            self.index.add(vectors_array)
            
            # Save index and metadata
            self._save_index()
            
            self.logger.info(f"Upserted {len(embeddings)} embeddings to local index")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upsert embeddings to local index: {str(e)}")
            return False
    
    def search(self, query_embedding: np.ndarray, index_name: str = None, 
              top_k: int = 10, **kwargs) -> List[SearchResult]:
        """
        Search for similar embeddings in the local index
        
        Args:
            query_embedding: Query vector
            index_name: Index name (ignored for local DB)
            top_k: Number of results to return
            **kwargs: Additional search parameters
            
        Returns:
            List of SearchResult objects
        """
        try:
            if not self.is_trained or self.index is None:
                self.logger.warning("Index not trained or empty")
                return []
            
            # Ensure query is normalized for cosine similarity
            query_vector = query_embedding.astype('float32').reshape(1, -1)
            
            # Search
            scores, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
            
            # Convert to SearchResult objects
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:  # No more results
                    break
                
                # Get chunk ID from index position
                chunk_ids = list(self.metadata.keys())
                if idx < len(chunk_ids):
                    chunk_id = chunk_ids[idx]
                    metadata = self.metadata[chunk_id]
                    
                    result = SearchResult(
                        chunk_id=chunk_id,
                        content=metadata.get('content', ''),
                        source_file=metadata.get('source_file', ''),
                        score=float(score),
                        metadata=metadata
                    )
                    results.append(result)
            
            self.logger.info(f"Found {len(results)} results for query")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search local index: {str(e)}")
            return []
    
    def get_stats(self, index_name: str = None) -> Dict[str, Any]:
        """
        Get local index statistics
        
        Args:
            index_name: Index name (ignored for local DB)
            
        Returns:
            Dictionary with index statistics
        """
        try:
            if not self.is_trained or self.index is None:
                return {'total_vectors': 0, 'dimension': 0}
            
            return {
                'total_vectors': self.index.ntotal,
                'dimension': self.dimension,
                'is_trained': self.is_trained,
                'index_type': 'faiss_local',
                'metadata_entries': len(self.metadata)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get local index stats: {str(e)}")
            return {}
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            if self.index is not None:
                # Save FAISS index
                index_file = self.index_path / "faiss_index.bin"
                faiss.write_index(self.index, str(index_file))
                
                # Save metadata
                metadata_file = self.index_path / "metadata.pkl"
                with open(metadata_file, 'wb') as f:
                    pickle.dump(self.metadata, f)
                
                self.logger.info(f"Saved index to {self.index_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to save local index: {str(e)}")
    
    def _load_index(self):
        """Load existing FAISS index and metadata from disk"""
        try:
            index_file = self.index_path / "faiss_index.bin"
            metadata_file = self.index_path / "metadata.pkl"
            
            if index_file.exists() and metadata_file.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(index_file))
                
                # Load metadata
                with open(metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                
                self.dimension = self.index.d
                self.is_trained = True
                
                self.logger.info(f"Loaded existing index with {self.index.ntotal} vectors")
                
        except Exception as e:
            self.logger.info(f"No existing index found or failed to load: {str(e)}")

def main():
    """Test the local vector database"""
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Local Vector Database Test")
    print("=" * 40)
    
    if not FAISS_AVAILABLE:
        print("❌ faiss-cpu package not installed")
        print("Install with: pip install faiss-cpu")
        return
    
    try:
        # Initialize database
        db = LocalVectorDB("test_index")
        
        # Create test index
        success = db.create_index(dimension=1024)
        print(f"Index created: {success}")
        
        # Get stats
        stats = db.get_stats()
        print(f"Index stats: {stats}")
        
        print("✅ Local vector database test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    main()
