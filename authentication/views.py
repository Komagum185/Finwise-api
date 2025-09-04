from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import transaction
from .models import CustomUser
from .serializers import (
    UserSerializer, UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer, UserSummarySerializer, AgentAssignmentSerializer
)
from partner_dashboard.permissions import (
    IsSuperAdmin, CanManageUsers, CanManageMSE, IsOwnerOrReadOnly
)
from django.db.models import Q


class RegisterUserView(generics.CreateAPIView):
    """Register a new user - only super admin can create users with certain roles"""
    
    serializer_class = UserCreateSerializer
    permission_classes = [IsSuperAdmin]
    
    def create(self, request, *args, **kwargs):
        """Create user with role validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Only super admin can create users with admin/agent roles
        role = serializer.validated_data.get('role')
        if role in ['super_admin', 'agent'] and not request.user.is_super_admin:
            return Response(
                {'error': 'Only super admin can create admin and agent users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = serializer.save()
        
        return Response({
            'message': 'User created successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """User login view"""
    
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        
        if user:
            if not user.is_approved and user.role != 'super_admin':
                return Response({
                    'error': 'Account not approved. Please contact administrator.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class ChangePasswordView(generics.UpdateAPIView):
    """Change user password"""
    
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.first_login = False
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        })


class UserListView(generics.ListAPIView):
    """List users based on role permissions"""
    
    serializer_class = UserSummarySerializer
    permission_classes = [CanManageUsers]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            # Super admin can see all users
            return CustomUser.objects.all()
        elif user.role == 'agent':
            # Agent can see assigned users and other agents
            return CustomUser.objects.filter(
                Q(assigned_agent=user) | Q(role='agent')
            )
        
        return CustomUser.objects.none()


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a user"""
    
    serializer_class = UserDetailSerializer
    permission_classes = [CanManageUsers, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            return CustomUser.objects.all()
        elif user.role == 'agent':
            return CustomUser.objects.filter(
                Q(assigned_agent=user) | Q(role='agent')
            )
        
        return CustomUser.objects.none()


class AgentListView(generics.ListAPIView):
    """List all agents"""
    
    serializer_class = AgentAssignmentSerializer
    permission_classes = [CanManageUsers]
    
    def get_queryset(self):
        return CustomUser.objects.filter(role='agent')


class AgentDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update an agent"""
    
    serializer_class = AgentAssignmentSerializer
    permission_classes = [CanManageUsers]
    
    def get_queryset(self):
        return CustomUser.objects.filter(role='agent')


class AssignUserToAgentView(generics.UpdateAPIView):
    """Assign a user to an agent"""
    
    serializer_class = UserUpdateSerializer
    permission_classes = [CanManageUsers]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            return CustomUser.objects.filter(role__in=['mse', 'partner'])
        elif user.role == 'agent':
            return CustomUser.objects.filter(role__in=['mse', 'partner'])
        
        return CustomUser.objects.none()
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        agent_id = request.data.get('assigned_agent')
        
        if agent_id:
            try:
                agent = CustomUser.objects.get(id=agent_id, role='agent')
                user.assigned_agent = agent
                user.save()
                
                return Response({
                    'message': f'User assigned to agent {agent.first_name} {agent.last_name}'
                })
            except CustomUser.DoesNotExist:
                return Response({
                    'error': 'Invalid agent ID'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'error': 'Agent ID is required'
        }, status=status.HTTP_400_BAD_REQUEST)


class ApproveUserView(generics.UpdateAPIView):
    """Approve a user account"""
    
    serializer_class = UserUpdateSerializer
    permission_classes = [CanManageUsers]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_super_admin:
            return CustomUser.objects.filter(is_approved=False)
        elif user.role == 'agent':
            return CustomUser.objects.filter(
                assigned_agent=user,
                is_approved=False
            )
        
        return CustomUser.objects.none()
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_approved = True
        user.save()
        
        return Response({
            'message': f'User {user.username} approved successfully'
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view - users can view and update their own profile"""
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_dashboard_data(request):
    """Get user-specific dashboard data based on role"""
    
    user = request.user
    
    if user.role == 'super_admin':
        # Super admin dashboard data
        data = {
            'total_users': CustomUser.objects.count(),
            'total_mse_users': CustomUser.objects.filter(role='mse').count(),
            'total_agents': CustomUser.objects.filter(role='agent').count(),
            'total_partners': CustomUser.objects.filter(role='partner').count(),
            'pending_approvals': CustomUser.objects.filter(is_approved=False).count(),
        }
    
    elif user.role == 'agent':
        # Agent dashboard data
        assigned_users = user.assigned_mse_users.all()
        data = {
            'assigned_users_count': assigned_users.count(),
            'assigned_mse_count': assigned_users.filter(role='mse').count(),
            'assigned_partner_count': assigned_users.filter(role='partner').count(),
            'pending_approvals': assigned_users.filter(is_approved=False).count(),
        }
    
    elif user.role == 'mse':
        # MSE dashboard data
        data = {
            'mse_name': user.mse_name,
            'is_approved': user.is_approved,
            'assigned_agent': user.assigned_agent.first_name if user.assigned_agent else None,
        }
    
    elif user.role == 'partner':
        # Partner dashboard data
        data = {
            'partner_institution': user.partner_institution,
            'assigned_agent': user.assigned_agent.first_name if user.assigned_agent else None,
        }
    
    else:
        data = {}
    
    return Response(data)
