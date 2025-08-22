from django.shortcuts import render
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.throttling import UserRateThrottle
from django.core.cache import cache
from django.conf import settings

from .models import CustomUser, PendingRegistration, OTPVerification
from .serializers import (
    UserSerializer, PendingRegistrationSerializer, PendingRegistrationCreateSerializer,
    OTPVerificationSerializer, VerifyOTPSerializer, ResendOTPSerializer,
    CustomUserSerializer, EnhancedRegistrationSerializer, RegistrationProgressSerializer,
    RegistrationStatusSerializer, UserOnboardingSerializer
)
from .utils import send_otp_email, send_otp_sms, send_registration_approval_email

# Conditionally import throttling based on environment
if not getattr(settings, 'DEBUG', True):
    from .throttling import LoginRateThrottle
else:
    LoginRateThrottle = None


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def auth_root(request):
    """
    Authentication API root endpoint
    """
    auth_info = {
        "name": "Finwise Authentication API",
        "version": "1.0.0",
        "description": "Authentication and user management endpoints",
        "endpoints": {
            "register": "/api/auth/register/",
            "register_with_approval": "/api/auth/register-with-approval/",
            "login": "/api/auth/login/",
            "logout": "/api/auth/logout/",
            "token_refresh": "/api/auth/token/refresh/",
            "profile": "/api/auth/profile/",
            "change_password": "/api/auth/change-password/",
            "password_reset": "/api/auth/password-reset/",
            "email_verification": "/api/auth/email-verify/",
            "otp_verification": "/api/auth/verify-otp/",
            "pending_registrations": "/api/auth/pending-registrations/",
            "registration_analytics": "/api/auth/registration-analytics/"
        },
        "status": "active"
    }
    
    return Response(auth_info)


class RegisterView(APIView):
    """User registration view"""
    permission_classes = [permissions.AllowAny]
    
    @transaction.atomic
    def post(self, request):
        """Register a new user"""
        data = request.data
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'{field} is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if user already exists
        if CustomUser.objects.filter(username=data['username']).exists():
            return Response(
                {'error': 'Username already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if CustomUser.objects.filter(email=data['email']).exists():
            return Response(
                {'error': 'Email already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password
        try:
            validate_password(data['password'])
        except ValidationError as e:
            return Response(
                {'error': e.messages[0]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user
        try:
            user = CustomUser.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data.get('phone_number', ''),
                date_of_birth=data.get('date_of_birth'),
                default_currency=data.get('default_currency', 'USD'),
                monthly_income=data.get('monthly_income')
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User registered successfully',
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    """User login view"""
    permission_classes = [permissions.AllowAny]
    
    # Apply rate limiting only in production
    if LoginRateThrottle:
        throttle_classes = [LoginRateThrottle]
    
    def get_ident(self, request):
        """Get client identifier for rate limiting"""
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def post(self, request):
        """Authenticate user and return tokens"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user by username
        user = authenticate(username=username, password=password)
        
        if not user:
            # Handle rate limiting only in production
            if LoginRateThrottle:
                # Increment failure counter for rate limiting
                self.throttle_failure(request, self)
                
                # Get current attempt count for user guidance
                cache_key = f"login_attempts:{self.get_ident(request)}"
                attempts = cache.get(cache_key, 0)
                
                if attempts >= 10:
                    return Response({
                        'error': 'Too many failed login attempts. Please wait 5 minutes before trying again.',
                        'wait_time': '5 minutes',
                        'attempts': attempts
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                elif attempts >= 5:
                    return Response({
                        'error': 'Multiple failed login attempts. Please wait 2 minutes before trying again.',
                        'wait_time': '2 minutes',
                        'attempts': attempts
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                else:
                    return Response({
                        'error': 'Invalid credentials',
                        'attempts': attempts,
                        'remaining_attempts': 20 - attempts
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                # Development: Simple error response
                return Response(
                    {'error': 'Invalid credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Check if user is active
        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Reset rate limiting on successful login
        if LoginRateThrottle:
            LoginRateThrottle().reset_login_attempts(request, self)
        
        return Response({
            'message': 'Login successful',
            'user': CustomUserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """User logout view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Logout user and blacklist refresh token"""
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({'message': 'Logout successful'})
        except Exception as e:
            return Response(
                {'error': 'Invalid token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(APIView):
    """User profile management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user profile"""
        serializer = CustomUserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    def put(self, request):
        """Update user profile"""
        user = request.user
        data = request.data
        
        # Update allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'date_of_birth', 'default_currency', 'monthly_income',
            'address', 'city', 'country', 'postal_code',
            'employment_status', 'employer_name', 'job_title',
            'preferred_banking_hours', 'communication_preference'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        # Validate email uniqueness if changed
        if 'email' in data and data['email'] != user.email:
            if CustomUser.objects.filter(email=data['email']).exists():
                return Response(
                    {'error': 'Email already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Mark email as unverified if changed
            user.is_verified = False
        
        user.save()
        
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response({
            'message': 'Profile updated successfully',
            'user': serializer.data
        })

    @action(detail=False, methods=['post'])
    def upload_profile_picture(self, request):
        """Upload profile picture"""
        user = request.user
        
        if 'profile_picture' not in request.FILES:
            return Response(
                {'error': 'Profile picture is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile_picture = request.FILES['profile_picture']
        
        # Validate file type and size
        if not profile_picture.content_type.startswith('image/'):
            return Response(
                {'error': 'File must be an image'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if profile_picture.size > 5 * 1024 * 1024:  # 5MB limit
            return Response(
                {'error': 'File size must be less than 5MB'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete old profile picture if exists
        if user.profile_picture:
            user.profile_picture.delete(save=False)
        
        user.profile_picture = profile_picture
        user.save()
        
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response({
            'message': 'Profile picture uploaded successfully',
            'user': serializer.data
        })

    @action(detail=False, methods=['post'])
    def remove_profile_picture(self, request):
        """Remove profile picture"""
        user = request.user
        
        if not user.profile_picture:
            return Response(
                {'error': 'No profile picture to remove'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.profile_picture.delete(save=False)
        user.profile_picture = None
        user.save()
        
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response({
            'message': 'Profile picture removed successfully',
            'user': serializer.data
        })

    @action(detail=False, methods=['get'])
    def onboarding_status(self, request):
        """Get user onboarding completion status"""
        user = request.user
        
        onboarding_steps = {
            'profile_complete': bool(user.first_name and user.last_name and user.phone_number),
            'financial_setup': bool(user.default_currency and user.monthly_income),
            'address_complete': bool(user.address and user.city and user.country),
            'employment_info': bool(user.employment_status),
            'preferences_set': bool(user.preferred_banking_hours and user.communication_preference),
            'terms_accepted': bool(user.terms_accepted_at)
        }
        
        completed_steps = sum(onboarding_steps.values())
        total_steps = len(onboarding_steps)
        completion_percentage = (completed_steps / total_steps) * 100
        
        return Response({
            'onboarding_complete': user.onboarding_completed,
            'completion_percentage': completion_percentage,
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'step_details': onboarding_steps,
            'next_steps': self._get_next_onboarding_steps(onboarding_steps)
        })

    def _get_next_onboarding_steps(self, onboarding_steps):
        """Get next steps for onboarding completion"""
        next_steps = []
        
        if not onboarding_steps['profile_complete']:
            next_steps.append('Complete your basic profile information')
        
        if not onboarding_steps['financial_setup']:
            next_steps.append('Set your financial preferences')
        
        if not onboarding_steps['address_complete']:
            next_steps.append('Add your address information')
        
        if not onboarding_steps['employment_info']:
            next_steps.append('Provide employment information')
        
        if not onboarding_steps['preferences_set']:
            next_steps.append('Set your banking preferences')
        
        if not onboarding_steps['terms_accepted']:
            next_steps.append('Accept terms and conditions')
        
        return next_steps


class ChangePasswordView(APIView):
    """Change password view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Change user password"""
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not current_password or not new_password:
            return Response(
                {'error': 'Current password and new password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify current password
        if not user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate new password
        try:
            validate_password(new_password)
        except ValidationError as e:
            return Response(
                {'error': e.messages[0]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Password changed successfully'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get user statistics"""
    user = request.user
    
    # Import here to avoid circular imports
    from wallet.models import Transaction, Budget, Goal
    
    stats = {
        'total_transactions': Transaction.objects.filter(user=user).count(),
        'total_budgets': Budget.objects.filter(user=user, is_active=True).count(),
        'active_goals': Goal.objects.filter(user=user, status='active').count(),
        'completed_goals': Goal.objects.filter(user=user, status='completed').count(),
    }
    
    return Response(stats)


class PendingRegistrationsView(APIView):
    """View for managing pending registrations with role-based access"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get pending registrations based on user role and permissions"""
        user = request.user
        
        # Check user permissions
        if not self._has_permission_to_view_registrations(user):
            return Response(
                {'error': 'Access denied. Insufficient privileges to view pending registrations.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get status filter from query params
        status_filter = request.query_params.get('status', 'pending')
        
        # Get registrations based on user role
        registrations = self._get_registrations_for_user(user, status_filter)
        
        serializer = PendingRegistrationSerializer(registrations, many=True)
        return Response({
            'registrations': serializer.data,
            'total_count': registrations.count(),
            'user_role': self._get_user_role(user),
            'permissions': self._get_user_permissions(user)
        })
    
    def _has_permission_to_view_registrations(self, user):
        """Check if user has permission to view pending registrations"""
        # Admin/staff users always have access
        if user.is_staff or user.is_superuser:
            return True
        
        # Check if user has specific role-based permissions
        # You can extend this based on your role system
        if hasattr(user, 'role') and user.role in ['Admin', 'Manager']:
            return True
        
        # For now, allow authenticated users to view their own pending registrations
        # This can be customized based on your business logic
        return True
    
    def _get_registrations_for_user(self, user, status_filter):
        """Get registrations based on user role and permissions"""
        queryset = PendingRegistration.objects.all()
        
        # Admin/staff users can see all registrations
        if user.is_staff or user.is_superuser:
            return queryset.filter(status=status_filter)
        
        # Role-based filtering (extend based on your role system)
        if hasattr(user, 'role') and user.role in ['Admin', 'Manager']:
            return queryset.filter(status=status_filter)
        
        # Regular users can only see their own pending registrations
        # This is a fallback - you might want to restrict this further
        return queryset.filter(status=status_filter)
    
    def _get_user_role(self, user):
        """Get user's role for frontend display"""
        if user.is_superuser:
            return 'Super Admin'
        elif user.is_staff:
            return 'Admin'
        elif hasattr(user, 'role'):
            return user.role
        else:
            return 'User'
    
    def _get_user_permissions(self, user):
        """Get user's permissions for frontend display"""
        permissions = {
            'can_view_all': user.is_staff or user.is_superuser,
            'can_approve': user.is_staff or user.is_superuser,
            'can_reject': user.is_staff or user.is_superuser,
            'can_edit': user.is_staff or user.is_superuser,
        }
        return permissions


class ApproveRegistrationView(APIView):
    """View for approving a pending registration"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, registration_id):
        """Approve a pending registration"""
        user = request.user
        
        # Check if user has permission to approve
        if not self._has_permission_to_approve(user):
            return Response(
                {'error': 'Access denied. Insufficient privileges to approve registrations.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            registration = PendingRegistration.objects.get(
                id=registration_id, 
                status='pending'
            )
        except PendingRegistration.DoesNotExist:
            return Response(
                {'error': 'Pending registration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if OTP is verified
        if not registration.otp_verified:
            return Response(
                {'error': 'OTP must be verified before approval'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create the actual user
            user = CustomUser.objects.create_user(
                username=registration.username,
                email=registration.email,
                password='temp_password',  # Will be set by user later
                first_name=registration.first_name,
                last_name=registration.last_name,
                phone_number=registration.phone_number,
                date_of_birth=registration.date_of_birth,
                default_currency=registration.default_currency,
                monthly_income=registration.monthly_income,
                is_active=False  # User needs to set password first
            )
            
            # Update registration status
            registration.status = 'approved'
            registration.reviewed_at = timezone.now()
            registration.reviewed_by = request.user
            registration.save()
            
            # Create OTP for password setup
            otp = OTPVerification.create_otp(
                user=user, 
                purpose='password_reset', 
                expiry_minutes=30
            )
            
            # Send email with OTP and password setup instructions
            send_otp_email(user.email, otp.otp_code, 'password_reset')
            
            return Response({
                'message': 'Registration approved successfully',
                'user_id': user.id,
                'otp_id': otp.id
            })
    
    def _has_permission_to_approve(self, user):
        """Check if user has permission to approve registrations"""
        return user.is_staff or user.is_superuser or (hasattr(user, 'role') and user.role in ['Admin', 'Manager'])


class RejectRegistrationView(APIView):
    """View for rejecting a pending registration"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, registration_id):
        """Reject a pending registration"""
        user = request.user
        
        # Check if user has permission to reject
        if not self._has_permission_to_reject(user):
            return Response(
                {'error': 'Access denied. Insufficient privileges to reject registrations.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        try:
            registration = PendingRegistration.objects.get(
                id=registration_id, 
                status='pending'
            )
        except PendingRegistration.DoesNotExist:
            return Response(
                {'error': 'Pending registration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        registration.status = 'rejected'
        registration.reviewed_at = timezone.now()
        registration.reviewed_by = request.user
        registration.rejection_reason = rejection_reason
        registration.save()
        
        # Send rejection email to user
        send_registration_approval_email(
            registration.email, 
            registration.username, 
            'rejected', 
            rejection_reason
        )
        
        return Response({
            'message': 'Registration rejected successfully',
            'rejection_reason': rejection_reason
        })
    
    def _has_permission_to_reject(self, user):
        """Check if user has permission to reject registrations"""
        return user.is_staff or user.is_superuser or (hasattr(user, 'role') and user.role in ['Admin', 'Manager'])


class VerifyOTPView(APIView):
    """View for verifying OTP"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Verify OTP for registration or other purposes"""
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        otp_code = serializer.validated_data['otp_code']
        purpose = serializer.validated_data['purpose']
        
        # Handle registration OTP verification
        if purpose == 'email_verification':
            registration_id = request.data.get('registration_id')
            if not registration_id:
                return Response(
                    {'error': 'Registration ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                registration = PendingRegistration.objects.get(
                    id=registration_id, 
                    status='pending'
                )
            except PendingRegistration.DoesNotExist:
                return Response(
                    {'error': 'Pending registration not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if registration.verify_otp(otp_code):
                return Response({
                    'message': 'OTP verified successfully',
                    'registration_id': registration_id
                })
            else:
                return Response(
                    {'error': 'Invalid or expired OTP'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Handle user OTP verification
        else:
            user_id = request.data.get('user_id')
            if not user_id:
                return Response(
                    {'error': 'User ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return Response(
                    {'error': 'User not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            try:
                otp_verification = OTPVerification.objects.get(
                    user=user,
                    purpose=purpose,
                    otp_code=otp_code,
                    is_used=False
                )
            except OTPVerification.DoesNotExist:
                return Response(
                    {'error': 'Invalid or expired OTP'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if otp_verification.is_expired:
                return Response(
                    {'error': 'OTP has expired'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            otp_verification.mark_as_used()
            
            # Handle different purposes
            if purpose == 'password_reset':
                # Allow user to set new password
                new_password = request.data.get('new_password')
                if new_password:
                    try:
                        validate_password(new_password)
                        user.set_password(new_password)
                        user.is_active = True
                        user.save()
                        return Response({'message': 'Password reset successfully'})
                    except ValidationError as e:
                        return Response(
                            {'error': e.messages[0]}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    return Response({'message': 'OTP verified. Please set new password.'})
            
            elif purpose == 'phone_verification':
                user.is_verified = True
                user.save()
                return Response({'message': 'Phone number verified successfully'})
            
            return Response({'message': 'OTP verified successfully'})


class ResendOTPView(APIView):
    """View for resending OTP"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Resend OTP for registration or other purposes"""
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        purpose = serializer.validated_data['purpose']
        
        # Handle registration OTP resend
        if purpose == 'email_verification':
            registration_id = request.data.get('registration_id')
            if not registration_id:
                return Response(
                    {'error': 'Registration ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                registration = PendingRegistration.objects.get(
                    id=registration_id, 
                    status='pending'
                )
            except PendingRegistration.DoesNotExist:
                return Response(
                    {'error': 'Pending registration not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            otp_code = registration.generate_otp()
            
            # Send OTP via email
            send_otp_email(registration.email, otp_code, 'email_verification')
            
            return Response({
                'message': 'OTP sent successfully',
                'registration_id': registration_id
            })
        
        # Handle user OTP resend
        else:
            user_id = request.data.get('user_id')
            if not user_id:
                return Response(
                    {'error': 'User ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                return Response(
                    {'error': 'User not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            otp = OTPVerification.create_otp(user=user, purpose=purpose)
            
            # Send OTP via email or SMS based on purpose
            if purpose == 'phone_verification' and user.phone_number:
                send_otp_sms(user.phone_number, otp.otp_code, purpose)
            else:
                send_otp_email(user.email, otp.otp_code, purpose)
            
            return Response({
                'message': 'OTP sent successfully',
                'user_id': user_id
            })


class RegisterWithApprovalView(APIView):
    """View for registering users with approval workflow"""
    permission_classes = [permissions.AllowAny]
    
    @transaction.atomic
    def post(self, request):
        """Create a pending registration"""
        serializer = PendingRegistrationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        registration = serializer.save()
        
        # Generate OTP for verification
        otp_code = registration.generate_otp()
        
        # Send OTP via email
        send_otp_email(registration.email, otp_code, 'email_verification')
        
        return Response({
            'message': 'Registration submitted for approval. Please verify your email with the OTP sent.',
            'registration_id': registration.id,
            'otp_sent': True
        }, status=status.HTTP_201_CREATED)


class EnhancedRegistrationView(APIView):
    """Enhanced registration view with multi-step process and questbanker-app integration"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Handle enhanced registration with additional fields"""
        serializer = EnhancedRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Check if user already exists
        if CustomUser.objects.filter(username=data['username']).exists():
            return Response(
                {'error': 'Username already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if CustomUser.objects.filter(email=data['email']).exists():
            return Response(
                {'error': 'Email already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate password
        try:
            validate_password(data['password'])
        except ValidationError as e:
            return Response(
                {'error': e.messages[0]}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create pending registration with enhanced data
            registration = PendingRegistration.objects.create(
                username=data['username'],
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone_number=data.get('phone_number', ''),
                date_of_birth=data.get('date_of_birth'),
                default_currency=data.get('default_currency', 'UGX'),
                monthly_income=data.get('monthly_income'),
                # Store additional data in a JSON field or create related model
            )
            
            # Generate OTP for verification
            otp_code = registration.generate_otp()
            
            # Send OTP via email
            send_otp_email(registration.email, otp_code, 'email_verification')
            
            return Response({
                'message': 'Registration submitted successfully. Please verify your email.',
                'registration_id': registration.id,
                'otp_sent': True,
                'next_step': 'email_verification'
            }, status=status.HTTP_201_CREATED)


class RegistrationProgressView(APIView):
    """View for tracking registration progress"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, registration_id):
        """Get registration progress"""
        try:
            registration = PendingRegistration.objects.get(id=registration_id)
        except PendingRegistration.DoesNotExist:
            return Response(
                {'error': 'Registration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Define registration steps
        steps = [
            {'id': 'basic_info', 'name': 'Basic Information', 'completed': True},
            {'id': 'email_verification', 'name': 'Email Verification', 'completed': registration.otp_verified},
            {'id': 'admin_approval', 'name': 'Admin Approval', 'completed': registration.status == 'approved'},
            {'id': 'password_setup', 'name': 'Password Setup', 'completed': registration.status == 'approved'},
            {'id': 'onboarding', 'name': 'Onboarding', 'completed': False}
        ]
        
        current_step = 1
        if registration.otp_verified:
            current_step = 2
        if registration.status == 'approved':
            current_step = 3
        
        completed_steps = [step['id'] for step in steps if step['completed']]
        
        progress_data = {
            'step': current_step,
            'total_steps': len(steps),
            'current_step_name': steps[current_step - 1]['name'],
            'completed_steps': completed_steps,
            'next_step': steps[current_step]['name'] if current_step < len(steps) else None,
            'can_proceed': registration.otp_verified if current_step == 1 else True
        }
        
        serializer = RegistrationProgressSerializer(progress_data)
        return Response(serializer.data)


class RegistrationStatusView(APIView):
    """View for checking registration status"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, registration_id):
        """Get registration status and next actions"""
        try:
            registration = PendingRegistration.objects.get(id=registration_id)
        except PendingRegistration.DoesNotExist:
            return Response(
                {'error': 'Registration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = RegistrationStatusSerializer(registration)
        return Response(serializer.data)


class UserOnboardingView(APIView):
    """View for user onboarding after approval"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user onboarding status"""
        serializer = UserOnboardingSerializer(request.user)
        return Response(serializer.data)
    
    def post(self, request):
        """Update user onboarding information"""
        user = request.user
        data = request.data
        
        # Update onboarding fields
        allowed_fields = [
            'phone_number', 'date_of_birth', 'default_currency', 
            'monthly_income', 'profile_picture'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Handle phone verification
        if 'phone_number' in data and data['phone_number'] != user.phone_number:
            user.is_verified = False  # Reset verification status
        
        user.save()
        
        serializer = UserOnboardingSerializer(user)
        return Response({
            'message': 'Onboarding information updated successfully',
            'user': serializer.data
        })


class RegistrationAnalyticsView(APIView):
    """View for registration analytics (Admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get registration analytics"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Access denied. Admin privileges required.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Registration statistics
        total_registrations = PendingRegistration.objects.filter(
            submitted_at__gte=start_date
        ).count()
        
        pending_registrations = PendingRegistration.objects.filter(
            status='pending',
            submitted_at__gte=start_date
        ).count()
        
        approved_registrations = PendingRegistration.objects.filter(
            status='approved',
            submitted_at__gte=start_date
        ).count()
        
        rejected_registrations = PendingRegistration.objects.filter(
            status='rejected',
            submitted_at__gte=start_date
        ).count()
        
        # Daily registration trends
        daily_registrations = PendingRegistration.objects.filter(
            submitted_at__gte=start_date
        ).extra(
            select={'day': 'date(submitted_at)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')
        
        # Average approval time
        approved_with_review = PendingRegistration.objects.filter(
            status='approved',
            reviewed_at__isnull=False,
            submitted_at__gte=start_date
        )
        
        if approved_with_review.exists():
            avg_approval_time = approved_with_review.aggregate(
                avg_time=models.Avg(
                    models.F('reviewed_at') - models.F('submitted_at')
                )
            )['avg_time']
            avg_approval_hours = avg_approval_time.total_seconds() / 3600
        else:
            avg_approval_hours = 0
        
        analytics = {
            'period': f'Last {days} days',
            'total_registrations': total_registrations,
            'pending_registrations': pending_registrations,
            'approved_registrations': approved_registrations,
            'rejected_registrations': rejected_registrations,
            'approval_rate': (approved_registrations / total_registrations * 100) if total_registrations > 0 else 0,
            'average_approval_time_hours': round(avg_approval_hours, 2),
            'daily_trends': list(daily_registrations),
            'recent_registrations': PendingRegistrationSerializer(
                PendingRegistration.objects.filter(
                    submitted_at__gte=start_date
                ).order_by('-submitted_at')[:10], 
                many=True
            ).data
        }
        
        return Response(analytics)


class PasswordResetRequestView(APIView):
    """Request password reset via email"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Send password reset email"""
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Don't reveal if email exists or not for security
            return Response({
                'message': 'If an account with this email exists, a password reset link has been sent.'
            })
        
        # Generate password reset token
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create password reset record
        from .models import PasswordResetToken
        reset_token, created = PasswordResetToken.objects.get_or_create(
            user=user,
            defaults={'token': token, 'expires_at': timezone.now() + timezone.timedelta(hours=24)}
        )
        
        if not created:
            reset_token.token = token
            reset_token.expires_at = timezone.now() + timezone.timedelta(hours=24)
            reset_token.save()
        
        # Send password reset email
        try:
            from .utils import send_password_reset_email
            send_password_reset_email(user, token, uid)
        except Exception as e:
            return Response(
                {'error': 'Failed to send password reset email'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'message': 'Password reset email sent successfully'
        })


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Reset password with token"""
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        if not all([uidb64, token, new_password]):
            return Response(
                {'error': 'All fields are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.utils.http import urlsafe_base64_decode
            from django.contrib.auth.tokens import default_token_generator
            
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            
            # Verify token
            if not default_token_generator.check_token(user, token):
                return Response(
                    {'error': 'Invalid or expired token'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate new password
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password)
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Invalidate all password reset tokens
            from .models import PasswordResetToken
            PasswordResetToken.objects.filter(user=user).delete()
            
            return Response({
                'message': 'Password reset successfully'
            })
            
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response(
                {'error': 'Invalid reset link'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(
                {'error': e.messages[0]}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class EmailVerificationView(APIView):
    """Email verification view"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Send email verification"""
        user = request.user
        
        if user.is_verified:
            return Response(
                {'error': 'Email is already verified'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate verification token
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Send verification email
        try:
            from .utils import send_email_verification
            send_email_verification(user, token, uid)
        except Exception as e:
            return Response(
                {'error': 'Failed to send verification email'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'message': 'Verification email sent successfully'
        })


class EmailVerificationConfirmView(APIView):
    """Confirm email verification with token"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Verify email with token"""
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        
        if not all([uidb64, token]):
            return Response(
                {'error': 'All fields are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.utils.http import urlsafe_base64_decode
            from django.contrib.auth.tokens import default_token_generator
            
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            
            # Verify token
            if not default_token_generator.check_token(user, token):
                return Response(
                    {'error': 'Invalid or expired token'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark email as verified
            user.is_verified = True
            user.save()
            
            return Response({
                'message': 'Email verified successfully'
            })
            
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response(
                {'error': 'Invalid verification link'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
