#!/usr/bin/env python3
"""
Test Local Vector Database
Quick test to verify the local database works correctly

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

def test_local_database():
    """Test the local vector database functionality"""
    
    print("🧪 Testing Local Vector Database")
    print("=" * 40)
    
    try:
        # Test imports
        from lib.local_vector_db import LocalVectorDB
        from lib.embeddings_generator import ClaimsEmbeddingsGenerator
        print("✅ Imports successful")
        
        # Test database creation
        db = LocalVectorDB("test_index")
        print("✅ Database initialized")
        
        # Test index creation
        success = db.create_index(dimension=1024)
        print(f"✅ Index created: {success}")
        
        # Test stats
        stats = db.get_stats()
        print(f"✅ Stats: {stats}")
        
        # Test embeddings generation
        print("\n🧠 Testing embeddings generation...")
        generator = ClaimsEmbeddingsGenerator()
        
        # Generate test embeddings
        test_texts = [
            "Property loss claim for Northside Manufacturing",
            "Policy number CPP-456789123 effective March 1st 2025",
            "Loss occurred on April 7th 2025 at 10:45 PM"
        ]
        
        embeddings = generator.generate_embeddings_batch(test_texts)
        print(f"✅ Generated {len(embeddings)} embeddings")
        
        # Test storing embeddings
        success = db.upsert_embeddings(embeddings)
        print(f"✅ Stored embeddings: {success}")
        
        # Test search
        query_embedding = generator.generate_embedding("property damage claim")
        results = db.search(query_embedding.embedding, top_k=3)
        print(f"✅ Search returned {len(results)} results")
        
        # Print search results
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.source_file} (score: {result.score:.3f})")
            print(f"     {result.content[:50]}...")
        
        print("\n🎉 All tests passed! Local database is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    logging.basicConfig(level=logging.INFO)
    
    success = test_local_database()
    
    if success:
        print("\n✅ Ready to run the full pipeline!")
        print("Run: python quick_start.py")
    else:
        print("\n❌ Fix the issues above before running the pipeline")
        sys.exit(1)

if __name__ == "__main__":
    main()
