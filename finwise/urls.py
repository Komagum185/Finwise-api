"""
URL configuration for finwise project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication and user management
    path('api/auth/', include('authentication.urls')),
    
    # Super Admin endpoints - Full CRUD on users, MSEs, institutions, roles, privileges
    path('api/admin/', include('admin_urls')),
    
    # Agent endpoints - Manage assigned MSEs, view wallet balances, registration status
    path('api/agent/', include('agent_urls')),
    
    # MSE endpoints - Access only their own data: wallet, loans, customers, suppliers, transactions, reports
    path('api/mse/', include('mse_urls')),
    
    # Partner endpoints - Access only to partner dashboard (legacy system)
    path('api/partner/', include('partner_urls')),
    
    # Partner Dashboard (legacy - partners use this)
    path('api/partner-dashboard/', include('partner_dashboard.urls')),
    
    # Other app endpoints
    path('api/mse/', include('mse.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/loans/', include('loans.urls')),
    path('api/markets/', include('markets.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/groups/', include('groups.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
