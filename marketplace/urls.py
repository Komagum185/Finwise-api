from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet, MarketOpportunityViewSet, OpportunityApplicationViewSet,
    MarketplaceMessageViewSet, ProductReviewViewSet, MarketplaceNotificationViewSet,
    MarketplaceStatisticsViewSet
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'opportunities', MarketOpportunityViewSet, basename='opportunity')
router.register(r'applications', OpportunityApplicationViewSet, basename='application')
router.register(r'messages', MarketplaceMessageViewSet, basename='message')
router.register(r'reviews', ProductReviewViewSet, basename='review')
router.register(r'notifications', MarketplaceNotificationViewSet, basename='notification')
router.register(r'statistics', MarketplaceStatisticsViewSet, basename='statistics')

urlpatterns = [
    path('', include(router.urls)),
]
