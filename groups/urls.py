from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet, GroupMembershipViewSet, GroupWalletViewSet

router = DefaultRouter()
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'group-memberships', GroupMembershipViewSet, basename='group-membership')
router.register(r'group-wallets', GroupWalletViewSet, basename='group-wallet')

urlpatterns = [
    path('', include(router.urls)),
]


