#!/usr/bin/env python3
"""
Comprehensive API Testing Suite for Finwise API
"""

import os
import django
import requests
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser
from wallet.models import EnhancedWallet, Category
from mses.models import MSE

User = get_user_model()


class ComprehensiveAPITestSuite:
    """Comprehensive test suite for all API endpoints"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = APIClient()
        self.test_user = None
        self.test_mse = None
        self.test_wallet = None
        self.access_token = None
        
    def run_all_tests(self):
        """Run all test scenarios"""
        print("🚀 Starting Comprehensive API Test Suite...")
        
        try:
            self.setup_test_data()
            self.test_authentication_system()
            self.test_user_management()
            self.test_wallet_system()
            self.test_mse_analytics()
            print("✅ All tests completed successfully!")
            
        except Exception as e:
            print(f"❌ Test suite failed: {str(e)}")
            raise
    
    def setup_test_data(self):
        """Setup test data"""
        print("📊 Setting up test data...")
        
        self.test_user = CustomUser.objects.create_user(
            username='testuser_api',
            email='testuser_api@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.test_mse = MSE.objects.create(
            name='Test MSE API',
            mse_type='Input MSE',
            business_type='Manufacturing',
            status='active',
            user=self.test_user
        )
        
        self.test_wallet = EnhancedWallet.objects.create(
            mse=self.test_mse,
            mse_name=self.test_mse.name,
            mse_code='TEST001',
            account_number='ACC001',
            account_type='business',
            currency='USD',
            balance=1000.00,
            status='active'
        )
        
        refresh = RefreshToken.for_user(self.test_user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        print("✅ Test data setup complete")
    
    def test_authentication_system(self):
        """Test authentication endpoints"""
        print("🔐 Testing authentication system...")
        
        login_data = {
            'username': 'testuser_api',
            'password': 'testpass123'
        }
        
        response = self.client.post(f'{self.base_url}/api/auth/login/', login_data)
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        print("✅ Login test passed")
    
    def test_user_management(self):
        """Test user management features"""
        print("👤 Testing user management...")
        
        response = self.client.get(f'{self.base_url}/api/auth/profile/')
        assert response.status_code == 200, f"Profile retrieval failed: {response.status_code}"
        print("✅ Profile retrieval test passed")
    
    def test_wallet_system(self):
        """Test enhanced wallet system"""
        print("💰 Testing wallet system...")
        
        response = self.client.get(f'{self.base_url}/api/wallet/enhanced-wallets/{self.test_wallet.id}/analytics/')
        assert response.status_code == 200, f"Wallet analytics failed: {response.status_code}"
        print("✅ Wallet analytics test passed")
    
    def test_mse_analytics(self):
        """Test MSE analytics"""
        print("🏢 Testing MSE analytics...")
        
        response = self.client.get(f'{self.base_url}/api/mses/mses/business_analytics/')
        assert response.status_code == 200, f"Business analytics failed: {response.status_code}"
        print("✅ Business analytics test passed")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        if self.test_wallet:
            self.test_wallet.delete()
        if self.test_mse:
            self.test_mse.delete()
        if self.test_user:
            self.test_user.delete()


def main():
    """Main function"""
    print("🧪 Finwise API Comprehensive Test Suite")
    
    try:
        response = requests.get("http://localhost:8000/api/", timeout=5)
        if response.status_code != 404:
            print("❌ Server not responding properly")
            return
    except requests.exceptions.RequestException:
        print("❌ Server not running. Please start Django server first.")
        return
    
    test_suite = ComprehensiveAPITestSuite()
    
    try:
        test_suite.run_all_tests()
    finally:
        test_suite.cleanup_test_data()
    
    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    main()
