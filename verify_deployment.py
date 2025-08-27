#!/usr/bin/env python3
"""
Render Deployment Verification Script
Tests all endpoints and configurations for production readiness.
"""

import os
import sys
import requests
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class RenderDeploymentChecker:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.getenv('RENDER_URL', 'http://localhost:8000')
        self.results = []
        
    def log_result(self, test_name, status, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details or {}
        }
        self.results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message}")
        
        if details and status != "PASS":
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/health/", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_result(
                        "Health Check", 
                        "PASS", 
                        f"Service is healthy (Response time: {response.elapsed.total_seconds():.2f}s)",
                        {"response": data}
                    )
                    return True
                else:
                    self.log_result(
                        "Health Check", 
                        "FAIL", 
                        "Service responded but reports unhealthy status",
                        {"response": data}
                    )
            else:
                self.log_result(
                    "Health Check", 
                    "FAIL", 
                    f"HTTP {response.status_code}",
                    {"response": response.text[:200]}
                )
        except requests.exceptions.RequestException as e:
            self.log_result(
                "Health Check", 
                "FAIL", 
                "Connection failed",
                {"error": str(e)}
            )
        return False
    
    def test_cors_configuration(self):
        """Test CORS headers"""
        try:
            # Test OPTIONS request
            response = requests.options(
                f"{self.base_url}/api/health/",
                headers={'Origin': 'https://your-frontend.vercel.app'},
                timeout=10
            )
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            }
            
            if any(cors_headers.values()):
                self.log_result(
                    "CORS Configuration", 
                    "PASS", 
                    "CORS headers are configured",
                    cors_headers
                )
                return True
            else:
                self.log_result(
                    "CORS Configuration", 
                    "WARN", 
                    "No CORS headers found",
                    {"headers": dict(response.headers)}
                )
        except Exception as e:
            self.log_result(
                "CORS Configuration", 
                "FAIL", 
                "Failed to test CORS",
                {"error": str(e)}
            )
        return False
    
    def test_environment_variables(self):
        """Check if required environment variables are configured"""
        required_vars = [
            'DJANGO_SECRET_KEY',
            'BHASHINI_API_KEY', 
            'GEMINI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if not missing_vars:
            self.log_result(
                "Environment Variables", 
                "PASS", 
                "All required environment variables are set"
            )
            return True
        else:
            self.log_result(
                "Environment Variables", 
                "FAIL", 
                f"Missing environment variables: {', '.join(missing_vars)}",
                {"missing": missing_vars}
            )
        return False
    
    def test_static_files(self):
        """Test static file serving"""
        try:
            response = requests.get(f"{self.base_url}/static/admin/css/base.css", timeout=10)
            
            if response.status_code == 200:
                self.log_result(
                    "Static Files", 
                    "PASS", 
                    "Static files are being served correctly"
                )
                return True
            else:
                self.log_result(
                    "Static Files", 
                    "WARN", 
                    f"Static files may not be configured (HTTP {response.status_code})"
                )
        except Exception as e:
            self.log_result(
                "Static Files", 
                "WARN", 
                "Could not test static files",
                {"error": str(e)}
            )
        return False
    
    def test_process_audio_endpoint(self):
        """Test the main audio processing endpoint"""
        try:
            # Test with empty POST (should return 400 with proper error)
            response = requests.post(
                f"{self.base_url}/api/process-audio/",
                timeout=30
            )
            
            if response.status_code == 400:
                data = response.json()
                if 'error' in data:
                    self.log_result(
                        "Process Audio Endpoint", 
                        "PASS", 
                        "Endpoint is accessible and handles errors properly",
                        {"error_response": data}
                    )
                    return True
            
            self.log_result(
                "Process Audio Endpoint", 
                "WARN", 
                f"Unexpected response (HTTP {response.status_code})",
                {"response": response.text[:200]}
            )
        except Exception as e:
            self.log_result(
                "Process Audio Endpoint", 
                "FAIL", 
                "Endpoint is not accessible",
                {"error": str(e)}
            )
        return False
    
    def check_deployment_files(self):
        """Check if all deployment files are present"""
        required_files = [
            'requirements.txt',
            'build.sh',
            'render.yaml',
            'manage.py',
            'meeting_assistant/wsgi.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (project_root / file_path).exists():
                missing_files.append(file_path)
        
        if not missing_files:
            self.log_result(
                "Deployment Files", 
                "PASS", 
                "All required deployment files are present"
            )
            return True
        else:
            self.log_result(
                "Deployment Files", 
                "FAIL", 
                f"Missing deployment files: {', '.join(missing_files)}",
                {"missing": missing_files}
            )
        return False
    
    def run_all_tests(self):
        """Run all deployment verification tests"""
        print("🚀 Starting Render Deployment Verification...")
        print(f"📍 Testing URL: {self.base_url}")
        print("=" * 60)
        
        # Check deployment files first
        self.check_deployment_files()
        
        # Check environment variables
        self.test_environment_variables()
        
        # Test endpoints (only if base_url is accessible)
        if self.base_url.startswith('http'):
            self.test_health_endpoint()
            self.test_cors_configuration()
            self.test_static_files()
            self.test_process_audio_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT VERIFICATION SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL') 
        warned = sum(1 for r in self.results if r['status'] == 'WARN')
        total = len(self.results)
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warned}")
        print(f"📋 Total: {total}")
        
        if failed == 0:
            print("\n🎉 Your backend is ready for Render deployment!")
            print("\nNext steps:")
            print("1. Push your code to GitHub")
            print("2. Connect your repository to Render")
            print("3. Set environment variables in Render dashboard")
            print("4. Deploy and test the live URL")
        else:
            print(f"\n⚠️  Please fix {failed} failed tests before deploying")
        
        return failed == 0

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify Render deployment readiness')
    parser.add_argument('--url', help='Base URL to test (default: http://localhost:8000)')
    args = parser.parse_args()
    
    checker = RenderDeploymentChecker(args.url)
    success = checker.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
