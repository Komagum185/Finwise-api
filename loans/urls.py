from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoanProductViewSet, GroupLoanViewSet, GroupLoanRepaymentViewSet

router = DefaultRouter()
router.register(r'products', LoanProductViewSet, basename='loan-product')
router.register(r'group-loans', GroupLoanViewSet, basename='group-loan')
router.register(r'group-repayments', GroupLoanRepaymentViewSet, basename='group-loan-repayment')

urlpatterns = [
    path('', include(router.urls)),
]


