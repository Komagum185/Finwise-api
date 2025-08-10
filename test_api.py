#!/usr/bin/env python3
"""
Simple test script to verify the Finwise API is working.
Run this after starting the Django development server.
"""

import requests
import json
from datetime import date

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/api"

def test_api():
    print("Testing Finwise API...")
    print("=" * 50)
    
    # Test 1: Check if the API is accessible
    try:
        response = requests.get(f"{BASE_URL}/transactions/")
        print(f"✓ API is accessible (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Make sure the Django server is running.")
        print("  Run: python manage.py runserver")
        return
    
    # Test 2: Check authentication requirement
    if response.status_code == 401:
        print("✓ Authentication is required (as expected)")
    else:
        print(f"⚠ Unexpected status code: {response.status_code}")
    
    print("\nAPI Endpoints available:")
    print(f"  - GET {BASE_URL}/transactions/ (list transactions)")
    print(f"  - POST {BASE_URL}/transactions/ (create transaction)")
    print(f"  - GET {BASE_URL}/transactions/summary/ (financial summary)")
    print(f"  - GET {BASE_URL}/transactions/recent/ (recent transactions)")
    
    print("\nTo test with authentication:")
    print("1. Start the server: python manage.py runserver")
    print("2. Visit http://127.0.0.1:8000/admin/ and login with admin/admin")
    print("3. Use tools like curl or Postman to test the API endpoints")

if __name__ == "__main__":
    test_api() 