from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'markets', views.MarketViewSet, basename='market')
router.register(r'producers', views.ProducerViewSet, basename='producer')
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'transactions', views.BusinessTransactionViewSet, basename='business-transaction')

urlpatterns = [
    path('', include(router.urls)),
] 