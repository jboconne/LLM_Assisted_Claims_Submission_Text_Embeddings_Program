#!/usr/bin/env python3
"""
Search API Module for Claims Data
Provides vector similarity search and keyword search capabilities

Author: LLM Claims Processing Team
Version: 1.0
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
import re
import json
from pathlib import Path
from datetime import datetime

from .embeddings_generator import ClaimsEmbeddingsGenerator, EmbeddingResult
from .vector_database import VectorDatabaseManager, SearchResult

@dataclass
class SearchQuery:
    """Represents a search query with parameters"""
    query_text: str
    search_type: str  # 'vector', 'keyword', 'hybrid'
    top_k: int = 10
    min_score: float = 0.0
    filters: Dict[str, Any] = None

@dataclass
class SearchResponse:
    """Represents a search response"""
    query: SearchQuery
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    search_type: str
    metadata: Dict[str, Any] = None

class ClaimsSearchAPI:
    """Search API for claims data with vector and keyword search"""
    
    def __init__(self, 
                 embeddings_generator: ClaimsEmbeddingsGenerator,
                 vector_db: VectorDatabaseManager,
                 index_name: str = "claims-embeddings"):
        """
        Initialize the search API
        
        Args:
            embeddings_generator: Instance of ClaimsEmbeddingsGenerator
            vector_db: Instance of VectorDatabaseManager
            index_name: Name of the vector database index
        """
        self.embeddings_generator = embeddings_generator
        self.vector_db = vector_db
        self.index_name = index_name
        self.logger = logging.getLogger(__name__)
        
        # Initialize keyword search index
        self.keyword_index = {}
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Build keyword search index from existing data"""
        try:
            # This would typically load from a persistent keyword index
            # For now, we'll build it dynamically during search
            self.logger.info("Keyword index will be built dynamically during search")
        except Exception as e:
            self.logger.error(f"Failed to build keyword index: {str(e)}")
    
    def search(self, query: SearchQuery) -> SearchResponse:
        """
        Perform search based on query type
        
        Args:
            query: SearchQuery object with search parameters
            
        Returns:
            SearchResponse object with results
        """
        start_time = datetime.now()
        
        try:
            if query.search_type == "vector":
                results = self._vector_search(query)
            elif query.search_type == "keyword":
                results = self._keyword_search(query)
            elif query.search_type == "hybrid":
                results = self._hybrid_search(query)
            else:
                raise ValueError(f"Unsupported search type: {query.search_type}")
            
            # Filter results by minimum score
            filtered_results = [r for r in results if r.score >= query.min_score]
            
            # Apply additional filters if provided
            if query.filters:
                filtered_results = self._apply_filters(filtered_results, query.filters)
            
            # Limit results
            final_results = filtered_results[:query.top_k]
            
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            
            response = SearchResponse(
                query=query,
                results=final_results,
                total_results=len(final_results),
                search_time_ms=search_time,
                search_type=query.search_type,
                metadata={
                    'index_name': self.index_name,
                    'model_name': self.embeddings_generator.model_name,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            self.logger.info(f"Search completed: {len(final_results)} results in {search_time:.2f}ms")
            return response
            
        except Exception as e:
            self.logger.error(f"Search failed: {str(e)}")
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_time_ms=0.0,
                search_type=query.search_type,
                metadata={'error': str(e)}
            )
    
    def _vector_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform vector similarity search"""
        try:
            # Generate embedding for query
            query_embedding = self.embeddings_generator.generate_embedding(
                query.query_text,
                chunk_id="query",
                metadata={'query': True}
            )
            
            # Search in vector database
            results = self.vector_db.search(
                query_embedding.embedding,
                self.index_name,
                top_k=query.top_k
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Vector search failed: {str(e)}")
            return []
    
    def _keyword_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform keyword-based search"""
        try:
            # This is a simplified keyword search implementation
            # In a production system, you'd use a proper search engine like Elasticsearch
            
            # Get all documents from vector database (this is not efficient for large datasets)
            # In practice, you'd maintain a separate keyword index
            
            # For now, we'll simulate keyword search by searching through metadata
            # This is a placeholder implementation
            
            results = []
            query_terms = self._extract_keywords(query.query_text)
            
            # This would typically search through a keyword index
            # For demonstration, we'll return empty results
            self.logger.warning("Keyword search is not fully implemented - requires keyword index")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Keyword search failed: {str(e)}")
            return []
    
    def _hybrid_search(self, query: SearchQuery) -> List[SearchResult]:
        """Perform hybrid search combining vector and keyword search"""
        try:
            # Get vector search results
            vector_results = self._vector_search(query)
            
            # Get keyword search results
            keyword_results = self._keyword_search(query)
            
            # Combine and rank results
            combined_results = self._combine_search_results(vector_results, keyword_results)
            
            return combined_results
            
        except Exception as e:
            self.logger.error(f"Hybrid search failed: {str(e)}")
            return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from search text"""
        # Simple keyword extraction
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def _combine_search_results(self, vector_results: List[SearchResult], 
                               keyword_results: List[SearchResult]) -> List[SearchResult]:
        """Combine and rank results from different search methods"""
        # Create a combined score for each result
        combined_results = {}
        
        # Add vector results with weight
        for result in vector_results:
            chunk_id = result.chunk_id
            combined_results[chunk_id] = {
                'result': result,
                'vector_score': result.score,
                'keyword_score': 0.0,
                'combined_score': result.score * 0.7  # 70% weight for vector search
            }
        
        # Add keyword results with weight
        for result in keyword_results:
            chunk_id = result.chunk_id
            if chunk_id in combined_results:
                combined_results[chunk_id]['keyword_score'] = result.score
                combined_results[chunk_id]['combined_score'] += result.score * 0.3  # 30% weight for keyword search
            else:
                combined_results[chunk_id] = {
                    'result': result,
                    'vector_score': 0.0,
                    'keyword_score': result.score,
                    'combined_score': result.score * 0.3
                }
        
        # Sort by combined score
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        # Update scores in results
        final_results = []
        for item in sorted_results:
            result = item['result']
            result.score = item['combined_score']
            final_results.append(result)
        
        return final_results
    
    def _apply_filters(self, results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]:
        """Apply filters to search results"""
        filtered_results = []
        
        for result in results:
            include = True
            
            for filter_key, filter_value in filters.items():
                if filter_key in result.metadata:
                    if isinstance(filter_value, list):
                        if result.metadata[filter_key] not in filter_value:
                            include = False
                            break
                    else:
                        if result.metadata[filter_key] != filter_value:
                            include = False
                            break
            
            if include:
                filtered_results.append(result)
        
        return filtered_results
    
    def search_by_text(self, query_text: str, search_type: str = "vector", 
                      top_k: int = 10, **kwargs) -> SearchResponse:
        """
        Convenience method for text-based search
        
        Args:
            query_text: Text to search for
            search_type: Type of search ('vector', 'keyword', 'hybrid')
            top_k: Number of results to return
            **kwargs: Additional search parameters
            
        Returns:
            SearchResponse object
        """
        query = SearchQuery(
            query_text=query_text,
            search_type=search_type,
            top_k=top_k,
            **kwargs
        )
        
        return self.search(query)
    
    def get_similar_documents(self, document_id: str, top_k: int = 5) -> SearchResponse:
        """
        Find documents similar to a specific document
        
        Args:
            document_id: ID of the document to find similar ones for
            top_k: Number of similar documents to return
            
        Returns:
            SearchResponse object
        """
        # This would require storing document embeddings and finding similar ones
        # For now, return empty results
        self.logger.warning("Similar documents search not implemented")
        
        query = SearchQuery(
            query_text=f"Find documents similar to {document_id}",
            search_type="vector",
            top_k=top_k
        )
        
        return SearchResponse(
            query=query,
            results=[],
            total_results=0,
            search_time_ms=0.0,
            search_type="similar",
            metadata={'error': 'Similar documents search not implemented'}
        )
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the search index"""
        try:
            stats = self.vector_db.get_stats(self.index_name)
            return {
                'index_name': self.index_name,
                'vector_db_stats': stats,
                'model_info': self.embeddings_generator.get_model_info()
            }
        except Exception as e:
            self.logger.error(f"Failed to get index stats: {str(e)}")
            return {'error': str(e)}

def main():
    """Test the search API"""
    import sys
    from pathlib import Path
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    print("Claims Search API Test")
    print("=" * 30)
    
    # This is a test without actual database connection
    print("This module provides search capabilities for claims data.")
    print("To use:")
    print("1. Initialize ClaimsEmbeddingsGenerator")
    print("2. Initialize VectorDatabaseManager")
    print("3. Create ClaimsSearchAPI instance")
    print("4. Use search methods to query the data")
    
    # Example usage (commented out as it requires actual setup)
    """
    # Initialize components
    embeddings_gen = ClaimsEmbeddingsGenerator()
    vector_db = VectorDatabaseManager(db_type="pinecone")
    search_api = ClaimsSearchAPI(embeddings_gen, vector_db)
    
    # Perform search
    query = SearchQuery(
        query_text="property loss claim",
        search_type="vector",
        top_k=5
    )
    
    results = search_api.search(query)
    print(f"Found {results.total_results} results")
    """

if __name__ == "__main__":
    main()
