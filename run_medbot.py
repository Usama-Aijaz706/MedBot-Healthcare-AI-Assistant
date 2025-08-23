#!/usr/bin/env python3
"""
🚀 MedBot Runner Script
Simple script to start your RAG-enhanced healthcare chatbot.
"""

import os
import sys
import time
from pathlib import Path

def check_environment():
    """Check if the environment is ready."""
    print("🔍 Checking environment...")
    
    # Check if med-books directory exists
    if not Path("med-books").exists():
        print("❌ med-books directory not found!")
        print("💡 Create it and add your medical PDFs:")
        print("   mkdir med-books")
        print("   # Then copy your PDF files into it")
        return False
    
    # Check if there are PDF files
    pdf_files = list(Path("med-books").glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in med-books directory!")
        print("💡 Add some medical PDF books to get started")
        return False
    
    print(f"✅ Found {len(pdf_files)} PDF files")
    return True

def main():
    """Main runner function."""
    print("🏥 MedBot - RAG-Enhanced Healthcare AI Assistant")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return
    
    print("\n🚀 Starting MedBot...")
    print("📚 The system will:")
    print("   1. Process your medical PDFs")
    print("   2. Create intelligent chunks")
    print("   3. Generate embeddings")
    print("   4. Store in ChromaDB vector database")
    print("   5. Launch the web interface")
    
    print("\n⏳ This may take a few minutes on first run...")
    
    try:
        # Import and run the main application
        from main import app
        import uvicorn
        
        print("\n🌐 Starting web server...")
        print("📱 Open your browser to: http://localhost:8000")
        print("🔑 Use the web interface to initialize the knowledge base")
        print("\n" + "=" * 60)
        
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("💡 Make sure all packages are installed:")
        print("   uv add fastapi uvicorn langchain langchain-community chromadb sentence-transformers pypdf2 python-multipart pydantic aiofiles numpy")
        return
    except Exception as e:
        print(f"\n❌ Error starting MedBot: {e}")
        print("💡 Check the logs above for details")
        return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 MedBot stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Please check the error details above")
