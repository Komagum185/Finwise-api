from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'documents', views.KYCDocumentViewSet, basename='kyc-document')
router.register(r'bank-accounts', views.BankAccountViewSet, basename='bank-account')
router.register(r'mobile-accounts', views.MobileMoneyAccountViewSet, basename='mobile-account')
router.register(r'verifications', views.KYCVerificationViewSet, basename='kyc-verification')
router.register(r'requests', views.VerificationRequestViewSet, basename='verification-request')

urlpatterns = [
    path('', include(router.urls)),
]
