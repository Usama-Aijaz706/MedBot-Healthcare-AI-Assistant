#!/usr/bin/env python3
"""
Test script for healthcare query detection with chat history context and follow-up validation.
This will help verify that follow-up questions are properly handled with context.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_system import RAGSystem

def test_healthcare_detection():
    """Test the healthcare query detection with various scenarios."""
    
    # Initialize RAG system
    rag_system = RAGSystem()
    
    print("🧪 Testing Healthcare Query Detection with Chat History & Follow-up Validation")
    print("=" * 80)
    
    # Test 1: Initial medical query
    print("\n📋 Test 1: Initial Medical Query")
    print("Query: 'Tell me about microbiology and its importance'")
    
    # Simulate chat history (empty for first query)
    chat_history = []
    
    is_medical = rag_system._is_healthcare_query("Tell me about microbiology and its importance", chat_history)
    print(f"Result: {'✅ Medical' if is_medical else '❌ Non-medical'}")
    
    # Test 2: Follow-up question in medical context
    print("\n📋 Test 2: Follow-up Question in Medical Context")
    print("Query: 'please explain in detail'")
    
    # Simulate chat history with previous medical conversation
    chat_history = [
        {
            'role': 'user',
            'content': 'Tell me about microbiology and its importance'
        },
        {
            'role': 'assistant',
            'content': 'Microbiology is the study of microorganisms including bacteria, viruses, fungi, protozoa, and algae. It plays a critical role in healthcare, industry, and environmental science...'
        }
    ]
    
    is_medical = rag_system._is_healthcare_query("please explain in detail", chat_history)
    print(f"Result: {'✅ Medical' if is_medical else '❌ Non-medical'}")
    
    # Test 3: Follow-up validation
    print("\n📋 Test 3: Follow-up Validation")
    print("Query: 'explain in detail'")
    
    validation = rag_system._validate_follow_up_context("explain in detail", chat_history)
    print(f"Valid: {'✅ Yes' if validation['valid'] else '❌ No'}")
    if validation['valid']:
        print(f"Type: {validation['type']}")
        print(f"Context: {validation['context']}")
    else:
        print(f"Error: {validation['error']}")
    
    # Test 4: Follow-up without medical context
    print("\n📋 Test 4: Follow-up Without Medical Context")
    print("Query: 'explain in detail'")
    
    # Chat history with non-medical conversation
    non_medical_history = [
        {
            'role': 'user',
            'content': 'What is the weather like today?'
        },
        {
            'role': 'assistant',
            'content': 'I cannot provide weather information. I am a medical AI assistant.'
        }
    ]
    
    validation = rag_system._validate_follow_up_context("explain in detail", non_medical_history)
    print(f"Valid: {'✅ Yes' if validation['valid'] else '❌ No'}")
    if validation['valid']:
        print(f"Type: {validation['type']}")
        print(f"Context: {validation['context']}")
    else:
        print(f"Error: {validation['error']}")
    
    # Test 5: Empty chat history
    print("\n📋 Test 5: Empty Chat History")
    print("Query: 'explain in detail'")
    
    validation = rag_system._validate_follow_up_context("explain in detail", [])
    print(f"Valid: {'✅ Yes' if validation['valid'] else '❌ No'}")
    if validation['valid']:
        print(f"Type: {validation['type']}")
        print(f"Context: {validation['context']}")
    else:
        print(f"Error: {validation['error']}")
    
    # Test 6: Legitimate medical follow-up
    print("\n📋 Test 6: Legitimate Medical Follow-up")
    print("Query: 'Can you tell me more about bacteria?'")
    
    validation = rag_system._validate_follow_up_context("Can you tell me more about bacteria?", chat_history)
    print(f"Valid: {'✅ Yes' if validation['valid'] else '❌ No'}")
    if validation['valid']:
        print(f"Type: {validation['type']}")
        print(f"Context: {validation['context']}")
    else:
        print(f"Error: {validation['error']}")
    
    print("\n" + "=" * 80)
    print("🎯 Test Summary:")
    print("- Test 1 should be ✅ Medical (initial microbiology query)")
    print("- Test 2 should be ✅ Medical (follow-up in medical context)")
    print("- Test 3 should be ✅ Valid (follow-up with medical context)")
    print("- Test 4 should be ❌ Invalid (follow-up without medical context)")
    print("- Test 5 should be ❌ Invalid (empty chat history)")
    print("- Test 6 should be ✅ Valid (legitimate medical follow-up)")

if __name__ == "__main__":
    test_healthcare_detection()
