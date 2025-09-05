#!/usr/bin/env python3
"""
Web Application for Claims Data Search
Provides a web interface for searching claims data using vector similarity and keyword search

Author: LLM Claims Processing Team
Version: 1.0
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Import our custom modules
from lib.embeddings_generator import ClaimsEmbeddingsGenerator
from lib.vector_database import VectorDatabaseManager
from lib.search_api import ClaimsSearchAPI, SearchQuery
from lib.text_chunker import ClaimsTextChunker

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for search components
search_api = None
embeddings_generator = None
vector_db = None

def initialize_search_components():
    """Initialize search components"""
    global search_api, embeddings_generator, vector_db
    
    try:
        # Initialize embeddings generator
        embeddings_generator = ClaimsEmbeddingsGenerator()
        logger.info("Embeddings generator initialized")
        
        # Initialize vector database (using environment variables)
        db_type = os.getenv('VECTOR_DB_TYPE', 'local')  # Default to local for easier setup
        vector_db = VectorDatabaseManager(db_type=db_type)
        logger.info(f"Vector database initialized: {db_type}")
        
        # Initialize search API
        search_api = ClaimsSearchAPI(
            embeddings_generator=embeddings_generator,
            vector_db=vector_db,
            index_name="claims-embeddings-local"
        )
        logger.info("Search API initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize search components: {str(e)}")
        return False

@app.route('/')
def index():
    """Main search page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    """Search API endpoint"""
    try:
        if not search_api:
            # Try to initialize if not already done
            if not initialize_search_components():
                return jsonify({'error': 'Failed to initialize search API'}), 500
        
        # Get search parameters
        data = request.get_json()
        query_text = data.get('query', '').strip()
        search_type = data.get('type', 'vector')
        top_k = int(data.get('top_k', 10))
        min_score = float(data.get('min_score', 0.0))
        filters = data.get('filters', {})
        
        if not query_text:
            return jsonify({'error': 'Query text is required'}), 400
        
        # Create search query
        query = SearchQuery(
            query_text=query_text,
            search_type=search_type,
            top_k=top_k,
            min_score=min_score,
            filters=filters
        )
        
        # Perform search
        response = search_api.search(query)
        
        # Convert results to JSON-serializable format
        results = []
        for result in response.results:
            results.append({
                'chunk_id': result.chunk_id,
                'content': result.content,
                'source_file': result.source_file,
                'score': result.score,
                'metadata': result.metadata
            })
        
        return jsonify({
            'query': {
                'text': response.query.query_text,
                'type': response.query.search_type,
                'top_k': response.query.top_k
            },
            'results': results,
            'total_results': response.total_results,
            'search_time_ms': response.search_time_ms,
            'search_type': response.search_type,
            'metadata': response.metadata
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get search index statistics"""
    try:
        if not search_api:
            # Try to initialize if not already done
            if not initialize_search_components():
                return jsonify({'error': 'Failed to initialize search API'}), 500
        
        stats = search_api.get_index_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'search_api_initialized': search_api is not None
    })

@app.route('/api/process_files', methods=['POST'])
def process_files():
    """Process files and generate embeddings"""
    try:
        if not search_api:
            # Try to initialize if not already done
            if not initialize_search_components():
                return jsonify({'error': 'Failed to initialize search API'}), 500
        
        # Get source directory
        source_dir = Path(__file__).parent / "source_output_files"
        
        if not source_dir.exists():
            return jsonify({'error': 'Source output files directory not found'}), 404
        
        # Initialize chunker
        chunker = ClaimsTextChunker(chunk_size=512, chunk_overlap=50)
        
        # Chunk all text files
        chunks = chunker.chunk_directory(str(source_dir))
        
        if not chunks:
            return jsonify({'error': 'No chunks created from source files'}), 400
        
        # Generate embeddings
        embeddings = search_api.embeddings_generator.generate_embeddings_from_chunks(chunks)
        
        # Store in vector database
        success = search_api.vector_db.upsert_embeddings(embeddings, search_api.index_name)
        
        if not success:
            return jsonify({'error': 'Failed to store embeddings in vector database'}), 500
        
        return jsonify({
            'message': 'Files processed successfully',
            'chunks_created': len(chunks),
            'embeddings_generated': len(embeddings),
            'stored_in_db': success
        })
        
    except Exception as e:
        logger.error(f"Process files error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Create templates directory and HTML files
def create_templates():
    """Create HTML templates for the web interface"""
    templates_dir = Path(__file__).parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create index.html
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claims Data Search</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .search-section {
            padding: 40px;
        }
        
        .search-form {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .search-input {
            flex: 1;
            min-width: 300px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .search-type {
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            background: white;
        }
        
        .search-btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .search-btn:hover {
            transform: translateY(-2px);
        }
        
        .search-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .filters {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .filter-group label {
            font-weight: 600;
            color: #555;
        }
        
        .filter-group input, .filter-group select {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .results-section {
            margin-top: 30px;
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .results-count {
            font-size: 1.1em;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .search-time {
            color: #666;
            font-size: 0.9em;
        }
        
        .result-item {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transition: box-shadow 0.3s;
        }
        
        .result-item:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .result-source {
            font-weight: 600;
            color: #667eea;
            font-size: 0.9em;
        }
        
        .result-score {
            background: #e8f5e8;
            color: #2d5a2d;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 600;
        }
        
        .result-content {
            color: #333;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        
        .result-metadata {
            font-size: 0.8em;
            color: #666;
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .error {
            background: #ffe6e6;
            color: #d63031;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .process-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .process-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        
        .process-btn:hover {
            background: #218838;
        }
        
        .process-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        @media (max-width: 768px) {
            .search-form {
                flex-direction: column;
            }
            
            .search-input {
                min-width: 100%;
            }
            
            .filters {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Claims Data Search</h1>
            <p>Search through insurance claims data using AI-powered vector similarity and keyword search</p>
        </div>
        
        <div class="search-section">
            <div class="process-section">
                <h3>📁 Process Files</h3>
                <p>First, process your extracted text files to generate embeddings and store them in the vector database.</p>
                <button id="processBtn" class="process-btn" onclick="processFiles()">Process Files & Generate Embeddings</button>
                <div id="processStatus"></div>
            </div>
            
            <form class="search-form" onsubmit="performSearch(event)">
                <input type="text" id="queryInput" class="search-input" placeholder="Enter your search query..." required>
                <select id="searchType" class="search-type">
                    <option value="vector">Vector Search</option>
                    <option value="keyword">Keyword Search</option>
                    <option value="hybrid">Hybrid Search</option>
                </select>
                <button type="submit" id="searchBtn" class="search-btn">Search</button>
            </form>
            
            <div class="filters">
                <div class="filter-group">
                    <label for="topK">Max Results:</label>
                    <input type="number" id="topK" value="10" min="1" max="50">
                </div>
                <div class="filter-group">
                    <label for="minScore">Min Score:</label>
                    <input type="number" id="minScore" value="0.0" min="0" max="1" step="0.1">
                </div>
            </div>
            
            <div id="resultsSection" class="results-section" style="display: none;">
                <div class="results-header">
                    <div class="results-count" id="resultsCount">0 results</div>
                    <div class="search-time" id="searchTime"></div>
                </div>
                <div id="resultsContainer"></div>
            </div>
        </div>
    </div>

    <script>
        let isProcessing = false;
        
        async function processFiles() {
            const btn = document.getElementById('processBtn');
            const status = document.getElementById('processStatus');
            
            if (isProcessing) return;
            
            isProcessing = true;
            btn.disabled = true;
            btn.textContent = 'Processing...';
            status.innerHTML = '<div class="loading">Processing files and generating embeddings...</div>';
            
            try {
                const response = await fetch('/api/process_files', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    status.innerHTML = `
                        <div style="color: #28a745; padding: 10px; background: #d4edda; border-radius: 5px;">
                            ✅ ${data.message}<br>
                            Chunks created: ${data.chunks_created}<br>
                            Embeddings generated: ${data.embeddings_generated}
                        </div>
                    `;
                } else {
                    status.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                }
            } catch (error) {
                status.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
            } finally {
                isProcessing = false;
                btn.disabled = false;
                btn.textContent = 'Process Files & Generate Embeddings';
            }
        }
        
        async function performSearch(event) {
            event.preventDefault();
            
            const query = document.getElementById('queryInput').value.trim();
            const searchType = document.getElementById('searchType').value;
            const topK = parseInt(document.getElementById('topK').value);
            const minScore = parseFloat(document.getElementById('minScore').value);
            
            if (!query) return;
            
            const searchBtn = document.getElementById('searchBtn');
            const resultsSection = document.getElementById('resultsSection');
            const resultsContainer = document.getElementById('resultsContainer');
            
            searchBtn.disabled = true;
            searchBtn.textContent = 'Searching...';
            resultsContainer.innerHTML = '<div class="loading">Searching...</div>';
            resultsSection.style.display = 'block';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: query,
                        type: searchType,
                        top_k: topK,
                        min_score: minScore
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    displayResults(data);
                } else {
                    resultsContainer.innerHTML = `<div class="error">❌ Error: ${data.error}</div>`;
                }
            } catch (error) {
                resultsContainer.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
            } finally {
                searchBtn.disabled = false;
                searchBtn.textContent = 'Search';
            }
        }
        
        function displayResults(data) {
            const resultsCount = document.getElementById('resultsCount');
            const searchTime = document.getElementById('searchTime');
            const resultsContainer = document.getElementById('resultsContainer');
            
            resultsCount.textContent = `${data.total_results} results`;
            searchTime.textContent = `Search time: ${data.search_time_ms.toFixed(2)}ms`;
            
            if (data.results.length === 0) {
                resultsContainer.innerHTML = '<div class="loading">No results found. Try adjusting your search terms or filters.</div>';
                return;
            }
            
            let html = '';
            data.results.forEach((result, index) => {
                html += `
                    <div class="result-item">
                        <div class="result-header">
                            <div class="result-source">${result.source_file}</div>
                            <div class="result-score">Score: ${result.score.toFixed(3)}</div>
                        </div>
                        <div class="result-content">${result.content}</div>
                        <div class="result-metadata">
                            <strong>Chunk ID:</strong> ${result.chunk_id}<br>
                            <strong>Search Type:</strong> ${data.search_type}<br>
                            ${result.metadata ? `<strong>Metadata:</strong> ${JSON.stringify(result.metadata, null, 2)}` : ''}
                        </div>
                    </div>
                `;
            });
            
            resultsContainer.innerHTML = html;
        }
        
        // Load stats on page load
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                console.log('Index stats:', data);
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }
        
        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
        });
    </script>
</body>
</html>'''
    
    with open(templates_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    logger.info("HTML templates created successfully")

if __name__ == "__main__":
    # Create templates
    create_templates()
    
    # Initialize search components
    if initialize_search_components():
        logger.info("Starting web application...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        logger.error("Failed to initialize search components. Please check your configuration.")
        print("Failed to initialize search components. Please check your configuration.")
        print("Make sure to set the required environment variables:")
        print("- VECTOR_DB_TYPE (pinecone or weaviate)")
        print("- PINECONE_API_KEY (if using Pinecone)")
        print("- PINECONE_ENVIRONMENT (if using Pinecone)")
        print("- WEAVIATE_URL (if using Weaviate)")
        print("- WEAVIATE_API_KEY (if using Weaviate)")
