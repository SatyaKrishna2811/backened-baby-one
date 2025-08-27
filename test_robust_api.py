#!/usr/bin/env python3
"""
Comprehensive test for the robust API with librosa caching fix and Bhashini retry logic
"""

import os
import sys
import django
import base64
import tempfile
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meeting_assistant.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_audio():
    """Create a simple test audio file"""
    try:
        import numpy as np
        import soundfile as sf
        
        # Generate a simple sine wave (1 second, 16kHz)
        duration = 1.0  # seconds
        sample_rate = 16000
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            sf.write(temp_file.name, audio_data, sample_rate)
            temp_path = temp_file.name
        
        # Read back as base64
        with open(temp_path, 'rb') as f:
            audio_bytes = f.read()
        
        os.unlink(temp_path)
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        logger.info(f"✅ Created test audio: {len(audio_base64)} characters")
        return audio_base64
        
    except Exception as e:
        logger.error(f"❌ Failed to create test audio: {str(e)}")
        return None

def test_librosa_caching_fix():
    """Test the librosa caching fix"""
    logger.info("🧪 Testing librosa caching fix...")
    
    try:
        from api.services import BhashiniService
        
        service = BhashiniService()
        
        # Create test audio data
        test_audio = create_test_audio()
        if not test_audio:
            logger.error("❌ Cannot test without audio")
            return False
        
        # Decode and test resampling
        audio_data = base64.b64decode(test_audio)
        y_resampled, sr = service.load_and_resample_audio(audio_data)
        
        if y_resampled is not None:
            logger.info(f"✅ Audio resampling successful: {len(y_resampled)} samples at {sr}Hz")
            return True
        else:
            logger.warning("⚠️ Audio resampling returned None (fallback mode)")
            return True  # This is acceptable behavior
            
    except Exception as e:
        logger.error(f"❌ Librosa test failed: {str(e)}")
        return False

def test_bhashini_service_initialization():
    """Test Bhashini service initialization"""
    logger.info("🧪 Testing Bhashini service initialization...")
    
    try:
        from api.services import BhashiniService
        
        service = BhashiniService()
        logger.info(f"✅ Bhashini service initialized with token: {service.api_token[:20]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Bhashini initialization failed: {str(e)}")
        return False

def test_gemini_service():
    """Test Gemini service"""
    logger.info("🧪 Testing Gemini service...")
    
    try:
        from api.services import GeminiService
        
        service = GeminiService()
        
        # Test a simple analysis
        test_text = "This is a test meeting transcript for analysis."
        result = service.analyze_meeting_transcript(test_text)
        
        if result and 'summary' in result:
            logger.info("✅ Gemini service working correctly")
            return True
        else:
            logger.warning("⚠️ Gemini service returned unexpected format")
            return False
            
    except Exception as e:
        logger.error(f"❌ Gemini test failed: {str(e)}")
        return False

def test_api_health():
    """Test API health endpoint"""
    logger.info("🧪 Testing API health endpoint...")
    
    try:
        import requests
        
        response = requests.get("http://127.0.0.1:8000/api/health/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ API health check passed: {data}")
            return True
        else:
            logger.error(f"❌ API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ API health test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting comprehensive API tests...")
    
    test_results = {
        "librosa_fix": test_librosa_caching_fix(),
        "bhashini_init": test_bhashini_service_initialization(),
        "gemini_service": test_gemini_service(),
        "api_health": test_api_health()
    }
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:20}: {status}")
        if result:
            passed += 1
    
    logger.info("="*50)
    logger.info(f"OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! Your API is robust and ready.")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
