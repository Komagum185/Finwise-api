from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from .models import CustomUser
from .serializers import (
    UserSerializer, UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer, UserSummarySerializer, 
    AgentAssignmentSerializer, UserDashboardDataSerializer
)
from django.db import models

class RegisterUserView(generics.CreateAPIView):
    """Register new user - only super admins can create certain roles"""
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Create new user with role validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check permissions for creating different roles
        user_data = serializer.validated_data
        
        # Only super admins can create super admin users
        if user_data.get('is_super_admin') and not request.user.is_super_admin:
            return Response(
                {"error": "Only super admins can create super admin users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only super admins and agents can create MSE users
        if user_data.get('is_mse') and not (request.user.is_super_admin or request.user.is_agent):
            return Response(
                {"error": "Only super admins and agents can create MSE users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only super admins can create partner users
        if user_data.get('is_partner') and not request.user.is_super_admin:
            return Response(
                {"error": "Only super admins can create partner users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create the user
        user = serializer.save()
        
        return Response({
            "message": "User created successfully",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
        
        
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from .models import CustomUser
from .serializers import (
    UserSerializer, UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer, UserSummarySerializer, 
    AgentAssignmentSerializer, UserDashboardDataSerializer
)
from django.db import models

class RegisterUserView(generics.CreateAPIView):
    """Register new user - only super admins can create certain roles"""
    serializer_class = UserCreateSerializer
    permission_classes = []  # Allow registration without authentication
    
    def create(self, request, *args, **kwargs):
        """Create new user with role validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check permissions for creating different roles
        user_data = serializer.validated_data
        
        # For unauthenticated registration, only allow basic roles
        if not request.user.is_authenticated:
            # Unauthenticated users can only create basic MSE users
            if user_data.get('is_super_admin') or user_data.get('is_agent') or user_data.get('is_partner'):
                return Response(
                    {"error": "Unauthenticated users can only create basic MSE accounts"},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Default to MSE if no role specified
            if not any([user_data.get('is_super_admin'), user_data.get('is_agent'), user_data.get('is_mse'), user_data.get('is_partner')]):
                user_data['is_mse'] = True
        else:
            # Authenticated users follow role-based permissions
            # Only super admins can create super admin users
            if user_data.get('is_super_admin') and not request.user.is_super_admin:
                return Response(
                    {"error": "Only super admins can create super admin users"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Only super admins and agents can create MSE users
            if user_data.get('is_mse') and not (request.user.is_super_admin or request.user.is_agent):
                return Response(
                    {"error": "Only super admins and agents can create MSE users"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Only super admins can create partner users
            if user_data.get('is_partner') and not request.user.is_super_admin:
                return Response(
                    {"error": "Only super admins can create partner users"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Create the user
        user = serializer.save()
        
        return Response({
            "message": "User created successfully",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    """User login view"""
    serializer_class = LoginSerializer
    permission_classes = []  # No authentication required for login
    
    def post(self, request):
        """Handle user login"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Update first login flag
        if user.first_login:
            user.first_login = False
            user.save()
        
        return Response({
            "message": "Login successful",
            "user": UserDashboardDataSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })

class ChangePasswordView(generics.UpdateAPIView):
    """Change user password"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        """Update user password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({"message": "Password changed successfully"})

class UserListView(generics.ListAPIView):
    """List users - filtered by permissions"""
    serializer_class = UserSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter users based on permissions"""
        user = self.request.user
        
        if user.is_super_admin:
            # Super admins can see all users
            return CustomUser.objects.all()
        elif user.is_agent:
            # Agents can see their assigned users and other agents
            return CustomUser.objects.filter(
                models.Q(assigned_agent=user) | models.Q(is_agent=True)
            )
        else:
            # Other users can only see themselves
            return CustomUser.objects.filter(id=user.id)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """User detail view with CRUD operations"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    
    def get_object(self):
        """Get user object with permission check"""
        obj = super().get_object()
        user = self.request.user
        
        # Check if user can view this object
        if not user.can_manage_user(obj):
            raise PermissionError("You don't have permission to view this user")
        
        return obj
    
    def update(self, request, *args, **kwargs):
        """Update user with permission check"""
        obj = self.get_object()
        user = request.user
        
        # Check if user can update this object
        if not user.can_manage_user(obj):
            return Response(
                {"error": "You don't have permission to update this user"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete user with permission check"""
        obj = self.get_object()
        user = request.user
        
        # Only super admins can delete users
        if not user.is_super_admin:
            return Response(
                {"error": "Only super admins can delete users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)

class AgentListView(generics.ListAPIView):
    """List all agents"""
    serializer_class = UserSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get all agents"""
        return CustomUser.objects.filter(is_agent=True)

class AgentDetailView(generics.RetrieveAPIView):
    """Agent detail view"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.filter(is_agent=True)

class AssignUserToAgentView(generics.UpdateAPIView):
    """Assign user to an agent"""
    serializer_class = AgentAssignmentSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    
    def update(self, request, *args, **kwargs):
        """Assign user to agent"""
        user = self.get_object()
        current_user = request.user
        
        # Check permissions
        if not (current_user.is_super_admin or current_user.is_agent):
            return Response(
                {"error": "Only super admins and agents can assign users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update assigned agent
        user.assigned_agent = serializer.validated_data.get('assigned_agent')
        user.save()
        
        return Response({
            "message": "User assigned to agent successfully",
            "user": UserDetailSerializer(user).data
        })

class ApproveUserView(generics.UpdateAPIView):
    """Approve user account"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    
    def update(self, request, *args, **kwargs):
        """Approve user"""
        user = self.get_object()
        current_user = request.user
        
        # Check permissions
        if not (current_user.is_super_admin or current_user.is_agent):
            return Response(
                {"error": "Only super admins and agents can approve users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Approve user
        user.is_approved = True
        user.save()
        
        return Response({
            "message": "User approved successfully",
            "user": UserSerializer(user).data
        })

class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view - users can view and update their own profile"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Return current user"""
        return self.request.user

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_data(request):
    """Get user dashboard data based on their roles and capabilities"""
    user = request.user
    
    # Get accessible dashboards
    accessible_dashboards = user.get_accessible_dashboards()
    
    # Get role-specific data
    dashboard_data = {
        "user": UserDashboardDataSerializer(user).data,
        "accessible_dashboards": accessible_dashboards,
        "capabilities": user.capabilities,
        "has_multiple_roles": user.has_multiple_roles,
        "primary_role": user.primary_role
    }
    
    # Add role-specific information
    if user.is_agent:
        assigned_users = user.get_assigned_users()
        dashboard_data["assigned_users_count"] = assigned_users.count()
        dashboard_data["assigned_users"] = UserSummarySerializer(assigned_users, many=True).data
    
    if user.is_mse:
        dashboard_data["mse_name"] = user.mse_name
        if user.assigned_agent:
            dashboard_data["assigned_agent"] = UserSummarySerializer(user.assigned_agent).data
    
    if user.is_partner:
        dashboard_data["partner_institution"] = user.partner_institution
    
    return Response(dashboard_data)



class ChangePasswordView(generics.UpdateAPIView):
    """Change user password"""
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        """Update user password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({"message": "Password changed successfully"})

class UserListView(generics.ListAPIView):
    """List users - filtered by permissions"""
    serializer_class = UserSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter users based on permissions"""
        user = self.request.user
        
        if user.is_super_admin:
            # Super admins can see all users
            return CustomUser.objects.all()
        elif user.is_agent:
            # Agents can see their assigned users and other agents
            return CustomUser.objects.filter(
                models.Q(assigned_agent=user) | models.Q(is_agent=True)
            )
        else:
            # Other users can only see themselves
            return CustomUser.objects.filter(id=user.id)

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """User detail view with CRUD operations"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    
    def get_object(self):
        """Get user object with permission check"""
        obj = super().get_object()
        user = self.request.user
        
        # Check if user can view this object
        if not user.can_manage_user(obj):
            raise PermissionError("You don't have permission to view this user")
        
        return obj
    
    def update(self, request, *args, **kwargs):
        """Update user with permission check"""
        obj = self.get_object()
        user = request.user
        
        # Check if user can update this object
        if not user.can_manage_user(obj):
            return Response(
                {"error": "You don't have permission to update this user"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete user with permission check"""
        obj = self.get_object()
        user = request.user
        
        # Only super admins can delete users
        if not user.is_super_admin:
            return Response(
                {"error": "Only super admins can delete users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)

class AgentListView(generics.ListAPIView):
    """List all agents"""
    serializer_class = UserSummarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get all agents"""
        return CustomUser.objects.filter(is_agent=True)

class AgentDetailView(generics.RetrieveAPIView):
    """Agent detail view"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.filter(is_agent=True)

class AssignUserToAgentView(generics.UpdateAPIView):
    """Assign user to an agent"""
    serializer_class = AgentAssignmentSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    
    def update(self, request, *args, **kwargs):
        """Assign user to agent"""
        user = self.get_object()
        current_user = request.user
        
        # Check permissions
        if not (current_user.is_super_admin or current_user.is_agent):
            return Response(
                {"error": "Only super admins and agents can assign users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update assigned agent
        user.assigned_agent = serializer.validated_data.get('assigned_agent')
        user.save()
        
        return Response({
            "message": "User assigned to agent successfully",
            "user": UserDetailSerializer(user).data
        })

class ApproveUserView(generics.UpdateAPIView):
    """Approve user account"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()
    
    def update(self, request, *args, **kwargs):
        """Approve user"""
        user = self.get_object()
        current_user = request.user
        
        # Check permissions
        if not (current_user.is_super_admin or current_user.is_agent):
            return Response(
                {"error": "Only super admins and agents can approve users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Approve user
        user.is_approved = True
        user.save()
        
        return Response({
            "message": "User approved successfully",
            "user": UserSerializer(user).data
        })

class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view - users can view and update their own profile"""
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Return current user"""
        return self.request.user

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_data(request):
    """Get user dashboard data based on their roles and capabilities"""
    user = request.user
    
    # Get accessible dashboards
    accessible_dashboards = user.get_accessible_dashboards()
    
    # Get role-specific data
    dashboard_data = {
        "user": UserDashboardDataSerializer(user).data,
        "accessible_dashboards": accessible_dashboards,
        "capabilities": user.capabilities,
        "has_multiple_roles": user.has_multiple_roles,
        "primary_role": user.primary_role
    }
    
    # Add role-specific information
    if user.is_agent:
        assigned_users = user.get_assigned_users()
        dashboard_data["assigned_users_count"] = assigned_users.count()
        dashboard_data["assigned_users"] = UserSummarySerializer(assigned_users, many=True).data
    
    if user.is_mse:
        dashboard_data["mse_name"] = user.mse_name
        if user.assigned_agent:
            dashboard_data["assigned_agent"] = UserSummarySerializer(user.assigned_agent).data
    
    if user.is_partner:
        dashboard_data["partner_institution"] = user.partner_institution
    
    return Response(dashboard_data)
