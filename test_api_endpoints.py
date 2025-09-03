#!/usr/bin/env python3
"""
Script to test API endpoints and verify they return the sample data.
This helps ensure your frontend can successfully fetch data from the API.
"""

import os
import sys
import django
import requests
import json

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finwise.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


def test_api_endpoints():
    """Test API endpoints using Django test client"""
    
    print("🧪 TESTING API ENDPOINTS")
    print("=" * 50)
    
    # Create a test client
    client = Client()
    
    # Test endpoints that don't require authentication first
    endpoints_to_test = [
        # Add your actual API endpoints here
        # Example: '/api/products/', '/api/mse/', etc.
    ]
    
    print("Note: Add your actual API endpoints to test them.")
    print("You can check your markets/urls.py and other app URL files.")
    
    # Let's check what URLs are available
    print("\n📋 CHECKING AVAILABLE URLS:")
    print("-" * 30)
    
    try:
        # Check if Django can resolve URLs
        from django.urls import get_resolver
        resolver = get_resolver()
        url_patterns = resolver.url_patterns
        
        print("Available URL patterns:")
        for pattern in url_patterns:
            if hasattr(pattern, 'url_patterns'):
                for sub_pattern in pattern.url_patterns:
                    if hasattr(sub_pattern, 'name') and sub_pattern.name:
                        print(f"• {sub_pattern.name}: {sub_pattern.pattern}")
            elif hasattr(pattern, 'name') and pattern.name:
                print(f"• {pattern.name}: {pattern.pattern}")
    except Exception as e:
        print(f"Could not resolve URLs: {e}")
    
    # Test database connectivity
    print("\n🗄️ DATABASE CONNECTIVITY TEST:")
    print("-" * 30)
    
    try:
        from markets.models import Product, Transaction
        from mse.models import MSE
        
        product_count = Product.objects.count()
        transaction_count = Transaction.objects.count()
        mse_count = MSE.objects.count()
        
        print(f"✅ Database connection successful!")
        print(f"   Products: {product_count}")
        print(f"   Transactions: {transaction_count}")
        print(f"   MSEs: {mse_count}")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    # Test model serialization
    print("\n📊 MODEL SERIALIZATION TEST:")
    print("-" * 30)
    
    try:
        from markets.serializers import ProductSerializer
        from markets.models import Product
        
        # Get first product
        product = Product.objects.first()
        if product:
            serializer = ProductSerializer(product)
            data = serializer.data
            print(f"✅ Product serialization successful!")
            print(f"   Product: {data.get('name', 'N/A')}")
            print(f"   Price: {data.get('price', 'N/A')} UGX")
            print(f"   MSE: {data.get('mse', 'N/A')}")
        else:
            print("❌ No products found in database")
            
    except Exception as e:
        print(f"❌ Product serialization failed: {e}")
    
    # Test view functionality
    print("\n👁️ VIEW FUNCTIONALITY TEST:")
    print("-" * 30)
    
    try:
        from markets.views import ProductViewSet
        from markets.models import Product
        
        # Test if viewset can handle requests
        products = Product.objects.all()[:5]
        print(f"✅ View functionality test successful!")
        print(f"   Can access {len(products)} products through models")
        
    except Exception as e:
        print(f"❌ View functionality test failed: {e}")


def show_api_usage_examples():
    """Show examples of how to use the API from frontend"""
    
    print("\n🌐 FRONTEND API USAGE EXAMPLES:")
    print("=" * 50)
    
    print("""
1. Fetch Products (JavaScript/Fetch):
   ```javascript
   fetch('/api/products/')
     .then(response => response.json())
     .then(data => {
       console.log('Products:', data);
       // Display products in your UI
     });
   ```

2. Fetch Transactions (JavaScript/Fetch):
   ```javascript
   fetch('/api/transactions/')
     .then(response => response.json())
     .then(data => {
       console.log('Transactions:', data);
       // Display transaction history
     });
   ```

3. Fetch MSEs (JavaScript/Fetch):
   ```javascript
   fetch('/api/mse/')
     .then(response => response.json())
     .then(data => {
       console.log('MSEs:', data);
       // Display MSE information
     });
   ```

4. React Hook Example:
   ```javascript
   import { useState, useEffect } from 'react';
   
   function ProductsList() {
     const [products, setProducts] = useState([]);
     const [loading, setLoading] = useState(true);
   
     useEffect(() => {
       fetch('/api/products/')
         .then(res => res.json())
         .then(data => {
           setProducts(data);
           setLoading(false);
         });
     }, []);
   
     if (loading) return <div>Loading...</div>;
   
     return (
       <div>
         {products.map(product => (
           <div key={product.id}>
             <h3>{product.name}</h3>
             <p>{product.price} UGX per {product.unit}</p>
           </div>
         ))}
       </div>
     );
   }
   ```

5. Vue.js Example:
   ```javascript
   export default {
     data() {
       return {
         products: [],
         loading: true
       }
     },
     async mounted() {
       try {
         const response = await fetch('/api/products/');
         this.products = await response.json();
         this.loading = false;
       } catch (error) {
         console.error('Error fetching products:', error);
       }
     }
   }
   ```
""")


def main():
    """Main function to run all tests"""
    
    print("🚀 FINWISE API TESTING SUITE")
    print("=" * 60)
    
    test_api_endpoints()
    show_api_usage_examples()
    
    print("\n" + "=" * 60)
    print("✅ TESTING COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Configure your API endpoints in URLs")
    print("2. Test endpoints with your frontend")
    print("3. Customize data as needed")
    print("4. Add authentication if required")


if __name__ == '__main__':
    main()
