from django.urls import path
from .views import (
    UserRegistrationView, EnhancedRegistrationView, RegistrationProgressView,
    RegistrationStatusView, UserOnboardingView, RegistrationAnalyticsView,
    LoginView, UserProfileView, LogoutView
)

app_name = 'auth_app'

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('register-enhanced/', EnhancedRegistrationView.as_view(), name='register-enhanced'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Registration workflow endpoints
    path('registration-progress/<uuid:registration_id>/', RegistrationProgressView.as_view(), name='registration-progress'),
    path('registration-status/<uuid:registration_id>/', RegistrationStatusView.as_view(), name='registration-status'),
    path('onboarding/', UserOnboardingView.as_view(), name='user-onboarding'),
    path('registration-analytics/', RegistrationAnalyticsView.as_view(), name='registration-analytics'),
    
    # User profile endpoints
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]
