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
from django.db import transaction
from django.utils import timezone

from .models import CustomUser, PendingRegistration, OTPVerification
from .serializers import (
    UserSerializer, PendingRegistrationSerializer, PendingRegistrationCreateSerializer,
    OTPVerificationSerializer, VerifyOTPSerializer, ResendOTPSerializer
)
from .utils import send_otp_email, send_otp_sms, send_registration_approval_email


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
    
    def post(self, request):
        """Authenticate user and return tokens"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Account is disabled'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


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
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user profile"""
        user = request.user
        data = request.data
        
        # Update allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'date_of_birth', 'default_currency', 'monthly_income'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Validate email uniqueness if changed
        if 'email' in data and data['email'] != user.email:
            if CustomUser.objects.filter(email=data['email']).exists():
                return Response(
                    {'error': 'Email already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        user.save()
        
        serializer = UserSerializer(user)
        return Response({
            'message': 'Profile updated successfully',
            'user': serializer.data
        })


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
    from api.models import Transaction, Budget, Goal
    
    stats = {
        'total_transactions': Transaction.objects.filter(user=user).count(),
        'total_budgets': Budget.objects.filter(user=user, is_active=True).count(),
        'active_goals': Goal.objects.filter(user=user, status='active').count(),
        'completed_goals': Goal.objects.filter(user=user, status='completed').count(),
    }
    
    return Response(stats)


class PendingRegistrationsView(APIView):
    """View for managing pending registrations (Admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get all pending registrations"""
        # Check if user is admin/staff
        if not request.user.is_staff:
            return Response(
                {'error': 'Access denied. Admin privileges required.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        status_filter = request.query_params.get('status', 'pending')
        registrations = PendingRegistration.objects.filter(status=status_filter)
        
        serializer = PendingRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)


class ApproveRegistrationView(APIView):
    """View for approving a pending registration"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, registration_id):
        """Approve a pending registration"""
        # Check if user is admin/staff
        if not request.user.is_staff:
            return Response(
                {'error': 'Access denied. Admin privileges required.'}, 
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


class RejectRegistrationView(APIView):
    """View for rejecting a pending registration"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, registration_id):
        """Reject a pending registration"""
        # Check if user is admin/staff
        if not request.user.is_staff:
            return Response(
                {'error': 'Access denied. Admin privileges required.'}, 
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
