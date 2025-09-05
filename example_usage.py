#!/usr/bin/env python3
"""
Example Usage Script for Claims Data Embeddings & Search
Demonstrates how to use the embeddings and search functionality

Author: LLM Claims Processing Team
Version: 1.0
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lib.text_chunker import ClaimsTextChunker
from lib.embeddings_generator import ClaimsEmbeddingsGenerator
from lib.vector_database import VectorDatabaseManager
from lib.search_api import ClaimsSearchAPI, SearchQuery

def setup_logging():
    """Setup logging for the example"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def example_1_basic_chunking():
    """Example 1: Basic text chunking"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Text Chunking")
    print("="*60)
    
    # Initialize chunker
    chunker = ClaimsTextChunker(chunk_size=256, chunk_overlap=25)
    
    # Sample text (simulating a claims document)
    sample_text = """
    ACORD 1 - PROPERTY LOSS NOTICE
    
    Producer Agency: Summit Business Insurance Agency
    Producer: David Thompson
    Phone: 555-345-6789
    Email: david.thompson@summitinsurance.com
    
    Policy Information:
    Policy Number: CPP-456789123
    Effective Date: March 1, 2025
    Expiration Date: March 1, 2026
    Company: Centennial Commercial Insurance
    
    Insured Information:
    Name: Northside Manufacturing Incorporated
    Tax ID: 84-3214567
    Business Phone: 555-432-8765
    Email: operations@northsidemfg.com
    Contact Person: Jennifer Martinez, Operations Manager
    
    Business Address:
    1250 Industrial Parkway
    Metropolis, Illinois 60001
    
    Loss Information:
    Date and Time of Loss: April 7, 2025 at 10:45 PM
    Location: 1250 Industrial Parkway, Metropolis, IL
    Type of Loss: Property damage due to equipment malfunction
    Estimated Loss: $150,000
    """
    
    # Chunk the text
    chunks = chunker.chunk_text(sample_text, "sample_claim.txt")
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Size: {len(chunk.content)} characters")
        print(f"  Preview: {chunk.content[:100]}...")

def example_2_embeddings_generation():
    """Example 2: Generate embeddings"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Embeddings Generation")
    print("="*60)
    
    # Initialize embeddings generator
    generator = ClaimsEmbeddingsGenerator()
    
    # Sample texts
    sample_texts = [
        "Property loss claim for Northside Manufacturing",
        "Policy number CPP-456789123 effective March 1st 2025",
        "Loss occurred on April 7th 2025 at 10:45 PM",
        "Estimated damage of $150,000 to industrial equipment",
        "Contact person Jennifer Martinez, Operations Manager"
    ]
    
    # Generate embeddings
    embeddings = generator.generate_embeddings_batch(sample_texts)
    
    print(f"Generated {len(embeddings)} embeddings:")
    for i, emb in enumerate(embeddings, 1):
        print(f"\nEmbedding {i}:")
        print(f"  Text: {emb.content}")
        print(f"  Dimension: {emb.embedding_dim}")
        print(f"  Model: {emb.model_name}")
        print(f"  Vector shape: {emb.embedding.shape}")

def example_3_vector_database():
    """Example 3: Vector database operations (simulated)"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Vector Database Operations")
    print("="*60)
    
    print("Note: This example shows the interface without actual database connection")
    print("To use with real database, set environment variables:")
    print("  - VECTOR_DB_TYPE=pinecone")
    print("  - PINECONE_API_KEY=your_key")
    print("  - PINECONE_ENVIRONMENT=your_env")
    
    # This would normally connect to a real database
    # vector_db = VectorDatabaseManager(db_type="pinecone")
    # index_created = vector_db.create_index("test-index", 1024)
    # print(f"Index created: {index_created}")

def example_4_search_simulation():
    """Example 4: Search simulation"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Search Simulation")
    print("="*60)
    
    # Initialize components (without database connection)
    generator = ClaimsEmbeddingsGenerator()
    
    # Sample documents
    documents = [
        "Property loss claim for Northside Manufacturing due to equipment malfunction",
        "Policy CPP-456789123 covers commercial property damage up to $2M",
        "Loss occurred on April 7th 2025 at 10:45 PM at industrial facility",
        "Contact Jennifer Martinez at operations@northsidemfg.com for details",
        "Estimated damage of $150,000 to manufacturing equipment and building"
    ]
    
    # Generate embeddings for documents
    doc_embeddings = generator.generate_embeddings_batch(documents)
    
    # Generate embedding for search query
    query_text = "equipment damage claim"
    query_embedding = generator.generate_embedding(query_text)
    
    print(f"Search Query: '{query_text}'")
    print(f"Query embedding dimension: {query_embedding.embedding_dim}")
    print(f"Query vector shape: {query_embedding.embedding.shape}")
    
    # Simulate similarity search (without actual vector database)
    print(f"\nFound {len(documents)} documents to search through")
    print("In a real implementation, this would use vector similarity search")

def example_5_web_interface():
    """Example 5: Web interface usage"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Web Interface")
    print("="*60)
    
    print("To start the web interface:")
    print("1. Set up your vector database credentials")
    print("2. Run: python web_app.py")
    print("3. Open browser to: http://localhost:5000")
    print("\nFeatures available in the web interface:")
    print("- Process files and generate embeddings")
    print("- Vector similarity search")
    print("- Keyword search")
    print("- Hybrid search")
    print("- Real-time search results")
    print("- Search analytics and statistics")

def example_6_full_pipeline():
    """Example 6: Full pipeline usage"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Full Pipeline")
    print("="*60)
    
    print("To run the complete pipeline:")
    print("1. Ensure you have extracted text files in source_output_files/")
    print("2. Set up vector database credentials")
    print("3. Run: python embeddings_pipeline.py")
    print("\nPipeline steps:")
    print("1. Chunk text files")
    print("2. Generate embeddings")
    print("3. Create vector database index")
    print("4. Store embeddings")
    print("5. Save metadata")
    print("6. Test search functionality")

def main():
    """Run all examples"""
    setup_logging()
    
    print("Claims Data Embeddings & Search - Usage Examples")
    print("=" * 60)
    
    try:
        example_1_basic_chunking()
        example_2_embeddings_generation()
        example_3_vector_database()
        example_4_search_simulation()
        example_5_web_interface()
        example_6_full_pipeline()
        
        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. Set up vector database credentials")
        print("2. Run the full pipeline: python embeddings_pipeline.py")
        print("3. Start web interface: python web_app.py")
        print("4. Begin searching your claims data!")
        
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
