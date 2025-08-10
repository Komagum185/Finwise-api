from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'mses', views.MSEViewSet, basename='mse')
router.register(r'input-mses', views.InputMSEViewSet, basename='input-mse')
router.register(r'output-mses', views.OutputMSEViewSet, basename='output-mse')
router.register(r'production-mses', views.ProductionMSEViewSet, basename='production-mse')
router.register(r'categories', views.MSECategoryViewSet, basename='mse-category')
router.register(r'wallets', views.WalletViewSet, basename='wallet')
router.register(r'users', views.UserRoleViewSet, basename='user-role')

urlpatterns = [
    path('', include(router.urls)),
] 