from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import PendingRegistration, OTPVerification

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer with profile information"""
    full_name = serializers.ReadOnlyField()
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'date_of_birth', 'is_verified', 'profile_picture_url',
            'default_currency', 'monthly_income', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_verified']
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
        return None


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'default_currency', 'monthly_income'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'default_currency', 'monthly_income'
        ]
    
    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class PendingRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for pending registrations"""
    reviewed_by_name = serializers.ReadOnlyField(source='reviewed_by.full_name')
    
    class Meta:
        model = PendingRegistration
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'default_currency', 'monthly_income', 'status',
            'submitted_at', 'reviewed_at', 'reviewed_by', 'reviewed_by_name',
            'rejection_reason', 'otp_verified'
        ]
        read_only_fields = [
            'id', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by',
            'reviewed_by_name', 'rejection_reason', 'otp_verified'
        ]


class PendingRegistrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating pending registrations"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = PendingRegistration
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'default_currency', 'monthly_income'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Check if username or email already exists in users or pending registrations
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("Username already exists")
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already exists")
        
        if PendingRegistration.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("Username already has a pending registration")
        
        if PendingRegistration.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already has a pending registration")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password')
        validated_data.pop('password_confirm')
        return PendingRegistration.objects.create(**validated_data)


class OTPVerificationSerializer(serializers.ModelSerializer):
    """Serializer for OTP verification"""
    
    class Meta:
        model = OTPVerification
        fields = ['id', 'purpose', 'created_at', 'expires_at', 'is_used']
        read_only_fields = ['id', 'purpose', 'created_at', 'expires_at', 'is_used']


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    otp_code = serializers.CharField(max_length=6, min_length=6)
    purpose = serializers.ChoiceField(choices=OTPVerification.PURPOSE_CHOICES)


class ResendOTPSerializer(serializers.Serializer):
    """Serializer for resending OTP"""
    purpose = serializers.ChoiceField(choices=OTPVerification.PURPOSE_CHOICES) 