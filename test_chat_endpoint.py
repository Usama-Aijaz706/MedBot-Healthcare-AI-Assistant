#!/usr/bin/env python3
"""
Test script to directly test the chat endpoint
"""

import requests
import json

def test_chat_endpoint():
    """Test the chat endpoint directly"""
    url = "http://localhost:8000/chat"
    
    # Test payload
    payload = {
        "user_question": "Tell me about microbiology and its importance, explain in detail",
        "chat_history": []
    }
    
    print("🧪 Testing chat endpoint directly...")
    print(f"📝 Query: {payload['user_question']}")
    print(f"🌐 URL: {url}")
    print("-" * 50)
    
    try:
        # Make the request
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Parse the response
            response_data = response.json()
            print(f"✅ Response received successfully!")
            print(f"📄 Response keys: {list(response_data.keys())}")
            
            # Show the actual response content
            if 'response' in response_data:
                print(f"📝 Response content (first 500 chars):")
                print("-" * 30)
                print(response_data['response'][:500])
                print("-" * 30)
                print(f"📏 Total response length: {len(response_data['response'])}")
            else:
                print("❌ No 'response' field in response data")
                print(f"🔍 Full response data: {json.dumps(response_data, indent=2)}")
            
            # Show sources if available
            if 'sources' in response_data:
                print(f"🔗 Sources count: {len(response_data['sources'])}")
                for i, source in enumerate(response_data['sources'][:3]):
                    print(f"  Source {i+1}: {source.get('source', 'Unknown')} (Relevance: {source.get('relevance_score', 0)})")
            
        else:
            print(f"❌ Error response: {response.status_code}")
            print(f"📄 Error content: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"📄 Raw response: {response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_chat_endpoint()
