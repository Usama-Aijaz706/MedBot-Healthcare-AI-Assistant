#!/usr/bin/env python3
"""
Test script to verify healthcare query detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_system import RAGSystem

def test_healthcare_detection():
    """Test the healthcare query detection with various queries"""
    
    # Initialize RAG system
    rag = RAGSystem()
    
    # Test queries
    test_queries = [
        "microbiology",
        "micro biology", 
        "micro-biology",
        "what is microbiology",
        "radiology",
        "who is the prime minister of pakistan",  # Should be rejected
        "what is diabetes",
        "how to treat headache",
        "symptoms of fever",
        "biology",
        "immunology",
        "pathology",
        "cardiology",
        "neurology",
        "dermatology",
        "anatomy",
        "physiology",
        "biochemistry",
        "genetics",
        "pharmacology",
        "epidemiology",
        "virology",
        "bacteriology",
        "parasitology",
        "mycology",
        "what is the weather like",  # Should be rejected
        "how to cook pasta",  # Should be rejected
        "what is the capital of france",  # Should be rejected
        "what is cancer",  # Should be detected
        "what is hypertension",  # Should be detected
        "what is arthritis",  # Should be detected
        "what is asthma"  # Should be detected
    ]
    
    print("🧪 Testing Healthcare Query Detection")
    print("=" * 50)
    
    healthcare_count = 0
    non_healthcare_count = 0
    
    for query in test_queries:
        is_healthcare = rag._is_healthcare_query(query)
        status = "✅ HEALTHCARE" if is_healthcare else "❌ NON-HEALTHCARE"
        
        if is_healthcare:
            healthcare_count += 1
        else:
            non_healthcare_count += 1
            
        print(f"{status}: '{query}'")
    
    print("\n" + "=" * 50)
    print(f"📊 Results:")
    print(f"   Healthcare queries: {healthcare_count}")
    print(f"   Non-healthcare queries: {non_healthcare_count}")
    print(f"   Total queries: {len(test_queries)}")
    
    # Specific test for microbiology variations
    print("\n🔬 Testing Microbiology Variations:")
    micro_queries = ["microbiology", "micro biology", "micro-biology", "micro biology"]
    for query in micro_queries:
        is_healthcare = rag._is_healthcare_query(query)
        status = "✅ HEALTHCARE" if is_healthcare else "❌ NON-HEALTHCARE"
        print(f"{status}: '{query}'")
    
    # Test the problematic "what is" patterns
    print("\n🔍 Testing 'What Is' Pattern Detection:")
    what_is_tests = [
        "what is the weather like",  # Should be rejected
        "what is the capital of france",  # Should be rejected
        "what is microbiology",  # Should be detected
        "what is diabetes",  # Should be detected
        "what is cancer",  # Should be detected
        "what is hypertension"  # Should be detected
    ]
    for query in what_is_tests:
        is_healthcare = rag._is_healthcare_query(query)
        status = "✅ HEALTHCARE" if is_healthcare else "❌ NON-HEALTHCARE"
        print(f"{status}: '{query}'")

if __name__ == "__main__":
    test_healthcare_detection()
