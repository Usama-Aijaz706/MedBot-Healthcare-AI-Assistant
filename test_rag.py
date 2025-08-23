#!/usr/bin/env python3
"""
🧪 Test Script for MedBot RAG System
This script tests the complete RAG workflow implementation.
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rag_system():
    """Test the complete RAG system."""
    try:
        logger.info("🧪 Starting RAG system test...")
        
        # Import our RAG system
        from rag_system import RAGSystem
        
        # Initialize RAG system
        logger.info("🚀 Initializing RAG system...")
        rag = RAGSystem(chunk_size=800, chunk_overlap=100)
        
        # Check system status
        status = rag.get_system_status()
        logger.info(f"📊 Initial system status: {status}")
        
        # Test PDF processing
        med_books_dir = "med-books"
        if not Path(med_books_dir).exists():
            logger.error(f"❌ Directory {med_books_dir} not found!")
            return False
        
        # Initialize knowledge base
        logger.info("🏥 Initializing knowledge base from medical PDFs...")
        success = rag.initialize_knowledge_base(med_books_dir)
        
        if not success:
            logger.error("❌ Failed to initialize knowledge base!")
            return False
        
        # Get updated status
        status = rag.get_system_status()
        logger.info(f"📊 Updated system status: {status}")
        
        # Test querying
        test_questions = [
            "What are the symptoms of diabetes?",
            "How to treat hypertension?",
            "What is the normal blood pressure range?",
            "Explain cardiovascular disease",
            "What are common skin conditions?"
        ]
        
        logger.info("🔍 Testing knowledge base queries...")
        for question in test_questions:
            logger.info(f"❓ Testing question: {question}")
            
            response = rag.query_knowledge_base(question, top_k=3)
            
            if response["success"]:
                logger.info(f"✅ Query successful!")
                logger.info(f"   📝 Response length: {len(response['response'])} characters")
                logger.info(f"   🔢 Chunks used: {response['chunks_used']}")
                logger.info(f"   📚 Sources: {response['sources']}")
            else:
                logger.warning(f"⚠️ Query failed: {response.get('error')}")
        
        logger.info("🎉 RAG system test completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("💡 Make sure all required packages are installed")
        return False
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False

def test_pdf_processor():
    """Test the PDF processor separately."""
    try:
        logger.info("📚 Testing PDF processor...")
        
        from pdf_processor import PDFProcessor
        
        processor = PDFProcessor(chunk_size=800, chunk_overlap=100)
        
        med_books_dir = "med-books"
        if not Path(med_books_dir).exists():
            logger.error(f"❌ Directory {med_books_dir} not found!")
            return False
        
        # Process PDFs
        chunks = processor.process_pdf_directory(med_books_dir)
        
        if chunks:
            logger.info(f"✅ PDF processing successful! Created {len(chunks)} chunks")
            
            # Get statistics
            stats = processor.get_chunk_statistics(chunks)
            logger.info(f"📊 Chunk statistics: {stats}")
            
            # Show sample chunks
            for i, chunk in enumerate(chunks[:3]):
                logger.info(f"📄 Sample chunk {i+1}:")
                logger.info(f"   ID: {chunk['id']}")
                logger.info(f"   Source: {chunk['source']}")
                logger.info(f"   Size: {chunk['chunk_size']} characters")
                logger.info(f"   Content preview: {chunk['content'][:100]}...")
            
            return True
        else:
            logger.error("❌ No chunks created from PDFs!")
            return False
            
    except Exception as e:
        logger.error(f"❌ PDF processor test failed: {e}")
        return False

def test_embedding_system():
    """Test the embedding system separately."""
    try:
        logger.info("🔢 Testing embedding system...")
        
        from embedding_system import EmbeddingSystem
        
        embedding_sys = EmbeddingSystem()
        
        # Check if system initialized
        status = embedding_sys.get_vector_store_info()
        logger.info(f"📊 Embedding system status: {status}")
        
        if status.get('status') == 'active':
            logger.info("✅ Embedding system initialized successfully!")
            return True
        else:
            logger.warning(f"⚠️ Embedding system not fully initialized: {status}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Embedding system test failed: {e}")
        return False

def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("🧪 MedBot RAG System Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("PDF Processor", test_pdf_processor),
        ("Embedding System", test_embedding_system),
        ("Complete RAG System", test_rag_system)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results[test_name] = "✅ PASSED" if result else "❌ FAILED"
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results[test_name] = "💥 CRASHED"
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        logger.info(f"{test_name}: {result}")
    
    # Overall result
    passed = sum(1 for result in results.values() if "PASSED" in result)
    total = len(results)
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! RAG system is working correctly.")
        return True
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
