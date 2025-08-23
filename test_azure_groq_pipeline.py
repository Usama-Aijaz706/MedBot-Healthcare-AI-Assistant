#!/usr/bin/env python3
"""
Test script for the Azure + Groq pipeline workflow.
This tests the new system where Azure enriches prompts and Groq generates final responses.
"""

from rag_system import RAGSystem

def test_azure_groq_pipeline():
    """Test the Azure + Groq pipeline workflow."""
    print("Testing MedBot Azure + Groq Pipeline")
    print("=" * 60)
    
    try:
        # Initialize RAG system
        print("Initializing RAG system...")
        rag = RAGSystem()
        
        # Get system status
        status = rag.get_system_status()
        print(f"System Status: {status['rag_system_status']}")
        print(f"Knowledge Base Initialized: {status['knowledge_base_initialized']}")
        print(f"Total Embeddings: {status['total_embeddings']}")
        
        if not status['knowledge_base_initialized']:
            print("Knowledge base not initialized. Please run process_pdfs.py first.")
            return False
        
        # Test medical questions with the new pipeline
        test_questions = [
            "What are the symptoms of diabetes?",
            "How to treat hypertension?",
            "What causes heart disease?"
        ]
        
        print(f"\nTesting {len(test_questions)} medical questions with Azure + Groq pipeline...")
        print("-" * 60)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. Question: {question}")
            print("Processing with Azure enrichment + Groq generation...")
            
            try:
                # This will now use Azure for enrichment and Groq for final response
                response = rag.query_knowledge_base(question, top_k=3)
                
                if response["success"]:
                    print(f"   Status: SUCCESS")
                    print(f"   Chunks used: {response['chunks_used']}")
                    print(f"   Response length: {len(response['response'])} characters")
                    print(f"   LLM Provider: {response.get('llm_provider', 'unknown')}")
                    
                    # Show a brief preview
                    preview = response['response'][:300].replace('\n', ' ').strip()
                    print(f"   Preview: {preview}...")
                    
                    # Check if it's using the new pipeline
                    if "enriched" in response['response'].lower() or "comprehensive" in response['response'].lower():
                        print("   ✅ Azure enrichment detected in response")
                    else:
                        print("   ⚠️ Response may not be using Azure enrichment")
                    
                else:
                    print(f"   Status: FAILED")
                    print(f"   Error: {response.get('error', 'Unknown error')}")
                    if 'message' in response:
                        print(f"   Message: {response['message']}")
                
            except Exception as e:
                print(f"   Status: ERROR")
                print(f"   Exception: {e}")
            
            print("-" * 40)
        
        print(f"\n{'='*60}")
        print("Azure + Groq pipeline test completed!")
        return True
        
    except Exception as e:
        print(f"Error testing pipeline: {e}")
        return False

if __name__ == "__main__":
    test_azure_groq_pipeline()
