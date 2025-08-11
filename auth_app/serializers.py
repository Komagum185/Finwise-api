from rest_framework import serializers
from .models import PendingRegistration, OTPVerification, User, PendingUser


# New serializers matching TypeScript interfaces exactly
class UserSerializer(serializers.ModelSerializer):
    """User serializer matching TypeScript User interface exactly"""
    
    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'role', 'mse_type', 'mse_code', 
            'phone', 'company', 'location'
        ]
        read_only_fields = ['id']


class PendingUserSerializer(serializers.ModelSerializer):
    """PendingUser serializer matching TypeScript PendingUser interface exactly"""
    
    class Meta:
        model = PendingUser
        fields = [
            'id', 'name', 'email', 'phone', 'company', 'mse_type', 
            'registration_date', 'status'
        ]
        read_only_fields = ['id', 'registration_date']


class RegisterFormDataSerializer(serializers.ModelSerializer):
    """RegisterFormData serializer matching TypeScript RegisterFormData interface exactly"""
    
    class Meta:
        model = PendingUser
        fields = [
            'name', 'email', 'phone', 'company', 'mse_type',
            'gender', 'branch_id', 'group_id', 'cause', 'nationality',
            'send_sms', 'subscribe', 'company_id'
        ]
    
    def validate_mse_type(self, value):
        """Validate MSE type is not empty"""
        if not value:
            raise serializers.ValidationError("MSE type is required")
        return value


# Legacy serializers for backward compatibility
class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'name', 'email', 'password', 'confirm_password', 'phone', 'company', 'mse_type'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create(**validated_data)
        return user


class EnhancedRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for enhanced user registration with multi-step process"""
    
    class Meta:
        model = PendingRegistration
        fields = [
            'username', 'email', 'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'default_currency', 'monthly_income'
        ]
    
    def validate_email(self, value):
        """Check if email is already in use"""
        from users.models import CustomUser
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        if PendingRegistration.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already has a pending registration")
        return value
    
    def validate_username(self, value):
        """Check if username is already in use"""
        from users.models import CustomUser
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already taken")
        if PendingRegistration.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already has a pending registration")
        return value


class RegistrationProgressSerializer(serializers.ModelSerializer):
    """Serializer for registration progress tracking"""
    
    class Meta:
        model = PendingRegistration
        fields = [
            'id', 'username', 'email', 'status', 'submitted_at', 'otp_verified',
            'reviewed_at', 'reviewed_by', 'rejection_reason'
        ]
        read_only_fields = ['id', 'submitted_at', 'reviewed_at', 'reviewed_by']


class RegistrationStatusSerializer(serializers.ModelSerializer):
    """Serializer for detailed registration status"""
    
    class Meta:
        model = PendingRegistration
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'status',
            'submitted_at', 'otp_verified', 'reviewed_at', 'reviewed_by',
            'rejection_reason', 'phone_number', 'date_of_birth', 'default_currency',
            'monthly_income'
        ]
        read_only_fields = ['id', 'submitted_at', 'reviewed_at', 'reviewed_by']


class UserOnboardingSerializer(serializers.ModelSerializer):
    """Serializer for user onboarding updates"""
    
    class Meta:
        model = User
        fields = [
            'phone', 'company', 'mse_type', 'mse_code', 'location'
        ]


class OTPVerificationSerializer(serializers.ModelSerializer):
    """Serializer for OTP verification"""
    
    class Meta:
        model = OTPVerification
        fields = ['id', 'user', 'purpose', 'otp_code', 'created_at', 'expires_at', 'is_used']
        read_only_fields = ['id', 'user', 'purpose', 'created_at', 'expires_at', 'is_used']


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        from users.models import CustomUser
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for user profile updates"""
    
    class Meta:
        model = User
        fields = [
            'name', 'phone', 'company', 'mse_type', 'mse_code', 'location'
        ]
