from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, SupplierViewSet, ProductViewSet, TransactionViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='market-customer')
router.register(r'suppliers', SupplierViewSet, basename='market-supplier')
router.register(r'products', ProductViewSet, basename='market-product')
router.register(r'transactions', TransactionViewSet, basename='market-transaction')
router.register(r'notifications', NotificationViewSet, basename='market-notification')

urlpatterns = [
    path('', include(router.urls)),
]


