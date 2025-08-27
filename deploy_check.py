#!/usr/bin/env python3
"""
Production deployment script for the AI Meeting Assistant Backend
Ensures all services are configured and ready for deployment
"""
import os
import django
import sys
from pathlib import Path

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meeting_assistant.settings')
django.setup()

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("Checking Environment Variables...")
    
    required_vars = [
        'DJANGO_SECRET_KEY',
        'BHASHINI_AUTH_TOKEN',
        'GEMINI_API_KEY'
    ]
    
    optional_vars = [
        'DEBUG',
        'FRONTEND_URL'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"  SUCCESS: {var} is set")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  INFO: {var} = {value}")
        else:
            print(f"  INFO: {var} not set (using default)")
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    return True

def run_migrations():
    """Run Django migrations"""
    print("\nRunning Django Migrations...")
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate'])
        print("SUCCESS: Migrations completed")
        return True
    except Exception as e:
        print(f"ERROR: Migration failed: {str(e)}")
        return False

def test_services():
    """Test all services"""
    print("\nTesting Services...")
    try:
        from api.services import get_service_health
        health = get_service_health()
        
        if health['status'] == 'healthy':
            print("SUCCESS: All services are healthy")
            for service, status in health['services'].items():
                print(f"  - {service}: {status}")
            return True
        else:
            print(f"ERROR: Services not healthy: {health['status']}")
            return False
            
    except Exception as e:
        print(f"ERROR: Service test failed: {str(e)}")
        return False

def collect_static():
    """Collect static files for production"""
    print("\nCollecting Static Files...")
    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("SUCCESS: Static files collected")
        return True
    except Exception as e:
        print(f"WARNING: Static file collection failed: {str(e)}")
        # This is not critical for API-only backend
        return True

def main():
    """Run all deployment checks"""
    print("AI Meeting Assistant Backend - Deployment Check")
    print("=" * 60)
    
    checks = [
        check_environment_variables,
        run_migrations,
        test_services,
        collect_static
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        if check():
            passed += 1
        print()  # Add spacing
    
    print("=" * 60)
    print(f"Deployment Check Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("SUCCESS: Backend is ready for deployment!")
        return True
    else:
        print("ERROR: Some deployment checks failed. Review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
