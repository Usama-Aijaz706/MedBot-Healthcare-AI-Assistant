#!/usr/bin/env python3
"""
Test script for the article fetching system.
This script tests the core functionality without Streamlit dependencies.
"""

import os
import requests
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GROQ_API_KEY = os.getenv("PMID")
EUROPE_PMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
HEADERS = {"User-Agent": "MedBot-ArticleFetcher (medbot@example.com)"}

def test_europe_pmc_search():
    """Test Europe PMC search functionality."""
    print("Testing Europe PMC search...")
    
    try:
        from urllib.parse import quote
        
        query = "lung cancer treatment"
        search_url = f"{EUROPE_PMC_BASE}/search?query={quote(query)}&format=json&pageSize=10"
        
        print(f"Searching for: {query}")
        print(f"URL: {search_url}")
        
        response = requests.get(search_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("resultList", {}).get("result", [])
        
        print(f"Search successful! Found {len(results)} results")
        
        # Check for articles with both PMID and PMCID
        valid_articles = []
        for article in results:
            pmid = article.get("pmid")
            pmcid = article.get("pmcid")
            
            if pmid and pmcid:
                valid_articles.append({
                    "pmid": pmid,
                    "pmcid": pmcid,
                    "title": article.get("title", "No title"),
                    "authors": article.get("authorString", "Unknown"),
                    "journal": article.get("journalTitle", "Unknown"),
                    "year": article.get("pubYear", "Unknown")
                })
        
        print(f"Articles with both PMID and PMCID: {len(valid_articles)}")
        
        if valid_articles:
            print("\nSample articles:")
            for i, article in enumerate(valid_articles[:3], 1):
                print(f"  {i}. {article['title'][:60]}...")
                print(f"     PMID: {article['pmid']} | PMCID: {article['pmcid']}")
                print(f"     Authors: {article['authors']}")
                print(f"     Journal: {article['journal']} ({article['year']})")
                print()
            
            # Return the first valid article for further testing
            return valid_articles[0]
        
        return None
        
    except Exception as e:
        print(f"Europe PMC search failed: {str(e)}")
        return None

def test_groq_api():
    """Test Groq API functionality."""
    print("Testing Groq API...")
    
    if not GROQ_API_KEY:
        print("No Groq API key found (PMID environment variable)")
        return False
    
    try:
        from openai import OpenAI
        
        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        
        # Test query enhancement
        test_query = "cancer"
        enhancement_prompt = f"""You are a medical research specialist. A user has asked for articles about: "{test_query}"

Your task is to enhance their query with proper medical terminology.
Return ONLY the enhanced search query, no explanations.

Enhanced query:"""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a medical research specialist. Provide only enhanced search queries."},
                {"role": "user", "content": enhancement_prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        enhanced_query = response.choices[0].message.content.strip()
        print(f"Groq API working! Enhanced '{test_query}' to: '{enhanced_query}'")
        return True
        
    except Exception as e:
        print(f"Groq API test failed: {str(e)}")
        return False

def test_article_fetcher_integration():
    """Test integration with article_fetcher.py."""
    print("Testing article_fetcher integration...")
    
    try:
        # Try to import article_fetcher
        from article_fetcher import fetch_article
        
        print("article_fetcher imported successfully")
        
        # Test with a sample PMCID
        test_pmcid = "PMC1234567"  # This is just a test ID
        print(f"Article fetcher function available: {fetch_article.__name__}")
        
        return True
        
    except ImportError as e:
        print(f"article_fetcher not available: {e}")
        return False
    except Exception as e:
        print(f"article_fetcher test failed: {str(e)}")
        return False

def test_pdf_converter_integration():
    """Test integration with simple_html_to_pdf.py."""
    print("Testing PDF converter integration...")
    
    try:
        # Try to import the PDF converter class
        from simple_html_to_pdf import SimpleHTMLToPDFConverter
        
        print("PDF converter imported successfully")
        print(f"PDF converter class available: {SimpleHTMLToPDFConverter.__name__}")
        
        # Test creating an instance
        converter = SimpleHTMLToPDFConverter()
        print(f"PDF converter instance created successfully")
        
        return True
        
    except ImportError as e:
        print(f"PDF converter not available: {e}")
        return False
    except Exception as e:
        print(f"PDF converter test failed: {str(e)}")
        return False

def test_full_article_fetch_and_pdf_conversion():
    """Test the complete workflow: fetch article and convert to PDF."""
    print("Testing full article fetch and PDF conversion workflow...")
    
    try:
        # First, search for articles
        print("Step 1: Searching for articles...")
        article = test_europe_pmc_search()
        
        if not article:
            print("No valid articles found for testing")
            return False
        
        print(f"Using article: {article['title'][:50]}...")
        print(f"PMCID: {article['pmcid']}")
        
        # Step 2: Fetch the full article content
        print("\nStep 2: Fetching full article content...")
        from article_fetcher import fetch_article
        
        # Fetch the article - this returns the actual directory path where the article was saved
        article_dir = fetch_article(article['pmcid'])
        
        print(f"DEBUG: fetch_article returned: {article_dir}")
        print(f"DEBUG: article_dir type: {type(article_dir)}")
        
        if not article_dir:
            print("Failed to fetch article content - fetch_article returned None")
            return False
        
        # Convert to Path object if it's a string
        if isinstance(article_dir, str):
            article_dir = Path(article_dir)
        
        print(f"DEBUG: article_dir after conversion: {article_dir}")
        print(f"DEBUG: article_dir exists: {article_dir.exists()}")
        print(f"DEBUG: article_dir is_dir: {article_dir.is_dir()}")
        
        if not article_dir.exists():
            print(f"Failed to fetch article content - directory does not exist: {article_dir}")
            return False
        
        print(f"Article fetched successfully to: {article_dir}")
        
        # Check if markdown file was created
        md_files = list(article_dir.glob("*.md"))
        print(f"DEBUG: Found {len(md_files)} markdown files: {md_files}")
        
        if not md_files:
            print("No markdown file found in article directory")
            return False
        
        md_file = md_files[0]
        print(f"Markdown file found: {md_file}")
        print(f"DEBUG: md_file exists: {md_file.exists()}")
        print(f"DEBUG: md_file size: {md_file.stat().st_size if md_file.exists() else 'N/A'} bytes")
        
        # Step 3: Convert to HTML and open in browser
        print("\nStep 3: Converting to HTML and opening in browser...")
        from simple_html_to_pdf import SimpleHTMLToPDFConverter
        
        converter = SimpleHTMLToPDFConverter()
        html_file = converter.convert_markdown_to_pdf(md_file, f"test_article_{article['pmcid']}")
        
        if html_file and html_file.exists():
            print(f"HTML file created successfully: {html_file}")
            print(f"File size: {html_file.stat().st_size / 1024:.1f} KB")
            print("Browser should have opened automatically for PDF download")
            return True
        else:
            print("HTML conversion failed")
            return False
        
    except Exception as e:
        print(f"Full workflow test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Testing Article Fetching System")
    print("=" * 50)
    
    tests = [
        ("Europe PMC Search", test_europe_pmc_search),
        ("Groq API", test_groq_api),
        ("Article Fetcher Integration", test_article_fetcher_integration),
        ("PDF Converter Integration", test_pdf_converter_integration),
        ("Full Workflow Test", test_full_article_fetch_and_pdf_conversion)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! The article fetching system is ready.")
    else:
        print("Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    main()
