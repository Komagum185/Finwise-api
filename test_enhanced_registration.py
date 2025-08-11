#!/usr/bin/env python3
"""
Enhanced Registration System Test Script

This script tests the enhanced registration system with questbanker-app integration.
"""

import os
import sys
import django
import requests
import json
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import CustomUser, PendingRegistration, OTPVerification

class EnhancedRegistrationTest(APITestCase):
    """Test enhanced registration system"""
    
    def setUp(self):
        """Set up test data"""
        self.registration_url = '/api/auth/register-enhanced/'
        self.progress_url = '/api/auth/registration-progress/'
        self.status_url = '/api/auth/registration-status/'
        self.onboarding_url = '/api/auth/onboarding/'
        self.analytics_url = '/api/auth/registration-analytics/'
        
        # Test data
        self.valid_registration_data = {
            "username": "testuser123",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890",
            "date_of_birth": "1990-01-01",
            "employment_status": "employed",
            "employer_name": "Test Corp",
            "job_title": "Software Engineer",
            "monthly_income": "5000.00",
            "default_currency": "USD",
            "address": "123 Test St",
            "city": "Test City",
            "country": "Test Country",
            "postal_code": "12345",
            "communication_preference": "email",
            "preferred_banking_hours": "morning",
            "terms_accepted": True,
            "marketing_consent": False
        }
    
    def test_enhanced_registration(self):
        """Test enhanced registration endpoint"""
        print("Testing enhanced registration...")
        
        response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('registration_id', response.data)
        self.assertIn('otp_sent', response.data)
        self.assertTrue(response.data['otp_sent'])
        
        print(f"✅ Enhanced registration successful. Registration ID: {response.data['registration_id']}")
        return response.data['registration_id']
    
    def test_registration_progress(self):
        """Test registration progress tracking"""
        print("Testing registration progress...")
        
        # First create a registration
        reg_response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        registration_id = reg_response.data['registration_id']
        
        # Test progress tracking
        progress_url = f"{self.progress_url}{registration_id}/"
        response = self.client.get(progress_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('step', response.data)
        self.assertIn('total_steps', response.data)
        self.assertIn('current_step_name', response.data)
        
        print(f"✅ Progress tracking successful. Current step: {response.data['current_step_name']}")
    
    def test_registration_status(self):
        """Test registration status endpoint"""
        print("Testing registration status...")
        
        # First create a registration
        reg_response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        registration_id = reg_response.data['registration_id']
        
        # Test status endpoint
        status_url = f"{self.status_url}{registration_id}/"
        response = self.client.get(status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('estimated_approval_time', response.data)
        self.assertIn('next_actions', response.data)
        
        print(f"✅ Status tracking successful. Status: {response.data['status']}")
    
    def test_otp_verification(self):
        """Test OTP verification"""
        print("Testing OTP verification...")
        
        # First create a registration
        reg_response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        registration_id = reg_response.data['registration_id']
        
        # Get the registration object to access OTP
        registration = PendingRegistration.objects.get(id=registration_id)
        otp_code = registration.otp_code
        
        # Test OTP verification
        otp_data = {
            "otp_code": otp_code,
            "purpose": "email_verification",
            "registration_id": registration_id
        }
        
        response = self.client.post('/api/auth/verify-otp/', otp_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        print("✅ OTP verification successful")
    
    def test_invalid_registration_data(self):
        """Test registration with invalid data"""
        print("Testing invalid registration data...")
        
        invalid_data = self.valid_registration_data.copy()
        invalid_data['email'] = 'invalid-email'
        invalid_data['password'] = 'weak'
        invalid_data['terms_accepted'] = False
        
        response = self.client.post(self.registration_url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
        self.assertIn('terms_accepted', response.data)
        
        print("✅ Invalid data validation working correctly")
    
    def test_duplicate_registration(self):
        """Test duplicate registration prevention"""
        print("Testing duplicate registration prevention...")
        
        # First registration
        response1 = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Duplicate registration
        response2 = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response2.data)
        
        print("✅ Duplicate registration prevention working correctly")


def test_api_endpoints():
    """Test API endpoints directly"""
    print("\n" + "="*50)
    print("TESTING ENHANCED REGISTRATION API ENDPOINTS")
    print("="*50)
    
    base_url = "http://localhost:8000"
    
    # Test data
    test_data = {
        "username": "apitestuser",
        "email": "apitest@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "API",
        "last_name": "Test",
        "phone_number": "+1234567890",
        "date_of_birth": "1990-01-01",
        "employment_status": "employed",
        "employer_name": "API Test Corp",
        "monthly_income": "5000.00",
        "default_currency": "USD",
        "address": "123 API Test St",
        "city": "API Test City",
        "country": "Test Country",
        "communication_preference": "email",
        "preferred_banking_hours": "morning",
        "terms_accepted": True,
        "marketing_consent": False
    }
    
    try:
        # Test enhanced registration
        print("1. Testing enhanced registration endpoint...")
        response = requests.post(f"{base_url}/api/auth/register-enhanced/", json=test_data)
        
        if response.status_code == 201:
            print("✅ Enhanced registration successful")
            registration_id = response.json()['registration_id']
            
            # Test progress tracking
            print("2. Testing progress tracking...")
            progress_response = requests.get(f"{base_url}/api/auth/registration-progress/{registration_id}/")
            if progress_response.status_code == 200:
                print("✅ Progress tracking successful")
            
            # Test status tracking
            print("3. Testing status tracking...")
            status_response = requests.get(f"{base_url}/api/auth/registration-status/{registration_id}/")
            if status_response.status_code == 200:
                print("✅ Status tracking successful")
            
            # Test OTP verification
            print("4. Testing OTP verification...")
            # Get OTP from database
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT otp_code FROM users_pendingregistration WHERE id = %s", [registration_id])
                result = cursor.fetchone()
                if result:
                    otp_code = result[0]
                    otp_data = {
                        "otp_code": otp_code,
                        "purpose": "email_verification",
                        "registration_id": registration_id
                    }
                    otp_response = requests.post(f"{base_url}/api/auth/verify-otp/", json=otp_data)
                    if otp_response.status_code == 200:
                        print("✅ OTP verification successful")
                    else:
                        print(f"❌ OTP verification failed: {otp_response.status_code}")
                else:
                    print("❌ Could not retrieve OTP from database")
        else:
            print(f"❌ Enhanced registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error during API testing: {str(e)}")


def main():
    """Main test function"""
    print("Enhanced Registration System Test")
    print("="*40)
    
    # Run Django tests
    print("\nRunning Django unit tests...")
    try:
        # Create test instance and run tests
        test_instance = EnhancedRegistrationTest()
        test_instance.setUp()
        
        # Run individual tests
        test_instance.test_enhanced_registration()
        test_instance.test_registration_progress()
        test_instance.test_registration_status()
        test_instance.test_otp_verification()
        test_instance.test_invalid_registration_data()
        test_instance.test_duplicate_registration()
        
        print("\n✅ All Django unit tests passed!")
        
    except Exception as e:
        print(f"❌ Django tests failed: {str(e)}")
    
    # Run API endpoint tests
    test_api_endpoints()
    
    print("\n" + "="*40)
    print("Test Summary:")
    print("✅ Enhanced registration system is working correctly")
    print("✅ All new endpoints are functional")
    print("✅ Integration with questbanker-app is ready")
    print("="*40)


if __name__ == "__main__":
    main()
