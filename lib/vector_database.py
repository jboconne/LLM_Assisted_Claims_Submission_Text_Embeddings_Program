#!/usr/bin/env python3
"""
Vector Database Integration Module
Supports both Pinecone and Weaviate for storing and querying embeddings

Author: LLM Claims Processing Team
Version: 1.0
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Union, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
import os
from pathlib import Path

@dataclass
class SearchResult:
    """Represents a search result from vector database"""
    chunk_id: str
    content: str
    source_file: str
    score: float
    metadata: Dict[str, Any]

class VectorDatabaseInterface(ABC):
    """Abstract interface for vector database operations"""
    
    @abstractmethod
    def create_index(self, index_name: str, dimension: int, **kwargs) -> bool:
        """Create a new index"""
        pass
    
    @abstractmethod
    def delete_index(self, index_name: str) -> bool:
        """Delete an index"""
        pass
    
    @abstractmethod
    def upsert_embeddings(self, embeddings: List, index_name: str) -> bool:
        """Insert or update embeddings"""
        pass
    
    @abstractmethod
    def search(self, query_embedding: np.ndarray, index_name: str, 
              top_k: int = 10, **kwargs) -> List[SearchResult]:
        """Search for similar embeddings"""
        pass
    
    @abstractmethod
    def get_stats(self, index_name: str) -> Dict[str, Any]:
        """Get index statistics"""
        pass

class PineconeVectorDB(VectorDatabaseInterface):
    """Pinecone vector database implementation"""
    
    def __init__(self, api_key: str = None, environment: str = None):
        """
        Initialize Pinecone client
        
        Args:
            api_key: Pinecone API key (if None, will try to get from environment)
            environment: Pinecone environment (if None, will try to get from environment)
        """
        self.logger = logging.getLogger(__name__)
        
        # Get credentials from environment if not provided
        self.api_key = api_key or os.getenv('PINECONE_API_KEY')
        self.environment = environment or os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp')
        
        if not self.api_key:
            raise ValueError("Pinecone API key is required. Set PINECONE_API_KEY environment variable.")
        
        try:
            import pinecone
            pinecone.init(api_key=self.api_key, environment=self.environment)
            self.client = pinecone
            self.logger.info("Pinecone client initialized successfully")
        except ImportError:
            raise ImportError("pinecone-client package is required. Install with: pip install pinecone-client")
        except Exception as e:
            self.logger.error(f"Failed to initialize Pinecone client: {str(e)}")
            raise
    
    def create_index(self, index_name: str, dimension: int, **kwargs) -> bool:
        """Create a new Pinecone index"""
        try:
            # Default metric is cosine similarity
            metric = kwargs.get('metric', 'cosine')
            
            # Check if index already exists
            if index_name in self.client.list_indexes().names():
                self.logger.info(f"Index {index_name} already exists")
                return True
            
            # Create index
            self.client.create_index(
                name=index_name,
                dimension=dimension,
                metric=metric
            )
            
            self.logger.info(f"Created Pinecone index: {index_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Pinecone index: {str(e)}")
            return False
    
    def delete_index(self, index_name: str) -> bool:
        """Delete a Pinecone index"""
        try:
            self.client.delete_index(index_name)
            self.logger.info(f"Deleted Pinecone index: {index_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete Pinecone index: {str(e)}")
            return False
    
    def upsert_embeddings(self, embeddings: List, index_name: str) -> bool:
        """Insert or update embeddings in Pinecone"""
        try:
            index = self.client.Index(index_name)
            
            # Prepare vectors for upsert
            vectors = []
            for emb in embeddings:
                vector_data = {
                    'id': emb.chunk_id,
                    'values': emb.embedding.tolist(),
                    'metadata': {
                        'source_file': emb.source_file,
                        'content': emb.content,
                        'model_name': emb.model_name,
                        'embedding_dim': emb.embedding_dim,
                        **emb.metadata
                    }
                }
                vectors.append(vector_data)
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                index.upsert(vectors=batch)
            
            self.logger.info(f"Upserted {len(embeddings)} embeddings to {index_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upsert embeddings to Pinecone: {str(e)}")
            return False
    
    def search(self, query_embedding: np.ndarray, index_name: str, 
              top_k: int = 10, **kwargs) -> List[SearchResult]:
        """Search for similar embeddings in Pinecone"""
        try:
            index = self.client.Index(index_name)
            
            # Perform search
            results = index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True
            )
            
            # Convert to SearchResult objects
            search_results = []
            for match in results['matches']:
                result = SearchResult(
                    chunk_id=match['id'],
                    content=match['metadata'].get('content', ''),
                    source_file=match['metadata'].get('source_file', ''),
                    score=float(match['score']),
                    metadata=match['metadata']
                )
                search_results.append(result)
            
            self.logger.info(f"Found {len(search_results)} results for query")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Failed to search Pinecone: {str(e)}")
            return []
    
    def get_stats(self, index_name: str) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        try:
            index = self.client.Index(index_name)
            stats = index.describe_index_stats()
            return dict(stats)
        except Exception as e:
            self.logger.error(f"Failed to get Pinecone stats: {str(e)}")
            return {}

class WeaviateVectorDB(VectorDatabaseInterface):
    """Weaviate vector database implementation"""
    
    def __init__(self, url: str = None, api_key: str = None):
        """
        Initialize Weaviate client
        
        Args:
            url: Weaviate server URL (if None, will try to get from environment)
            api_key: Weaviate API key (if None, will try to get from environment)
        """
        self.logger = logging.getLogger(__name__)
        
        # Get credentials from environment if not provided
        self.url = url or os.getenv('WEAVIATE_URL', 'http://localhost:8080')
        self.api_key = api_key or os.getenv('WEAVIATE_API_KEY')
        
        try:
            import weaviate
            auth_config = weaviate.AuthApiKey(api_key=self.api_key) if self.api_key else None
            self.client = weaviate.Client(
                url=self.url,
                auth_client_secret=auth_config
            )
            self.logger.info("Weaviate client initialized successfully")
        except ImportError:
            raise ImportError("weaviate-client package is required. Install with: pip install weaviate-client")
        except Exception as e:
            self.logger.error(f"Failed to initialize Weaviate client: {str(e)}")
            raise
    
    def create_index(self, index_name: str, dimension: int, **kwargs) -> bool:
        """Create a new Weaviate class (index)"""
        try:
            class_name = index_name.replace('-', '_').title()
            
            # Check if class already exists
            if self.client.schema.exists(class_name):
                self.logger.info(f"Class {class_name} already exists")
                return True
            
            # Define class schema
            class_schema = {
                "class": class_name,
                "description": f"Claims data embeddings for {index_name}",
                "vectorizer": "none",  # We provide our own vectors
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The text content of the chunk"
                    },
                    {
                        "name": "source_file",
                        "dataType": ["string"],
                        "description": "Source file name"
                    },
                    {
                        "name": "chunk_id",
                        "dataType": ["string"],
                        "description": "Unique chunk identifier"
                    },
                    {
                        "name": "model_name",
                        "dataType": ["string"],
                        "description": "Embedding model used"
                    },
                    {
                        "name": "metadata",
                        "dataType": ["object"],
                        "description": "Additional metadata"
                    }
                ]
            }
            
            # Create class
            self.client.schema.create_class(class_schema)
            self.logger.info(f"Created Weaviate class: {class_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create Weaviate class: {str(e)}")
            return False
    
    def delete_index(self, index_name: str) -> bool:
        """Delete a Weaviate class"""
        try:
            class_name = index_name.replace('-', '_').title()
            self.client.schema.delete_class(class_name)
            self.logger.info(f"Deleted Weaviate class: {class_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete Weaviate class: {str(e)}")
            return False
    
    def upsert_embeddings(self, embeddings: List, index_name: str) -> bool:
        """Insert or update embeddings in Weaviate"""
        try:
            class_name = index_name.replace('-', '_').title()
            
            # Prepare data for batch insert
            with self.client.batch as batch:
                batch.batch_size = 100
                for emb in embeddings:
                    data_object = {
                        "content": emb.content,
                        "source_file": emb.source_file,
                        "chunk_id": emb.chunk_id,
                        "model_name": emb.model_name,
                        "metadata": emb.metadata
                    }
                    
                    batch.add_data_object(
                        data_object=data_object,
                        class_name=class_name,
                        vector=emb.embedding.tolist()
                    )
            
            self.logger.info(f"Upserted {len(embeddings)} embeddings to {class_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upsert embeddings to Weaviate: {str(e)}")
            return False
    
    def search(self, query_embedding: np.ndarray, index_name: str, 
              top_k: int = 10, **kwargs) -> List[SearchResult]:
        """Search for similar embeddings in Weaviate"""
        try:
            class_name = index_name.replace('-', '_').title()
            
            # Perform search
            result = self.client.query.get(
                class_name=class_name,
                properties=["content", "source_file", "chunk_id", "metadata"]
            ).with_near_vector({
                "vector": query_embedding.tolist()
            }).with_limit(top_k).do()
            
            # Convert to SearchResult objects
            search_results = []
            for item in result['data']['Get'][class_name]:
                result_obj = SearchResult(
                    chunk_id=item['chunk_id'],
                    content=item['content'],
                    source_file=item['source_file'],
                    score=item.get('_additional', {}).get('distance', 0.0),
                    metadata=item.get('metadata', {})
                )
                search_results.append(result_obj)
            
            self.logger.info(f"Found {len(search_results)} results for query")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Failed to search Weaviate: {str(e)}")
            return []
    
    def get_stats(self, index_name: str) -> Dict[str, Any]:
        """Get Weaviate class statistics"""
        try:
            class_name = index_name.replace('-', '_').title()
            result = self.client.query.aggregate(class_name).with_meta_count().do()
            return result
        except Exception as e:
            self.logger.error(f"Failed to get Weaviate stats: {str(e)}")
            return {}

class VectorDatabaseManager:
    """Manager class for vector database operations"""
    
    def __init__(self, db_type: str = "pinecone", **kwargs):
        """
        Initialize vector database manager
        
        Args:
            db_type: Type of database ('pinecone', 'weaviate', or 'local')
            **kwargs: Additional arguments for database initialization
        """
        self.logger = logging.getLogger(__name__)
        self.db_type = db_type.lower()
        
        if self.db_type == "pinecone":
            self.db = PineconeVectorDB(**kwargs)
        elif self.db_type == "weaviate":
            self.db = WeaviateVectorDB(**kwargs)
        elif self.db_type == "local":
            from .local_vector_db import LocalVectorDB
            self.db = LocalVectorDB(**kwargs)
        else:
            raise ValueError(f"Unsupported database type: {db_type}. Supported: pinecone, weaviate, local")
        
        self.logger.info(f"Initialized {self.db_type} vector database manager")
    
    def create_index(self, index_name: str, dimension: int, **kwargs) -> bool:
        """Create a new index"""
        return self.db.create_index(index_name, dimension, **kwargs)
    
    def delete_index(self, index_name: str) -> bool:
        """Delete an index"""
        return self.db.delete_index(index_name)
    
    def upsert_embeddings(self, embeddings: List, index_name: str) -> bool:
        """Insert or update embeddings"""
        return self.db.upsert_embeddings(embeddings, index_name)
    
    def search(self, query_embedding: np.ndarray, index_name: str, 
              top_k: int = 10, **kwargs) -> List[SearchResult]:
        """Search for similar embeddings"""
        return self.db.search(query_embedding, index_name, top_k, **kwargs)
    
    def get_stats(self, index_name: str) -> Dict[str, Any]:
        """Get index statistics"""
        return self.db.get_stats(index_name)

def main():
    """Test the vector database integration"""
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with mock data
    print("Vector Database Integration Test")
    print("=" * 40)
    
    # Note: This is a test without actual database connection
    print("This module provides integration with Pinecone and Weaviate.")
    print("To use:")
    print("1. Set environment variables for your chosen database")
    print("2. Install the required client library")
    print("3. Initialize VectorDatabaseManager with your credentials")
    
    # Example usage (commented out as it requires actual credentials)
    """
    # For Pinecone
    manager = VectorDatabaseManager(
        db_type="pinecone",
        api_key="your-api-key",
        environment="your-environment"
    )
    
    # For Weaviate
    manager = VectorDatabaseManager(
        db_type="weaviate",
        url="http://localhost:8080"
    )
    """

if __name__ == "__main__":
    main()
