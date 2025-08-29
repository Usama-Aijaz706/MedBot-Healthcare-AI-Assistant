#!/usr/bin/env python3
"""
Debug script to test RAG system functionality
"""

import logging
from rag_system import RAGSystem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_healthcare_detection():
    """Test healthcare query detection"""
    print("🔍 Testing healthcare query detection...")
    
    try:
        # Initialize RAG system
        rag = RAGSystem()
        print("✅ RAG system initialized")
        
        # Test query
        test_query = "Tell me about microbiology and its importance, explain in detail"
        print(f"📝 Testing query: '{test_query}'")
        
        # Check if it's a healthcare query
        is_healthcare = rag._is_healthcare_query(test_query)
        print(f"🏥 Is healthcare query: {is_healthcare}")
        
        if is_healthcare:
            print("✅ Query should be allowed")
            
            # Try to generate a response
            print("🔄 Attempting to generate response...")
            response = rag.generate_azure_enhanced_response(
                question=test_query,
                chat_history=[]
            )
            
            print(f"📊 Response success: {response.get('success', False)}")
            if response.get('success'):
                print(f"📝 Response length: {len(response.get('response', ''))}")
                print(f"🔗 Chunks used: {response.get('chunks_used', 0)}")
                print(f"📄 Response preview: {response.get('response', '')[:200]}...")
            else:
                print(f"❌ Error: {response.get('error', 'Unknown error')}")
        else:
            print("❌ Query was blocked - this is the problem!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_healthcare_detection()
