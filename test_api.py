"""
Simple API endpoint test for production readiness
"""
import requests
import json
import base64
import time

def test_health_endpoint():
    """Test the health endpoint"""
    print("Testing Health Endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8000/api/health/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Health endpoint working - Status: {data.get('status')}")
            return True
        else:
            print(f"ERROR: Health endpoint failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Health endpoint test failed: {str(e)}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("Testing Root Endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Root endpoint working - Service: {data.get('service')}")
            return True
        else:
            print(f"ERROR: Root endpoint failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Root endpoint test failed: {str(e)}")
        return False

def test_supported_languages():
    """Test supported languages endpoint"""
    print("Testing Supported Languages Endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8000/api/supported-languages/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Supported languages endpoint working - {data.get('count')} languages")
            return True
        else:
            print(f"ERROR: Supported languages endpoint failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"ERROR: Supported languages test failed: {str(e)}")
        return False

def test_audio_processing_endpoint():
    """Test audio processing endpoint with sample data"""
    print("Testing Audio Processing Endpoint...")
    try:
        # Create simple test audio data (base64 encoded silence)
        import numpy as np
        import soundfile as sf
        import tempfile
        import os
        
        # Create 1 second of silence
        sample_rate = 16000
        duration = 1
        samples = int(duration * sample_rate)
        audio_data = np.zeros(samples, dtype=np.float32)
        
        # Save and encode
        temp_path = f"api_test_audio_{int(time.time())}.wav"
        try:
            sf.write(temp_path, audio_data, sample_rate)
            with open(temp_path, 'rb') as f:
                audio_bytes = f.read()
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        # Test JSON payload
        payload = {
            "audioData": audio_b64,
            "sourceLanguage": "hi",
            "targetLanguage": "en",
            "audioFormat": "wav",
            "preMeetingNotes": "Test meeting notes"
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/api/process-audio/", 
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("SUCCESS: Audio processing endpoint working")
                print(f"  - Transcript available: {'transcript' in data.get('data', {})}")
                print(f"  - Translation available: {'translation' in data.get('data', {})}")
                print(f"  - Summary available: {'summary' in data.get('data', {})}")
                return True
            else:
                print(f"ERROR: Audio processing failed - {data.get('error')}")
                return False
        else:
            print(f"ERROR: Audio processing endpoint failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Audio processing test failed: {str(e)}")
        return False

def main():
    """Run API tests"""
    print("AI Meeting Assistant Backend - API Tests")
    print("=" * 50)
    print("NOTE: Make sure the Django server is running on http://127.0.0.1:8000/")
    print()
    
    tests = [
        test_root_endpoint,
        test_health_endpoint,
        test_supported_languages,
        test_audio_processing_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"API Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All API endpoints are working correctly!")
        return True
    else:
        print("WARNING: Some API tests failed. Check the server logs.")
        return False

if __name__ == "__main__":
    success = main()
