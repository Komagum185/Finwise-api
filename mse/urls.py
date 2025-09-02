from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MSECategoryViewSet, MSEViewSet, WalletViewSet, SelfRegisterView

router = DefaultRouter()
router.register(r'categories', MSECategoryViewSet, basename='mse-category')
router.register(r'mses', MSEViewSet, basename='mse')
router.register(r'wallets', WalletViewSet, basename='mse-wallet')

urlpatterns = [
    path('', include(router.urls)),
    path('self-register/', SelfRegisterView.as_view(), name='mse-self-register'),
]


