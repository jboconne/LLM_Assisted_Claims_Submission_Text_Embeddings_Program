#!/usr/bin/env python3
"""
Embeddings Generator Module for Claims Data
Generates high-quality embeddings using BGE model for RAG pipeline

Author: LLM Claims Processing Team
Version: 1.0
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Union
from pathlib import Path
import json
import pickle
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
import torch

@dataclass
class EmbeddingResult:
    """Represents an embedding with metadata"""
    chunk_id: str
    embedding: np.ndarray
    source_file: str
    content: str
    metadata: Dict[str, any]
    model_name: str
    embedding_dim: int

class ClaimsEmbeddingsGenerator:
    """Generates embeddings for claims data using BGE model"""
    
    def __init__(self, 
                 model_name: str = "BAAI/bge-large-en-v1.5",
                 device: str = "auto",
                 normalize_embeddings: bool = True):
        """
        Initialize the embeddings generator
        
        Args:
            model_name: Name of the sentence transformer model to use
            device: Device to run the model on ('cpu', 'cuda', 'auto')
            normalize_embeddings: Whether to normalize embeddings to unit length
        """
        self.model_name = model_name
        self.normalize_embeddings = normalize_embeddings
        self.logger = logging.getLogger(__name__)
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        self.logger.info(f"Initializing embeddings generator with model: {model_name}")
        self.logger.info(f"Using device: {self.device}")
        
        # Load the model
        self.model = None
        self.embedding_dim = None
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            self.logger.info("Loading sentence transformer model...")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
            # Get embedding dimension
            test_embedding = self.model.encode(["test"], normalize_embeddings=self.normalize_embeddings)
            self.embedding_dim = test_embedding.shape[1]
            
            self.logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
            
        except Exception as e:
            self.logger.error(f"Failed to load model {self.model_name}: {str(e)}")
            raise
    
    def generate_embedding(self, text: str, chunk_id: str = None, 
                          metadata: Dict = None) -> EmbeddingResult:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            chunk_id: Unique identifier for the chunk
            metadata: Additional metadata
            
        Returns:
            EmbeddingResult object
        """
        try:
            # Generate embedding
            embedding = self.model.encode(
                [text], 
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True
            )[0]
            
            # Create result
            result = EmbeddingResult(
                chunk_id=chunk_id or f"chunk_{hash(text) % 1000000}",
                embedding=embedding,
                source_file=metadata.get('source_file', 'unknown') if metadata else 'unknown',
                content=text,
                metadata=metadata or {},
                model_name=self.model_name,
                embedding_dim=self.embedding_dim
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], 
                                 chunk_ids: List[str] = None,
                                 metadata_list: List[Dict] = None) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            chunk_ids: List of chunk IDs (optional)
            metadata_list: List of metadata dictionaries (optional)
            
        Returns:
            List of EmbeddingResult objects
        """
        try:
            self.logger.info(f"Generating embeddings for {len(texts)} texts...")
            
            # Generate embeddings in batch
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True,
                batch_size=32,  # Process in batches for memory efficiency
                show_progress_bar=True
            )
            
            # Create results
            results = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                chunk_id = chunk_ids[i] if chunk_ids and i < len(chunk_ids) else f"chunk_{i}"
                metadata = metadata_list[i] if metadata_list and i < len(metadata_list) else {}
                
                result = EmbeddingResult(
                    chunk_id=chunk_id,
                    embedding=embedding,
                    source_file=metadata.get('source_file', 'unknown'),
                    content=text,
                    metadata=metadata,
                    model_name=self.model_name,
                    embedding_dim=self.embedding_dim
                )
                results.append(result)
            
            self.logger.info(f"Successfully generated {len(results)} embeddings")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise
    
    def generate_embeddings_from_chunks(self, chunks: List) -> List[EmbeddingResult]:
        """
        Generate embeddings from TextChunk objects
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            List of EmbeddingResult objects
        """
        texts = [chunk.content for chunk in chunks]
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        metadata_list = []
        
        for chunk in chunks:
            metadata = {
                'source_file': chunk.source_file,
                'chunk_index': chunk.chunk_index,
                'start_char': chunk.start_char,
                'end_char': chunk.end_char,
                'chunk_size': len(chunk.content),
                **chunk.metadata
            }
            metadata_list.append(metadata)
        
        return self.generate_embeddings_batch(texts, chunk_ids, metadata_list)
    
    def save_embeddings(self, embeddings: List[EmbeddingResult], 
                       output_path: str, 
                       format: str = "json") -> str:
        """
        Save embeddings to file
        
        Args:
            embeddings: List of EmbeddingResult objects
            output_path: Path to save the embeddings
            format: Format to save in ('json', 'pickle', 'numpy')
            
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if format.lower() == "json":
                # Convert to JSON-serializable format
                data = []
                for emb in embeddings:
                    emb_data = {
                        'chunk_id': emb.chunk_id,
                        'embedding': emb.embedding.tolist(),
                        'source_file': emb.source_file,
                        'content': emb.content,
                        'metadata': emb.metadata,
                        'model_name': emb.model_name,
                        'embedding_dim': emb.embedding_dim
                    }
                    data.append(emb_data)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format.lower() == "pickle":
                with open(output_path, 'wb') as f:
                    pickle.dump(embeddings, f)
            
            elif format.lower() == "numpy":
                # Save as numpy arrays
                embeddings_array = np.array([emb.embedding for emb in embeddings])
                metadata = [asdict(emb) for emb in embeddings]
                
                np.savez(output_path, 
                        embeddings=embeddings_array,
                        metadata=metadata)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Saved {len(embeddings)} embeddings to {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save embeddings: {str(e)}")
            raise
    
    def load_embeddings(self, file_path: str, format: str = "json") -> List[EmbeddingResult]:
        """
        Load embeddings from file
        
        Args:
            file_path: Path to the embeddings file
            format: Format of the file ('json', 'pickle', 'numpy')
            
        Returns:
            List of EmbeddingResult objects
        """
        file_path = Path(file_path)
        
        try:
            if format.lower() == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                embeddings = []
                for item in data:
                    emb = EmbeddingResult(
                        chunk_id=item['chunk_id'],
                        embedding=np.array(item['embedding']),
                        source_file=item['source_file'],
                        content=item['content'],
                        metadata=item['metadata'],
                        model_name=item['model_name'],
                        embedding_dim=item['embedding_dim']
                    )
                    embeddings.append(emb)
            
            elif format.lower() == "pickle":
                with open(file_path, 'rb') as f:
                    embeddings = pickle.load(f)
            
            elif format.lower() == "numpy":
                data = np.load(file_path, allow_pickle=True)
                embeddings = []
                
                for i, (emb_array, metadata) in enumerate(zip(data['embeddings'], data['metadata'])):
                    emb = EmbeddingResult(
                        chunk_id=metadata['chunk_id'],
                        embedding=emb_array,
                        source_file=metadata['source_file'],
                        content=metadata['content'],
                        metadata=metadata['metadata'],
                        model_name=metadata['model_name'],
                        embedding_dim=metadata['embedding_dim']
                    )
                    embeddings.append(emb)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Loaded {len(embeddings)} embeddings from {file_path}")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to load embeddings: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, any]:
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'device': self.device,
            'embedding_dim': self.embedding_dim,
            'normalize_embeddings': self.normalize_embeddings
        }

def main():
    """Test the embeddings generator"""
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize generator
    generator = ClaimsEmbeddingsGenerator()
    
    # Test with sample texts
    sample_texts = [
        "This is a property loss claim for Northside Manufacturing.",
        "Policy number CPP-456789123 effective March 1st 2025.",
        "Loss occurred on April 7th 2025 at 10:45 PM."
    ]
    
    # Generate embeddings
    embeddings = generator.generate_embeddings_batch(sample_texts)
    
    print(f"\nGenerated {len(embeddings)} embeddings:")
    for i, emb in enumerate(embeddings):
        print(f"\nEmbedding {i+1}:")
        print(f"  Chunk ID: {emb.chunk_id}")
        print(f"  Content: {emb.content}")
        print(f"  Embedding shape: {emb.embedding.shape}")
        print(f"  Model: {emb.model_name}")
    
    # Save embeddings
    output_path = Path(__file__).parent.parent / "embeddings" / "test_embeddings.json"
    generator.save_embeddings(embeddings, str(output_path))
    print(f"\nSaved embeddings to: {output_path}")

if __name__ == "__main__":
    main()
