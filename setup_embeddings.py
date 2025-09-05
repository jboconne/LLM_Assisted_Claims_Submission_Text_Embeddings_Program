#!/usr/bin/env python3
"""
Setup Script for Claims Data Embeddings & Search
Helps users set up the embeddings and search system

Author: LLM Claims Processing Team
Version: 1.0
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 80)
    print("🚀 CLAIMS DATA EMBEDDINGS & SEARCH SETUP")
    print("=" * 80)
    print("This script will help you set up the embeddings and search system.")
    print()

def check_python_version():
    """Check Python version"""
    print("📋 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required. Current version:", f"{version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = [
        "embeddings_output",
        "logs",
        "templates"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment():
    """Setup environment variables"""
    print("\n🔧 Environment Setup")
    print("You need to set up environment variables for your vector database.")
    print("\nChoose your vector database:")
    print("1. Pinecone (Recommended - Cloud-based)")
    print("2. Weaviate (Open-source)")
    print("3. Skip for now")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    env_vars = {}
    
    if choice == "1":
        print("\nSetting up Pinecone...")
        api_key = input("Enter your Pinecone API key: ").strip()
        environment = input("Enter your Pinecone environment (e.g., us-west1-gcp): ").strip()
        
        env_vars = {
            "VECTOR_DB_TYPE": "pinecone",
            "PINECONE_API_KEY": api_key,
            "PINECONE_ENVIRONMENT": environment
        }
        
    elif choice == "2":
        print("\nSetting up Weaviate...")
        url = input("Enter Weaviate URL (default: http://localhost:8080): ").strip() or "http://localhost:8080"
        api_key = input("Enter Weaviate API key (optional): ").strip()
        
        env_vars = {
            "VECTOR_DB_TYPE": "weaviate",
            "WEAVIATE_URL": url
        }
        
        if api_key:
            env_vars["WEAVIATE_API_KEY"] = api_key
    
    elif choice == "3":
        print("Skipping environment setup. You can set these later.")
        return True
    
    else:
        print("Invalid choice. Skipping environment setup.")
        return True
    
    # Save environment variables to .env file
    if env_vars:
        env_file = Path(".env")
        with open(env_file, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        print(f"✅ Environment variables saved to {env_file}")
    
    return True

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        from lib.text_chunker import ClaimsTextChunker
        from lib.embeddings_generator import ClaimsEmbeddingsGenerator
        from lib.vector_database import VectorDatabaseManager
        from lib.search_api import ClaimsSearchAPI
        
        print("✅ All modules imported successfully")
        
        # Test chunker
        chunker = ClaimsTextChunker()
        print("✅ Text chunker initialized")
        
        # Test embeddings generator (this will download the model)
        print("📥 Downloading BGE model (this may take a few minutes)...")
        generator = ClaimsEmbeddingsGenerator()
        print("✅ Embeddings generator initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def create_sample_config():
    """Create sample configuration file"""
    print("\n📝 Creating sample configuration...")
    
    config = {
        "chunking": {
            "chunk_size": 512,
            "chunk_overlap": 50,
            "min_chunk_size": 100
        },
        "embeddings": {
            "model_name": "BAAI/bge-large-en-v1.5",
            "normalize_embeddings": True
        },
        "vector_database": {
            "type": "pinecone",
            "index_name": "claims-embeddings",
            "metric": "cosine"
        },
        "search": {
            "default_top_k": 10,
            "default_min_score": 0.0
        }
    }
    
    config_file = Path("config.json")
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Sample configuration saved to {config_file}")

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "=" * 80)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
    print("\nNext steps:")
    print("1. 📄 Process your claims data (if not already done):")
    print("   python LLM_Assisted_Claims_Submission_Text_Extraction_Program.py")
    
    print("\n2. 🧠 Generate embeddings and set up search:")
    print("   python embeddings_pipeline.py")
    
    print("\n3. 🌐 Start the web interface:")
    print("   python web_app.py")
    print("   Then open: http://localhost:5000")
    
    print("\n4. 📚 Run examples to learn the API:")
    print("   python example_usage.py")
    
    print("\n5. 📖 Read the documentation:")
    print("   See EMBEDDINGS_README.md for detailed usage instructions")
    
    print("\n" + "=" * 80)
    print("Happy searching! 🔍")
    print("=" * 80)

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup environment
    setup_environment()
    
    # Test installation
    if not test_installation():
        print("\n❌ Setup failed at installation test")
        print("Please check the error messages above and try again")
        sys.exit(1)
    
    # Create sample config
    create_sample_config()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
