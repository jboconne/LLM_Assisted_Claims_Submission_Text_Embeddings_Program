#!/usr/bin/env python3
"""
Embeddings Pipeline for Claims Data
Main script that orchestrates the complete embeddings workflow

Author: LLM Claims Processing Team
Version: 1.0
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import our custom modules
from lib.text_chunker import ClaimsTextChunker, TextChunk
from lib.embeddings_generator import ClaimsEmbeddingsGenerator, EmbeddingResult
from lib.vector_database import VectorDatabaseManager
from lib.search_api import ClaimsSearchAPI

class ClaimsEmbeddingsPipeline:
    """Main pipeline for processing claims data into embeddings"""
    
    def __init__(self, 
                 source_dir: str = None,
                 output_dir: str = None,
                 vector_db_type: str = "pinecone",
                 index_name: str = "claims-embeddings",
                 chunk_size: int = 512,
                 chunk_overlap: int = 50):
        """
        Initialize the embeddings pipeline
        
        Args:
            source_dir: Directory containing source text files
            output_dir: Directory to save processed data
            vector_db_type: Type of vector database ('pinecone' or 'weaviate')
            index_name: Name of the vector database index
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up directories
        self.source_dir = Path(source_dir) if source_dir else PROJECT_ROOT / "source_output_files"
        self.output_dir = Path(output_dir) if output_dir else PROJECT_ROOT / "embeddings_output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.chunker = ClaimsTextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embeddings_generator = ClaimsEmbeddingsGenerator()
        self.vector_db = VectorDatabaseManager(db_type=vector_db_type)
        self.search_api = ClaimsSearchAPI(
            embeddings_generator=self.embeddings_generator,
            vector_db=self.vector_db,
            index_name=index_name
        )
        
        self.index_name = index_name
        self.logger.info(f"Embeddings pipeline initialized with source: {self.source_dir}")
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete embeddings pipeline
        
        Returns:
            Dictionary with pipeline results and statistics
        """
        self.logger.info("=" * 80)
        self.logger.info("🚀 STARTING CLAIMS EMBEDDINGS PIPELINE")
        self.logger.info("=" * 80)
        
        results = {
            'start_time': datetime.now().isoformat(),
            'source_dir': str(self.source_dir),
            'output_dir': str(self.output_dir),
            'index_name': self.index_name,
            'steps_completed': [],
            'errors': [],
            'statistics': {}
        }
        
        try:
            # Step 1: Chunk text files
            self.logger.info("📄 Step 1: Chunking text files...")
            chunks = self._chunk_files()
            results['steps_completed'].append('chunking')
            results['statistics']['chunks_created'] = len(chunks)
            self.logger.info(f"✅ Created {len(chunks)} chunks")
            
            # Step 2: Generate embeddings
            self.logger.info("🧠 Step 2: Generating embeddings...")
            embeddings = self._generate_embeddings(chunks)
            results['steps_completed'].append('embeddings_generation')
            results['statistics']['embeddings_generated'] = len(embeddings)
            self.logger.info(f"✅ Generated {len(embeddings)} embeddings")
            
            # Step 3: Create vector database index
            self.logger.info("🗄️ Step 3: Setting up vector database...")
            self._setup_vector_database(embeddings)
            results['steps_completed'].append('vector_database_setup')
            self.logger.info("✅ Vector database setup complete")
            
            # Step 4: Store embeddings
            self.logger.info("💾 Step 4: Storing embeddings...")
            self._store_embeddings(embeddings)
            results['steps_completed'].append('embeddings_storage')
            self.logger.info("✅ Embeddings stored successfully")
            
            # Step 5: Save metadata
            self.logger.info("📋 Step 5: Saving metadata...")
            self._save_metadata(chunks, embeddings, results)
            results['steps_completed'].append('metadata_save')
            self.logger.info("✅ Metadata saved")
            
            results['end_time'] = datetime.now().isoformat()
            results['status'] = 'success'
            
            self.logger.info("=" * 80)
            self.logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            self.logger.info("=" * 80)
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
            results['status'] = 'failed'
            results['end_time'] = datetime.now().isoformat()
        
        return results
    
    def _chunk_files(self) -> List[TextChunk]:
        """Chunk all text files in the source directory"""
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")
        
        # Get all text files
        text_files = list(self.source_dir.rglob("*.txt"))
        
        if not text_files:
            raise ValueError(f"No text files found in {self.source_dir}")
        
        self.logger.info(f"Found {len(text_files)} text files to process")
        
        all_chunks = []
        for file_path in text_files:
            self.logger.info(f"Processing: {file_path.name}")
            chunks = self.chunker.chunk_file(str(file_path))
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def _generate_embeddings(self, chunks: List[TextChunk]) -> List[EmbeddingResult]:
        """Generate embeddings for all chunks"""
        if not chunks:
            raise ValueError("No chunks to process")
        
        # Generate embeddings in batches
        embeddings = self.embeddings_generator.generate_embeddings_from_chunks(chunks)
        
        # Save embeddings to file for backup
        embeddings_file = self.output_dir / "embeddings.json"
        self.embeddings_generator.save_embeddings(embeddings, str(embeddings_file))
        
        return embeddings
    
    def _setup_vector_database(self, embeddings: List[EmbeddingResult]):
        """Set up vector database index"""
        if not embeddings:
            raise ValueError("No embeddings to store")
        
        # Get embedding dimension
        embedding_dim = embeddings[0].embedding_dim
        
        # Create index
        success = self.vector_db.create_index(
            index_name=self.index_name,
            dimension=embedding_dim,
            metric='cosine'
        )
        
        if not success:
            raise RuntimeError(f"Failed to create vector database index: {self.index_name}")
    
    def _store_embeddings(self, embeddings: List[EmbeddingResult]):
        """Store embeddings in vector database"""
        if not embeddings:
            raise ValueError("No embeddings to store")
        
        success = self.vector_db.upsert_embeddings(embeddings, self.index_name)
        
        if not success:
            raise RuntimeError("Failed to store embeddings in vector database")
    
    def _save_metadata(self, chunks: List[TextChunk], embeddings: List[EmbeddingResult], results: Dict):
        """Save pipeline metadata and statistics"""
        metadata = {
            'pipeline_info': {
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'source_directory': str(self.source_dir),
                'output_directory': str(self.output_dir),
                'index_name': self.index_name
            },
            'statistics': {
                'total_chunks': len(chunks),
                'total_embeddings': len(embeddings),
                'embedding_dimension': embeddings[0].embedding_dim if embeddings else 0,
                'model_name': self.embeddings_generator.model_name,
                'chunk_size': self.chunker.chunk_size,
                'chunk_overlap': self.chunker.chunk_overlap
            },
            'chunks_summary': [
                {
                    'chunk_id': chunk.chunk_id,
                    'source_file': chunk.source_file,
                    'chunk_size': len(chunk.content),
                    'start_char': chunk.start_char,
                    'end_char': chunk.end_char
                }
                for chunk in chunks
            ],
            'pipeline_results': results
        }
        
        # Save metadata
        metadata_file = self.output_dir / "pipeline_metadata.json"
        import json
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Metadata saved to: {metadata_file}")
    
    def test_search(self, query: str = "property loss claim", top_k: int = 5) -> Dict[str, Any]:
        """Test the search functionality"""
        self.logger.info(f"Testing search with query: '{query}'")
        
        try:
            from lib.search_api import SearchQuery
            
            search_query = SearchQuery(
                query_text=query,
                search_type="vector",
                top_k=top_k
            )
            
            response = self.search_api.search(search_query)
            
            return {
                'query': query,
                'results_count': response.total_results,
                'search_time_ms': response.search_time_ms,
                'results': [
                    {
                        'chunk_id': result.chunk_id,
                        'source_file': result.source_file,
                        'score': result.score,
                        'content_preview': result.content[:200] + "..." if len(result.content) > 200 else result.content
                    }
                    for result in response.results
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Search test failed: {str(e)}")
            return {'error': str(e)}

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="Claims Embeddings Pipeline")
    parser.add_argument("--source-dir", type=str, help="Source directory containing text files")
    parser.add_argument("--output-dir", type=str, help="Output directory for processed data")
    parser.add_argument("--vector-db", type=str, choices=["pinecone", "weaviate"], 
                       default="pinecone", help="Vector database type")
    parser.add_argument("--index-name", type=str, default="claims-embeddings", 
                       help="Vector database index name")
    parser.add_argument("--chunk-size", type=int, default=512, help="Text chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Chunk overlap")
    parser.add_argument("--test-search", action="store_true", help="Test search after pipeline")
    parser.add_argument("--query", type=str, default="property loss claim", 
                       help="Test search query")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(PROJECT_ROOT / "logs" / f"embeddings_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            logging.StreamHandler()
        ]
    )
    
    # Create logs directory
    (PROJECT_ROOT / "logs").mkdir(exist_ok=True)
    
    # Initialize pipeline
    pipeline = ClaimsEmbeddingsPipeline(
        source_dir=args.source_dir,
        output_dir=args.output_dir,
        vector_db_type=args.vector_db,
        index_name=args.index_name,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    # Run pipeline
    results = pipeline.run_full_pipeline()
    
    # Print results
    print("\n" + "=" * 80)
    print("PIPELINE RESULTS")
    print("=" * 80)
    print(f"Status: {results['status']}")
    print(f"Steps completed: {', '.join(results['steps_completed'])}")
    print(f"Chunks created: {results['statistics'].get('chunks_created', 0)}")
    print(f"Embeddings generated: {results['statistics'].get('embeddings_generated', 0)}")
    
    if results['errors']:
        print(f"Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  - {error}")
    
    # Test search if requested
    if args.test_search and results['status'] == 'success':
        print("\n" + "=" * 80)
        print("TESTING SEARCH")
        print("=" * 80)
        
        search_results = pipeline.test_search(args.query)
        
        if 'error' in search_results:
            print(f"Search test failed: {search_results['error']}")
        else:
            print(f"Query: {search_results['query']}")
            print(f"Results found: {search_results['results_count']}")
            print(f"Search time: {search_results['search_time_ms']:.2f}ms")
            print("\nTop results:")
            for i, result in enumerate(search_results['results'][:3], 1):
                print(f"{i}. {result['source_file']} (score: {result['score']:.3f})")
                print(f"   {result['content_preview']}")
                print()
    
    print(f"\nOutput directory: {results['output_dir']}")
    print("Pipeline completed!")

if __name__ == "__main__":
    main()
