from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()

# Sales Analytics endpoints
router.register(r'sales-data', views.SalesDataViewSet, basename='sales-data')
router.register(r'product-performance', views.ProductPerformanceViewSet, basename='product-performance')
router.register(r'market-trends', views.MarketTrendsViewSet, basename='market-trends')
router.register(r'predictions', views.PredictionsViewSet, basename='predictions')

app_name = 'reports'

urlpatterns = [
    path('', include(router.urls)),
] 