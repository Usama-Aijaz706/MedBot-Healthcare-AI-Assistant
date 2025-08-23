#!/usr/bin/env python3
"""
PDF Processing and Embedding Creation Script
This script processes your medical PDFs and creates embeddings for the RAG system.
"""

import os
import sys
import time
from pathlib import Path
import logging

# Configure logging to show progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pdf_processing.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to process PDFs and create embeddings."""
    print("MedBot - PDF Processing and Embedding Creation")
    print("=" * 60)
    
    # Check if med-books directory exists
    med_books_dir = Path("med-books")
    if not med_books_dir.exists():
        print("med-books directory not found!")
        print("💡 Create it and add your medical PDFs first")
        return False
    
    # Count PDF files
    pdf_files = list(med_books_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in med-books directory!")
        print("💡 Add some medical PDF books to get started")
        return False
    
    print(f"Found {len(pdf_files)} PDF files to process")
    print("PDF files:")
    for i, pdf in enumerate(pdf_files[:10], 1):  # Show first 10
        print(f"   {i}. {pdf.name}")
    if len(pdf_files) > 10:
        print(f"   ... and {len(pdf_files) - 10} more")
    
    print("\nStarting PDF processing and embedding creation...")
    print("This will take several minutes depending on the number and size of PDFs")
    print("=" * 60)
    
    try:
        # Import our RAG system
        from rag_system import RAGSystem
        
        # Initialize RAG system with smaller chunks for faster processing
        print("Initializing RAG system...")
        rag = RAGSystem(chunk_size=800, chunk_overlap=100)
        
        # Get initial status
        status = rag.get_system_status()
        print(f"Initial system status: {status}")
        
        # Process PDFs and create embeddings
        print("\nInitializing knowledge base from medical PDFs...")
        print("Step 1: Processing PDFs and creating chunks...")
        
        start_time = time.time()
        success = rag.initialize_knowledge_base("med-books")
        end_time = time.time()
        
        if success:
            processing_time = end_time - start_time
            print(f"\nKnowledge base initialized successfully!")
            print(f"Total processing time: {processing_time:.2f} seconds")
            
            # Get final status
            final_status = rag.get_system_status()
            print(f"\nFinal system status:")
            print(f"   Total chunks: {final_status.get('total_chunks', 0)}")
            print(f"   Total embeddings: {final_status.get('total_chunks', 0)}")
            print(f"   Vector store: {final_status.get('vector_store', {}).get('status', 'unknown')}")
            
            print(f"\nYour medical knowledge base is now ready!")
            print(f"You can now start the web interface with: uv run python run_medbot.py")
            print(f"Or test the system with: uv run python test_rag.py")
            
            return True
        else:
            print("Failed to initialize knowledge base!")
            print("💡 Check the logs above for details")
            return False
            
    except ImportError as e:
        print(f"Import error: {e}")
        print("💡 Make sure all packages are installed:")
        print("   uv add fastapi uvicorn langchain langchain-community chromadb sentence-transformers pypdf2 python-multipart pydantic aiofiles numpy")
        return False
    except Exception as e:
        print(f"Error during processing: {e}")
        print("💡 Check the logs above for details")
        return False

def test_simple_rag(rag_system):
    """Test the RAG system with a simple query."""
    try:
        print("\nTesting RAG system with a simple query...")
        
        # Test query
        test_question = "What are the symptoms of diabetes?"
        print(f"Test question: {test_question}")
        
        response = rag_system.query_knowledge_base(test_question, top_k=3)
        
        if response["success"]:
            print("RAG query successful!")
            print(f"Response length: {len(response['response'])} characters")
            print(f"Chunks used: {response['chunks_used']}")
            print(f"Sources: {response['sources']}")
            
            # Show a preview of the response
            print(f"\nResponse preview:")
            print(response['response'][:500] + "...")
            
            return True
        else:
            print(f"RAG query failed: {response.get('error')}")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    try:
        # Process PDFs and create embeddings
        success = main()
        
        if success:
            print("\n" + "=" * 60)
            print("PDF Processing Complete!")
            print("=" * 60)
            
            # Test the system
            test_simple_rag(rag)
            
        else:
            print("\nPDF processing failed. Please check the errors above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("💡 Please check the error details above")
        sys.exit(1)
