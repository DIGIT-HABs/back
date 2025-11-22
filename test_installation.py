"""
Test script to verify DIGIT-HAB CRM installation.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digit_hab_crm.settings')
django.setup()

def test_imports():
    """Test basic imports."""
    try:
        # Test Django apps
        from django.contrib.auth import get_user_model
        from apps.auth.models import Agency, UserProfile
        from apps.properties.models import Property, PropertyImage
        from apps.core.models import Configuration, ActivityLog
        
        print("✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database_connection():
    """Test database connection."""
    try:
        from django.db import connection
        
        # Test basic query
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_models():
    """Test model creation."""
    try:
        User = get_user_model()
        from apps.core.models import Configuration
        
        # Test model definitions
        print("✅ Model definitions valid")
        
        # Test basic model creation in test environment
        if os.environ.get('DJANGO_ENV') == 'test':
            config = Configuration.objects.create(
                key='test_key',
                value='test_value',
                description='Test configuration'
            )
            print("✅ Model creation successful")
            config.delete()
        
        return True
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

def test_settings():
    """Test Django settings."""
    try:
        from django.conf import settings
        
        # Check required settings
        required_settings = [
            'SECRET_KEY',
            'DATABASES',
            'INSTALLED_APPS',
            'REST_FRAMEWORK',
        ]
        
        for setting in required_settings:
            if not hasattr(settings, setting):
                raise Exception(f"Missing setting: {setting}")
        
        print("✅ Settings configuration valid")
        return True
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def test_apps():
    """Test Django apps."""
    try:
        from django.apps import apps
        
        # Check app configuration
        app_configs = [
            'apps.auth',
            'apps.properties', 
            'apps.core',
        ]
        
        for app in app_configs:
            app_config = apps.get_app_config(app.split('.')[-1])
            print(f"✅ App {app} configured: {app_config.verbose_name}")
        
        return True
    except Exception as e:
        print(f"❌ Apps error: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing DIGIT-HAB CRM Installation")
    print("=" * 50)
    
    tests = [
        ("Import Modules", test_imports),
        ("Database Connection", test_database_connection),
        ("Settings Configuration", test_settings),
        ("Django Apps", test_apps),
        ("Model Definitions", test_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print("   Test failed!")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! DIGIT-HAB CRM is ready for development.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return 1

if __name__ == '__main__':
    sys.exit(main())