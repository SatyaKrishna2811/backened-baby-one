#!/usr/bin/env python3
"""
Test production API keys for Render deployment readiness
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bhashini_api():
    """Test Bhashini API with production credentials"""
    print("🔑 Testing Bhashini API...")
    
    # Get credentials
    auth_token = os.getenv('BHASHINI_AUTH_TOKEN') or os.getenv('BHASHINI_API_KEY')
    user_id = os.getenv('BHASHINI_USER_ID')
    ulca_key = os.getenv('ULCA_API_KEY')
    
    print(f"   Auth Token: {auth_token[:20] if auth_token else 'NOT SET'}...")
    print(f"   User ID: {user_id if user_id else 'NOT SET'}")
    print(f"   ULCA Key: {ulca_key[:20] if ulca_key else 'NOT SET'}...")
    
    if not auth_token:
        print("❌ BHASHINI_AUTH_TOKEN not found")
        return False
    
    # Test with pipeline configuration request
    url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    
    headers = {
        'Accept': '*/*',
        'User-Agent': 'Thunder Client (https://www.thunderclient.com)',
        'Authorization': f'{auth_token}',
        'Content-Type': 'application/json'
    }
    
    # Minimal pipeline request for testing
    payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {
                        "sourceLanguage": "hi"
                    }
                }
            }
        ],
        "inputData": {
            "audio": [
                {
                    "audioUri": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAgD4AAAB9AAACABAAZGF0YQAAAAA="
                }
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Bhashini API: WORKING")
            return True
        elif response.status_code == 401:
            print("❌ Bhashini API: Authentication failed - check token")
        elif response.status_code == 500:
            print("⚠️  Bhashini API: Server error - may be temporary")
        else:
            print(f"⚠️  Bhashini API: Unexpected status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        
        return False
        
    except Exception as e:
        print(f"❌ Bhashini API: Connection failed - {str(e)}")
        return False

def test_gemini_api():
    """Test Gemini API with production credentials"""
    print("\n🔑 Testing Gemini API...")
    
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"   API Key: {api_key[:20] if api_key else 'NOT SET'}...")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return False
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Test message"
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Gemini API: WORKING")
            return True
        elif response.status_code == 401:
            print("❌ Gemini API: Authentication failed - check API key")
        elif response.status_code == 403:
            print("❌ Gemini API: Forbidden - check API key permissions")
        else:
            print(f"⚠️  Gemini API: Unexpected status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        
        return False
        
    except Exception as e:
        print(f"❌ Gemini API: Connection failed - {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Production API Keys for Render Deployment")
    print("=" * 60)
    
    bhashini_ok = test_bhashini_api()
    gemini_ok = test_gemini_api()
    
    print("\n" + "=" * 60)
    print("📊 PRODUCTION API KEY TEST SUMMARY")
    print("=" * 60)
    
    if bhashini_ok and gemini_ok:
        print("🎉 All API keys are working! Ready for Render deployment.")
        print("\nNext steps:")
        print("1. Push code to GitHub")
        print("2. Create new web service on Render.com")
        print("3. Connect GitHub repository")
        print("4. Use the environment variables from render.yaml")
        print("5. Deploy and test live endpoints")
        return True
    else:
        print("⚠️  Some API keys need attention before deployment")
        if not bhashini_ok:
            print("   - Fix Bhashini credentials")
        if not gemini_ok:
            print("   - Fix Gemini credentials")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
