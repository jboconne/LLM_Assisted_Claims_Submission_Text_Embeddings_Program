#!/usr/bin/env python3
"""
Run Embeddings Pipeline with Local Database
Quick start script that uses local FAISS database (no API keys required)

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

from embeddings_pipeline import ClaimsEmbeddingsPipeline

def main():
    """Run the embeddings pipeline with local database"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(PROJECT_ROOT / "logs" / "local_pipeline.log"),
            logging.StreamHandler()
        ]
    )
    
    # Create logs directory
    (PROJECT_ROOT / "logs").mkdir(exist_ok=True)
    
    print("🚀 Starting Claims Embeddings Pipeline with Local Database")
    print("=" * 70)
    print("This will use FAISS for local vector storage (no API keys required)")
    print()
    
    try:
        # Initialize pipeline with local database
        pipeline = ClaimsEmbeddingsPipeline(
            source_dir="./source_output_files",
            output_dir="./embeddings_output",
            vector_db_type="local",  # Use local FAISS database
            index_name="claims-embeddings-local",
            chunk_size=512,
            chunk_overlap=50
        )
        
        print("✅ Pipeline initialized successfully")
        print("📄 Processing source files...")
        
        # Run the complete pipeline
        results = pipeline.run_full_pipeline()
        
        # Print results
        print("\n" + "=" * 70)
        print("📊 PIPELINE RESULTS")
        print("=" * 70)
        print(f"Status: {results['status']}")
        print(f"Steps completed: {', '.join(results['steps_completed'])}")
        print(f"Chunks created: {results['statistics'].get('chunks_created', 0)}")
        print(f"Embeddings generated: {results['statistics'].get('embeddings_generated', 0)}")
        
        if results['errors']:
            print(f"Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
        
        if results['status'] == 'success':
            print("\n🎉 Pipeline completed successfully!")
            print("\nNext steps:")
            print("1. 🌐 Start the web interface:")
            print("   python web_app.py")
            print("2. 🔍 Open your browser to: http://localhost:5000")
            print("3. 📚 Try searching your claims data!")
            
            # Test search
            print("\n🧪 Testing search functionality...")
            search_results = pipeline.test_search("property loss claim", top_k=3)
            
            if 'error' not in search_results:
                print(f"✅ Search test successful!")
                print(f"Found {search_results['results_count']} results")
                print(f"Search time: {search_results['search_time_ms']:.2f}ms")
            else:
                print(f"⚠️ Search test failed: {search_results['error']}")
        
        print(f"\n📁 Output directory: {results['output_dir']}")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure you have extracted text files in source_output_files/")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check the logs for more details")
        sys.exit(1)

if __name__ == "__main__":
    main()
