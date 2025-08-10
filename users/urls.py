from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, UserProfileView, 
    ChangePasswordView, user_stats, PendingRegistrationsView,
    ApproveRegistrationView, RejectRegistrationView, VerifyOTPView,
    ResendOTPView, RegisterWithApprovalView
)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('register-with-approval/', RegisterWithApprovalView.as_view(), name='register_with_approval'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('stats/', user_stats, name='user_stats'),
    
    # Pending registrations (Admin only)
    path('pending-registrations/', PendingRegistrationsView.as_view(), name='pending_registrations'),
    path('pending-registrations/<uuid:registration_id>/approve/', ApproveRegistrationView.as_view(), name='approve_registration'),
    path('pending-registrations/<uuid:registration_id>/reject/', RejectRegistrationView.as_view(), name='reject_registration'),
    
    # OTP verification
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
] 