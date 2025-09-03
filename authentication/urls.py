from django.urls import path
from .views import RegisterUserView, LoginView, ChangePasswordView, SuperAdminPartnerRegistrationView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('super-admin/create-partner/', SuperAdminPartnerRegistrationView.as_view(), name='super-admin-create-partner'),
]
