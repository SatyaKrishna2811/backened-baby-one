#!/usr/bin/env python3
"""
Test script for production API endpoint
"""
import requests
import json
import base64
import io
import wave

def create_test_audio():
    """Create a simple test audio file in base64"""
    # Create a simple 1-second audio file
    sample_rate = 16000
    duration = 1  # 1 second
    samples = [0] * (sample_rate * duration)  # Silent audio
    
    # Create WAV file in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b'\x00' * (sample_rate * duration * 2))
    
    buffer.seek(0)
    audio_data = buffer.read()
    return base64.b64encode(audio_data).decode('utf-8')

def create_test_audio_bytes():
    """Create a simple test audio file as bytes"""
    # Create a simple 1-second audio file
    sample_rate = 16000
    duration = 1  # 1 second
    
    # Create WAV file in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b'\x00' * (sample_rate * duration * 2))
    
    buffer.seek(0)
    return buffer.read()

def test_production_api():
    """Test the production API endpoint"""
    print("Testing Production API")
    print("======================")
    
    # Production URL
    base_url = "https://meeting-mind-backened-baby-one.onrender.com"
    
    # Test health endpoint first
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health/", timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test main endpoint
    print("\n2. Testing process-audio endpoint...")
    try:
        # Create test audio file
        audio_data = create_test_audio_bytes()
        
        # Prepare multipart form data
        files = {
            'audio': ('test_audio.wav', audio_data, 'audio/wav')
        }
        
        data = {
            'source_language': 'hi',  # Hindi
            'target_language': 'en'   # English
        }
        
        print(f"   Sending multipart request with {len(audio_data)} bytes of audio data...")
        response = requests.post(
            f"{base_url}/api/process-audio/", 
            files=files,
            data=data,
            timeout=120
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Success! Response keys: {list(result.keys())}")
            print(f"   Duration: {result.get('duration', 'N/A')}")
            print(f"   Success flag: {result.get('success', 'N/A')}")
            if 'data' in result:
                data = result['data']
                print(f"   Data keys: {list(data.keys())}")
                if 'transcription' in data:
                    print(f"   Transcription: {data['transcription'][:100]}...")
                if 'summary' in data:
                    print(f"   Summary: {data['summary'][:100]}...")
        else:
            print(f"   Error response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_production_api()
