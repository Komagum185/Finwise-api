from django.urls import path
from .views import (
    RegisterUserView, LoginView, ChangePasswordView, UserListView, UserDetailView,
    AgentListView, AgentDetailView, AssignUserToAgentView, ApproveUserView,
    UserProfileView, user_dashboard_data, PasswordResetView, PasswordResetConfirmView
)

urlpatterns = [
    # Basic authentication
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # Password reset
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    # User management (Super Admin and Agent)
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    
    # Agent management
    path('agents/', AgentListView.as_view(), name='agent-list'),
    path('agents/<int:pk>/', AgentDetailView.as_view(), name='agent-detail'),
    path('users/<int:pk>/assign-agent/', AssignUserToAgentView.as_view(), name='assign-user-to-agent'),
    
    # User approval
    path('users/<int:pk>/approve/', ApproveUserView.as_view(), name='approve-user'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Dashboard data
    path('dashboard-data/', user_dashboard_data, name='user-dashboard-data'),
]
