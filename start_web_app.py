#!/usr/bin/env python3
"""
Start Web Application with Proper Initialization
Ensures all components are properly initialized before starting the web server

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
    """Start the web application with proper initialization"""
    
    # Set environment variable for local database
    os.environ['VECTOR_DB_TYPE'] = 'local'
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Starting Claims Data Search Web Application")
    print("=" * 60)
    print("Using local FAISS database (no API keys required)")
    print()
    
    try:
        # Import and start the web app
        from web_app import app, initialize_search_components
        
        # Initialize search components
        print("📦 Initializing search components...")
        if initialize_search_components():
            print("✅ Search components initialized successfully")
        else:
            print("❌ Failed to initialize search components")
            print("The web app will still start, but search may not work properly")
        
        print("\n🌐 Starting web server...")
        print("Open your browser to: http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        print()
        
        # Start the Flask app
        app.run(host='0.0.0.0', port=5000, debug=False)
        
    except Exception as e:
        print(f"❌ Failed to start web application: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check that you have text files in source_output_files/")
        print("3. Verify Python 3.8+ is installed")
        sys.exit(1)

if __name__ == "__main__":
    main()
