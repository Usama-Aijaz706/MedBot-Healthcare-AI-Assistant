#!/usr/bin/env python3
"""
Simple test script for the MedBot knowledge base.
Run this after you've successfully initialized the knowledge base.
"""

from rag_system import RAGSystem

def test_knowledge_base():
    """Test the initialized knowledge base."""
    print("Testing MedBot Knowledge Base")
    print("=" * 50)
    
    try:
        # Initialize RAG system (this will load the existing knowledge base)
        print("Loading existing knowledge base...")
        rag = RAGSystem()
        
        # Get system status
        status = rag.get_system_status()
        print(f"System Status: {status['rag_system_status']}")
        print(f"Knowledge Base Initialized: {status['knowledge_base_initialized']}")
        print(f"Total Chunks: {status['total_chunks']}")
        print(f"Total Embeddings: {status['total_embeddings']}")
        
        if not status['knowledge_base_initialized']:
            print("\nKnowledge base not initialized. Please run process_pdfs.py first.")
            return False
        
        # Test some medical questions
        test_questions = [
            "What are the symptoms of diabetes?",
            "How to treat hypertension?",
            "What causes heart disease?",
            "What are the signs of depression?",
            "How to prevent cancer?"
        ]
        
        print(f"\nTesting {len(test_questions)} medical questions...")
        print("-" * 50)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. Question: {question}")
            
            try:
                response = rag.query_knowledge_base(question, top_k=3)
                
                if response["success"]:
                    print(f"   Status: SUCCESS")
                    print(f"   Chunks used: {response['chunks_used']}")
                    print(f"   Response length: {len(response['response'])} characters")
                    
                    # Show a brief preview
                    preview = response['response'][:200].replace('\n', ' ').strip()
                    print(f"   Preview: {preview}...")
                    
                else:
                    print(f"   Status: FAILED")
                    print(f"   Error: {response.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   Status: ERROR")
                print(f"   Exception: {e}")
        
        print(f"\n{'='*50}")
        print("Knowledge base test completed!")
        return True
        
    except Exception as e:
        print(f"Error testing knowledge base: {e}")
        return False

if __name__ == "__main__":
    test_knowledge_base()
