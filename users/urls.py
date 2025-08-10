from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, UserProfileView, 
    ChangePasswordView, user_stats, PendingRegistrationsView,
    ApproveRegistrationView, RejectRegistrationView, VerifyOTPView,
    ResendOTPView, RegisterWithApprovalView, EnhancedRegistrationView,
    RegistrationProgressView, RegistrationStatusView, UserOnboardingView,
    RegistrationAnalyticsView
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

    # Enhanced registration endpoints
    path('register-enhanced/', EnhancedRegistrationView.as_view(), name='register-enhanced'),
    path('registration-progress/<uuid:registration_id>/', RegistrationProgressView.as_view(), name='registration-progress'),
    path('registration-status/<uuid:registration_id>/', RegistrationStatusView.as_view(), name='registration-status'),
    path('onboarding/', UserOnboardingView.as_view(), name='user-onboarding'),
    path('registration-analytics/', RegistrationAnalyticsView.as_view(), name='registration-analytics'),
] 