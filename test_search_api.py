#!/usr/bin/env python3
"""
Test Search API
Quick test to verify the search API is working correctly

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

def test_search_api():
    """Test the search API functionality"""
    
    print("🧪 Testing Search API")
    print("=" * 40)
    
    try:
        # Set environment variable for local database
        os.environ['VECTOR_DB_TYPE'] = 'local'
        
        # Import components
        from lib.embeddings_generator import ClaimsEmbeddingsGenerator
        from lib.vector_database import VectorDatabaseManager
        from lib.search_api import ClaimsSearchAPI, SearchQuery
        
        print("✅ Imports successful")
        
        # Initialize components
        print("📦 Initializing components...")
        embeddings_gen = ClaimsEmbeddingsGenerator()
        vector_db = VectorDatabaseManager(db_type="local")
        search_api = ClaimsSearchAPI(
            embeddings_generator=embeddings_gen,
            vector_db=vector_db,
            index_name="claims-embeddings-local"
        )
        print("✅ Components initialized")
        
        # Test search
        print("🔍 Testing search...")
        query = SearchQuery(
            query_text="property loss claim",
            search_type="vector",
            top_k=5
        )
        
        results = search_api.search(query)
        print(f"✅ Search completed: {results.total_results} results found")
        print(f"   Search time: {results.search_time_ms:.2f}ms")
        
        # Show results
        if results.results:
            print("\n📋 Search Results:")
            for i, result in enumerate(results.results[:3], 1):
                print(f"  {i}. {result.source_file} (score: {result.score:.3f})")
                print(f"     {result.content[:100]}...")
                print()
        
        # Test index stats
        print("📊 Testing index stats...")
        stats = search_api.get_index_stats()
        print(f"✅ Index stats: {stats}")
        
        print("\n🎉 All tests passed! Search API is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    logging.basicConfig(level=logging.INFO)
    
    success = test_search_api()
    
    if success:
        print("\n✅ Search API is ready!")
        print("You can now use the web interface at: http://localhost:5000")
    else:
        print("\n❌ Fix the issues above before using the search API")
        sys.exit(1)

if __name__ == "__main__":
    main()
