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
from .views import api_root

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api_root'),  # API root endpoint
    path('api/wallet/', include('wallet.urls')),  # Consolidated from api + finance_app
    path('api/auth/', include('users.urls')),
    path('api/mses/', include('mses.urls')),       # Use existing mses app
    path('api/markets/', include('markets.urls')), # Use existing markets app
    path('api/reports/', include('reports.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/loans/', include('loans.urls')),     # Loan management system
    path('api/kyc/', include('kyc.urls')),         # KYC & verification system
    path('api/customers/', include('customers.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/marketplace/', include('marketplace.urls')),  # Customer management system
    path('api/ussd/', include('ussd.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
