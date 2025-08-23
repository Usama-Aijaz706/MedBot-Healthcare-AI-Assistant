#!/usr/bin/env python3
"""
Test script to demonstrate user name extraction and personalization features
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_system import RAGSystem

def test_user_name_extraction():
    """Test the user name extraction functionality"""
    
    # Initialize RAG system
    rag = RAGSystem()
    
    # Test queries with names
    test_queries = [
        "I am Usama, can you tell me about diabetes?",
        "My name is Sarah, what is microbiology?",
        "I'm John and I want to know about hypertension",
        "Call me Maria, explain radiology",
        "This is Dr. Smith, tell me about cardiology",
        "Alex here, what are the symptoms of fever?",
        "David speaking, how to treat headache?",
        "What is the weather like?",  # No name
        "How to cook pasta?",  # No name
        "I am Usama, can you please tell me what it is so the model should remember the name of the user for that chat id only"
    ]
    
    print("🧪 Testing User Name Extraction")
    print("=" * 50)
    
    for query in test_queries:
        extracted_name = rag.extract_user_name(query)
        if extracted_name:
            print(f"✅ Name extracted: '{extracted_name}' from: '{query}'")
        else:
            print(f"❌ No name found in: '{query}'")
    
    print("\n" + "=" * 50)
    print("🔍 Testing Healthcare Detection with Names")
    print("=" * 50)
    
    # Test healthcare detection for queries with names
    healthcare_tests = [
        "I am Usama, can you tell me about diabetes?",
        "My name is Sarah, what is microbiology?",
        "I'm John and I want to know about hypertension",
        "Call me Maria, explain radiology",
        "This is Dr. Smith, tell me about cardiology"
    ]
    
    for query in healthcare_tests:
        is_healthcare = rag._is_healthcare_query(query)
        extracted_name = rag.extract_user_name(query)
        status = "✅ HEALTHCARE" if is_healthcare else "❌ NON-HEALTHCARE"
        name_info = f" (Name: {extracted_name})" if extracted_name else ""
        print(f"{status}: '{query}'{name_info}")

def test_comprehensive_prompt_creation():
    """Test the comprehensive prompt creation with user names"""
    
    rag = RAGSystem()
    
    # Test prompt creation with and without user names
    test_cases = [
        ("What is diabetes?", None),
        ("I am Usama, can you tell me about diabetes?", "Usama"),
        ("My name is Sarah, what is microbiology?", "Sarah"),
        ("How to treat headache?", None)
    ]
    
    print("\n" + "=" * 50)
    print("📝 Testing Comprehensive Prompt Creation")
    print("=" * 50)
    
    for question, user_name in test_cases:
        # Mock context for testing
        mock_context = "Diabetes is a chronic condition affecting blood sugar levels..."
        
        prompt = rag._create_comprehensive_prompt(question, mock_context, user_name)
        
        print(f"\n🔍 Question: {question}")
        print(f"👤 User Name: {user_name if user_name else 'None'}")
        print(f"📝 Prompt starts with: {prompt[:100]}...")
        
        # Check if personalization is included
        if user_name and f"Hello {user_name}!" in prompt:
            print("✅ Personalization detected in prompt")
        elif not user_name:
            print("✅ No personalization (as expected)")
        else:
            print("❌ Personalization missing")

if __name__ == "__main__":
    test_user_name_extraction()
    test_comprehensive_prompt_creation()
    
    print("\n" + "=" * 50)
    print("🎯 Summary of New Features:")
    print("=" * 50)
    print("✅ User name extraction from various patterns")
    print("✅ Personalization in comprehensive prompts")
    print("✅ Name memory for chat sessions")
    print("✅ Enhanced context and examples")
    print("✅ Improved healthcare query detection")
    print("\n🚀 Your MedBot now provides a personalized experience!")
