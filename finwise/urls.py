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

from authentication.views import ChangePasswordView, LoginView, RegisterUserView
from .views import api_root

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api_root'),  # API root endpoint
    
    # Authentication and user management
    path('api/auth/', include('authentication.urls')),

    # Aliased routes for frontend
    path('api/mse/self-register/', RegisterUserView.as_view(), name='mse-self-register'),
    path('api/mse/login/', LoginView.as_view(), name='mse-login'),
    path('api/mse/change-password/', ChangePasswordView.as_view(), name='mse-change-password'),
    # Core business modules
    path('api/mse/', include('mse.urls')),
    path('api/groups/', include('groups.urls')),
    path('api/loans/', include('loans.urls')),
    path('api/reports/', include('reports.urls')), # Reporting system
    path('api/markets/', include('markets.urls')), # Market operations
    path('api/inventory/', include('inventory.urls')), # Inventory management
    # Financial and operational modules
    path('api/wallet/', include('wallet.urls')),   # Wallet management

    
    # Support and compliance

    
    # USSD banking system

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
