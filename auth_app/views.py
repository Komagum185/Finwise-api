from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db import transaction
from .models import CustomUser, PendingRegistration, OTPVerification
from .serializers import (
    CustomUserSerializer, UserRegistrationSerializer, EnhancedRegistrationSerializer,
    RegistrationProgressSerializer, RegistrationStatusSerializer, UserOnboardingSerializer,
    OTPVerificationSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer,
    UserProfileUpdateSerializer
)


class UserRegistrationView(APIView):
    """User registration view"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User registered successfully',
                'user': CustomUserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnhancedRegistrationView(APIView):
    """Enhanced registration view with multi-step process and admin approval"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = EnhancedRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # Create pending registration
                    registration = serializer.save()
                    
                    # Generate OTP
                    otp_code = registration.generate_otp()
                    
                    # TODO: Send OTP via email/SMS
                    # For now, we'll just return it in the response
                    
                    return Response({
                        'message': 'Registration submitted successfully. Please verify OTP and wait for admin approval.',
                        'registration_id': str(registration.id),
                        'otp_sent': True,
                        'otp_code': otp_code,  # Remove this in production
                        'next_steps': [
                            'Verify OTP',
                            'Wait for admin approval',
                            'Complete onboarding after approval'
                        ]
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                return Response({
                    'error': 'Registration failed',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegistrationProgressView(APIView):
    """View to check registration progress"""
    permission_classes = [AllowAny]
    
    def get(self, request, registration_id):
        try:
            registration = PendingRegistration.objects.get(id=registration_id)
            serializer = RegistrationProgressSerializer(registration)
            
            # Determine next steps based on current status
            next_steps = []
            if not registration.otp_verified:
                next_steps.append('Verify OTP')
            elif registration.status == 'pending':
                next_steps.append('Wait for admin approval')
            elif registration.status == 'approved':
                next_steps.append('Complete onboarding')
            elif registration.status == 'rejected':
                next_steps.append('Review rejection reason and resubmit if needed')
            
            return Response({
                'registration': serializer.data,
                'next_steps': next_steps,
                'progress_percentage': self._calculate_progress(registration)
            })
            
        except PendingRegistration.DoesNotExist:
            return Response({
                'error': 'Registration not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _calculate_progress(self, registration):
        """Calculate registration progress percentage"""
        steps = ['submitted', 'otp_verified', 'admin_reviewed', 'finalized']
        current_step = 0
        
        if registration.submitted_at:
            current_step += 1
        if registration.otp_verified:
            current_step += 1
        if registration.reviewed_at:
            current_step += 1
        if registration.status in ['approved', 'rejected']:
            current_step += 1
        
        return (current_step / len(steps)) * 100


class RegistrationStatusView(APIView):
    """View to get detailed registration status"""
    permission_classes = [AllowAny]
    
    def get(self, request, registration_id):
        try:
            registration = PendingRegistration.objects.get(id=registration_id)
            serializer = RegistrationStatusSerializer(registration)
            
            # Get status-specific information
            status_info = self._get_status_info(registration)
            
            return Response({
                'registration': serializer.data,
                'status_info': status_info,
                'timeline': self._get_timeline(registration)
            })
            
        except PendingRegistration.DoesNotExist:
            return Response({
                'error': 'Registration not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _get_status_info(self, registration):
        """Get information specific to current status"""
        if registration.status == 'pending':
            return {
                'message': 'Your registration is under review',
                'estimated_time': '1-2 business days',
                'actions_required': ['Verify OTP', 'Wait for admin review']
            }
        elif registration.status == 'approved':
            return {
                'message': 'Your registration has been approved!',
                'actions_required': ['Complete onboarding', 'Set up your account']
            }
        elif registration.status == 'rejected':
            return {
                'message': 'Your registration was not approved',
                'reason': registration.rejection_reason,
                'actions_required': ['Review feedback', 'Resubmit if needed']
            }
        
        return {}
    
    def _get_timeline(self, registration):
        """Get registration timeline"""
        timeline = [
            {
                'step': 'Registration Submitted',
                'timestamp': registration.submitted_at,
                'status': 'completed'
            }
        ]
        
        if registration.otp_verified:
            timeline.append({
                'step': 'OTP Verified',
                'timestamp': registration.otp_created_at,
                'status': 'completed'
            })
        
        if registration.reviewed_at:
            timeline.append({
                'step': 'Admin Review',
                'timestamp': registration.reviewed_at,
                'status': 'completed'
            })
        
        return timeline


class UserOnboardingView(APIView):
    """View for user onboarding after registration approval"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current onboarding status"""
        user = request.user
        serializer = CustomUserSerializer(user)
        
        onboarding_status = {
            'is_complete': user.onboarding_completed,
            'completed_at': user.onboarding_completed_at,
            'required_fields': self._get_required_fields(user),
            'completed_fields': self._get_completed_fields(user),
            'progress_percentage': self._calculate_onboarding_progress(user)
        }
        
        return Response({
            'user': serializer.data,
            'onboarding_status': onboarding_status
        })
    
    def put(self, request):
        """Update onboarding information"""
        user = request.user
        serializer = UserOnboardingSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'message': 'Onboarding information updated successfully',
                'user': CustomUserSerializer(user).data,
                'onboarding_complete': user.onboarding_completed
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_required_fields(self, user):
        """Get list of required onboarding fields"""
        return [
            'phone_number', 'date_of_birth', 'first_name', 'last_name',
            'address', 'city', 'country', 'postal_code'
        ]
    
    def _get_completed_fields(self, user):
        """Get list of completed onboarding fields"""
        required_fields = self._get_required_fields(user)
        completed = []
        
        for field in required_fields:
            if getattr(user, field):
                completed.append(field)
        
        return completed
    
    def _calculate_onboarding_progress(self, user):
        """Calculate onboarding progress percentage"""
        required_fields = self._get_required_fields(user)
        completed_fields = self._get_completed_fields(user)
        
        if not required_fields:
            return 100
        
        return (len(completed_fields) / len(required_fields)) * 100


class RegistrationAnalyticsView(APIView):
    """Admin view for registration analytics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get registration analytics"""
        total_registrations = PendingRegistration.objects.count()
        pending_count = PendingRegistration.objects.filter(status='pending').count()
        approved_count = PendingRegistration.objects.filter(status='approved').count()
        rejected_count = PendingRegistration.objects.filter(status='rejected').count()
        
        # Recent registrations
        recent_registrations = PendingRegistration.objects.order_by('-submitted_at')[:10]
        recent_serializer = RegistrationProgressSerializer(recent_registrations, many=True)
        
        # Status distribution
        status_distribution = {
            'pending': pending_count,
            'approved': approved_count,
            'rejected': rejected_count
        }
        
        # Monthly trends (last 6 months)
        monthly_trends = self._get_monthly_trends()
        
        return Response({
            'overview': {
                'total_registrations': total_registrations,
                'pending_count': pending_count,
                'approved_count': approved_count,
                'rejected_count': rejected_count,
                'approval_rate': (approved_count / total_registrations * 100) if total_registrations > 0 else 0
            },
            'status_distribution': status_distribution,
            'recent_registrations': recent_serializer.data,
            'monthly_trends': monthly_trends
        })
    
    def _get_monthly_trends(self):
        """Get monthly registration trends"""
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        
        monthly_data = PendingRegistration.objects.annotate(
            month=TruncMonth('submitted_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')[:6]
        
        return [
            {
                'month': item['month'].strftime('%B %Y'),
                'count': item['count']
            }
            for item in monthly_data
        ]


class LoginView(APIView):
    """User login view"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful',
                'user': CustomUserSerializer(user).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            })
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(APIView):
    """User profile view"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user profile"""
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user profile"""
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': CustomUserSerializer(user).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """User logout view"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Logout successful'
            })
        except Exception as e:
            return Response({
                'error': 'Logout failed',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
