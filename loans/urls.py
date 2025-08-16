from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'applications', views.LoanApplicationViewSet, basename='loan-application')
router.register(r'loans', views.LoanViewSet, basename='loan')
router.register(r'schedules', views.LoanScheduleViewSet, basename='loan-schedule')
router.register(r'payments', views.LoanPaymentViewSet, basename='loan-payment')
router.register(r'documents', views.LoanDocumentViewSet, basename='loan-document')

urlpatterns = [
    path('', include(router.urls)),
]
