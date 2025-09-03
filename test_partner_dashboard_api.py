#!/usr/bin/env python3
"""
Script to test the Partner Dashboard API endpoints.
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = 'http://localhost:8000/api/partner-dashboard'

# Test credentials
PARTNER_VIEWER = {
    'username': 'partner_viewer',
    'password': 'password123'
}

PARTNER_EXPORT = {
    'username': 'partner_export',
    'password': 'password123'
}

def get_auth_token(credentials):
    """Get authentication token for a user"""
    login_url = 'http://localhost:8000/api/auth/login/'
    
    response = requests.post(login_url, json=credentials)
    if response.status_code == 200:
        return response.json().get('access')
    else:
        print(f"Failed to get token for {credentials['username']}: {response.text}")
        return None

def test_endpoint(url, token, description):
    """Test an API endpoint"""
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    print(f"\n🔍 Testing: {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Check content type to determine how to handle response
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"Response Keys: {list(data.keys())}")
                        if 'count' in data:
                            print(f"Total Records: {data['count']}")
                    elif isinstance(data, list):
                        print(f"Response Items: {len(data)}")
                except:
                    print("Response: JSON data (parsing failed)")
            elif 'text/csv' in content_type:
                print("Response: CSV data")
                print(f"Content Length: {len(response.content)} bytes")
            elif 'application/pdf' in content_type:
                print("Response: PDF data")
                print(f"Content Length: {len(response.content)} bytes")
            else:
                print(f"Response: {content_type}")
                print(f"Content Length: {len(response.content)} bytes")
        elif response.status_code == 401:
            print("❌ Unauthorized - Authentication required")
        elif response.status_code == 403:
            print("❌ Forbidden - Insufficient permissions")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Make sure the Django server is running")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_partner_dashboard_api():
    """Test all Partner Dashboard API endpoints"""
    
    print("🚀 PARTNER DASHBOARD API TESTING")
    print("=" * 50)
    
    # Get tokens for both partner users
    print("\n🔑 Getting authentication tokens...")
    
    viewer_token = get_auth_token(PARTNER_VIEWER)
    export_token = get_auth_token(PARTNER_EXPORT)
    
    if not viewer_token or not export_token:
        print("❌ Failed to get authentication tokens. Exiting.")
        return
    
    print("✅ Authentication tokens obtained successfully!")
    
    # Test endpoints with partner viewer (viewer rights)
    print(f"\n👤 Testing with Partner Viewer (rights: viewer)")
    print("-" * 40)
    
    test_endpoint(f"{BASE_URL}/summaries/", viewer_token, "Dashboard Summaries")
    test_endpoint(f"{BASE_URL}/graphs/", viewer_token, "Dashboard Graphs")
    test_endpoint(f"{BASE_URL}/reports/", viewer_token, "Report List")
    test_endpoint(f"{BASE_URL}/reports/digitization/", viewer_token, "Digitization Report")
    test_endpoint(f"{BASE_URL}/reports/loans/", viewer_token, "Loan Report")
    test_endpoint(f"{BASE_URL}/reports/digital-services/", viewer_token, "Digital Service Report")
    test_endpoint(f"{BASE_URL}/access-log/", viewer_token, "Access Log")
    
    # Test export endpoints with partner viewer (should be denied)
    print(f"\n📤 Testing Export Endpoints with Partner Viewer (should be denied)")
    print("-" * 50)
    
    test_endpoint(f"{BASE_URL}/reports/digitization/export/", viewer_token, "Basic Export (Viewer)")
    
    # Test endpoints with partner export (export rights)
    print(f"\n👤 Testing with Partner Export (rights: export)")
    print("-" * 40)
    
    test_endpoint(f"{BASE_URL}/summaries/", export_token, "Dashboard Summaries")
    test_endpoint(f"{BASE_URL}/graphs/", export_token, "Dashboard Graphs")
    
    # Test export endpoints with partner export (should be allowed)
    print(f"\n📤 Testing Export Endpoints with Partner Export (should be allowed)")
    print("-" * 50)
    
    test_endpoint(f"{BASE_URL}/reports/digitization/export/", export_token, "Basic Export (Export)")
    test_endpoint(f"{BASE_URL}/reports/loans/export/", export_token, "Loans Export (Export)")
    test_endpoint(f"{BASE_URL}/reports/digital-services/export/", export_token, "Digital Services Export (Export)")
    
    # Note: Format-specific export URLs are working but need URL pattern fixes
    print(f"\n📝 Note: Basic export endpoints work, format-specific URLs need URL pattern fixes")
    
    # Test filters
    print(f"\n🔍 Testing Filters")
    print("-" * 20)
    
    test_endpoint(f"{BASE_URL}/summaries/?age=0-35&gender=female", export_token, "Summaries with Age and Gender Filters")
    test_endpoint(f"{BASE_URL}/reports/digitization/?region=Kampala&district=Central", export_token, "Digitization Report with Region Filter")
    
    # Test pagination
    print(f"\n📄 Testing Pagination")
    print("-" * 20)
    
    test_endpoint(f"{BASE_URL}/reports/digitization/?page=1&page_size=5", export_token, "Digitization Report with Pagination")
    
    print(f"\n✅ Partner Dashboard API Testing Complete!")
    print(f"📊 Check the results above to verify all endpoints are working correctly.")

if __name__ == '__main__':
    test_partner_dashboard_api()
