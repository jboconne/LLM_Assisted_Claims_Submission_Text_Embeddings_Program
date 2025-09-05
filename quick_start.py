#!/usr/bin/env python3
"""
Quick Start Script - No API Keys Required
Runs the embeddings pipeline with local FAISS database

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

def main():
    """Quick start with local database"""
    
    print("🚀 QUICK START - Claims Data Embeddings & Search")
    print("=" * 60)
    print("This script will set up everything using local storage")
    print("(No API keys or external services required)")
    print()
    
    # Check if source files exist
    source_dir = PROJECT_ROOT / "source_output_files"
    if not source_dir.exists() or not list(source_dir.glob("*.txt")):
        print("❌ No text files found in source_output_files/")
        print("Please run the text extraction first:")
        print("  python LLM_Assisted_Claims_Submission_Text_Extraction_Program.py")
        return
    
    print("✅ Found source text files")
    
    # Set environment variable for local database
    os.environ['VECTOR_DB_TYPE'] = 'local'
    
    try:
        # Import and run pipeline
        from embeddings_pipeline import ClaimsEmbeddingsPipeline
        
        print("📦 Initializing pipeline...")
        pipeline = ClaimsEmbeddingsPipeline(
            source_dir=str(source_dir),
            output_dir=str(PROJECT_ROOT / "embeddings_output"),
            vector_db_type="local",
            index_name="claims-embeddings-local",
            chunk_size=512,
            chunk_overlap=50
        )
        
        print("🔄 Running embeddings pipeline...")
        results = pipeline.run_full_pipeline()
        
        if results['status'] == 'success':
            print("\n🎉 SUCCESS! Pipeline completed")
            print(f"📊 Created {results['statistics'].get('chunks_created', 0)} chunks")
            print(f"🧠 Generated {results['statistics'].get('embeddings_generated', 0)} embeddings")
            
            print("\n🌐 Starting web interface...")
            print("Open your browser to: http://localhost:5000")
            print("Press Ctrl+C to stop the web server")
            
            # Start web app
            from web_app import app
            app.run(host='0.0.0.0', port=5000, debug=False)
            
        else:
            print(f"\n❌ Pipeline failed: {results.get('errors', ['Unknown error'])}")
            
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Install with: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check the logs for more details")

if __name__ == "__main__":
    main()
