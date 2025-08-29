#!/usr/bin/env python3
"""
Test script to verify Europe PMC client functionality
"""

from pmid import EuropePMCClient

def test_europe_pmc_client():
    """Test the Europe PMC client with a known PMID"""
    
    print("🧪 Testing Europe PMC Client")
    print("=" * 50)
    
    # Create client
    client = EuropePMCClient()
    print("✅ Client created successfully")
    
    # Test PMID that was used in article_fetcher.py
    test_pmid = "55556666"
    print(f"\n🔍 Testing PMID: {test_pmid}")
    
    # Fetch article
    article = client.fetch_article_by_pmid(test_pmid)
    
    if article:
        print("✅ Article fetched successfully!")
        print(f"📝 Title: {article.get('title', 'Not found')}")
        print(f"👥 Authors: {article.get('authorString', 'Not found')}")
        print(f"📚 Journal: {article.get('journalTitle', 'Not found')}")
        print(f"📅 Year: {article.get('pubYear', 'Not found')}")
        print(f"📄 Abstract: {article.get('abstractText', 'Not found')[:100]}...")
        print(f"🆔 PMCID: {article.get('pmcid', 'Not found')}")
    else:
        print("❌ Failed to fetch article")
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    test_europe_pmc_client()
