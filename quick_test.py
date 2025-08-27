"""
Quick API Key Verification Script
Tests Bhashini and Gemini API keys directly
"""
import os
import requests
import json
from datetime import datetime

# Your API keys
BHASHINI_TOKEN = "ujzb4jidEwJo1U-IDxGr2iMkRChAw8qrKcKUQsCA1RSOC2rt6ITU3TihElxkmoHA"
GEMINI_API_KEY = "AIzaSyDQq1B4ZAsHIwVvK49Sl99up4H4JA0GxGQ"

def test_bhashini_api():
    """Test Bhashini API directly"""
    print("Testing Bhashini API...")
    try:
        # Test language detection endpoint
        url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
        headers = {"Authorization": BHASHINI_TOKEN}
        
        # Simple language detection payload
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "audio-lang-detection",
                    "config": {
                        "serviceId": "bhashini/iitmandi/audio-lang-detection/gpu"
                    }
                }
            ],
            "inputData": {"audio": [{"audioContent": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="}]}
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("SUCCESS: Bhashini API is working")
            print(f"  Response: {response.status_code}")
            return True
        else:
            print(f"ERROR: Bhashini API failed - Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Bhashini API test failed: {str(e)}")
        return False

def test_gemini_api():
    """Test Gemini API directly"""
    print("\nTesting Gemini API...")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "Hello, this is a test. Please respond with 'API Working'"
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data:
                print("SUCCESS: Gemini API is working")
                print(f"  Response: {response.status_code}")
                return True
            else:
                print("ERROR: Gemini API returned unexpected format")
                return False
        else:
            print(f"ERROR: Gemini API failed - Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Gemini API test failed: {str(e)}")
        return False

def main():
    """Run API key tests"""
    print("AI Meeting Assistant - API Key Verification")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    bhashini_ok = test_bhashini_api()
    gemini_ok = test_gemini_api()
    
    print("\n" + "=" * 50)
    print("API Key Test Results:")
    print(f"  Bhashini: {'WORKING' if bhashini_ok else 'FAILED'}")
    print(f"  Gemini: {'WORKING' if gemini_ok else 'FAILED'}")
    
    if bhashini_ok and gemini_ok:
        print("\nSUCCESS: Both API keys are working correctly!")
        print("Your backend is ready for production deployment.")
    else:
        print("\nWARNING: Some API keys are not working.")
    
    return bhashini_ok and gemini_ok

if __name__ == "__main__":
    success = main()
