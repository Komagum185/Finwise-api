from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser
from .serializers import RegisterUserSerializer, ChangePasswordSerializer, CustomUserSerializer

class IsSuperAdmin(permissions.BasePermission):
    """
    Custom permission to only allow super admin users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role == 'admin' and
            request.user.is_superuser
        )

class SuperAdminPartnerRegistrationView(generics.CreateAPIView):
    """
    Super admin only endpoint to create partner users.
    Regular users cannot access this endpoint.
    """
    queryset = CustomUser.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = [IsSuperAdmin]

    def create(self, request, *args, **kwargs):
        # Ensure only partner users can be created through this endpoint
        if request.data.get('role') != 'partner':
            return Response(
                {'detail': 'This endpoint can only create partner users.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create partner user with auto-approval
        user = serializer.save()
        user.is_approved = True  # Auto-approve partner users created by super admin
        user.save()

        data = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_approved': user.is_approved,
            'message': 'Partner user created successfully by super admin'
        }

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

class RegisterUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterUserSerializer
    permission_classes = [permissions.AllowAny]  # Anyone can register

    def create(self, request, *args, **kwargs):
        # Prevent partner role creation through public registration
        if request.data.get('role') == 'partner':
            return Response(
                {'detail': 'Partner users can only be created by super administrators.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # Create the user

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        data = {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'first_login': user.first_login,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
# JWT Login
class LoginView(generics.GenericAPIView):
    serializer_class = RegisterUserSerializer  # Only username/password required
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            if not user.is_approved:
                return Response({'detail': 'Account not approved by admin.'}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'first_login': user.first_login,
                'role': user.role
            }
            return Response(data)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# Change password (first login or regular)
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = CustomUser
    permission_classes = [permissions.AllowAny]

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'old_password': 'Wrong password.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.first_login = False
        user.save()
        return Response({'detail': 'Password updated successfully'})
