from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import PendingRegistration, OTPVerification, CustomUser, User, PendingUser

UserModel = get_user_model()


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
class CustomUserSerializer(serializers.ModelSerializer):
    """User serializer with profile information"""
    full_name = serializers.ReadOnlyField()
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserModel
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
        model = UserModel
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
        user = UserModel.objects.create_user(**validated_data)
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
        model = UserModel
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'default_currency', 'monthly_income'
        ]
    
    def validate_email(self, value):
        user = self.context['request'].user
        if UserModel.objects.exclude(pk=user.pk).filter(email=value).exists():
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
        if UserModel.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("Username already exists")
        
        if UserModel.objects.filter(email=attrs['email']).exists():
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


class EnhancedRegistrationSerializer(serializers.ModelSerializer):
    """Enhanced registration serializer with additional fields for questbanker-app integration"""
    
    # Additional fields for enhanced registration
    profile_picture = serializers.ImageField(required=False)
    address = serializers.CharField(max_length=500, required=False)
    city = serializers.CharField(max_length=100, required=False)
    country = serializers.CharField(max_length=100, required=False)
    postal_code = serializers.CharField(max_length=20, required=False)
    
    # Financial profile fields
    employment_status = serializers.ChoiceField(
        choices=[
            ('employed', 'Employed'),
            ('self_employed', 'Self Employed'),
            ('unemployed', 'Unemployed'),
            ('student', 'Student'),
            ('retired', 'Retired'),
        ],
        required=False
    )
    employer_name = serializers.CharField(max_length=200, required=False)
    job_title = serializers.CharField(max_length=100, required=False)
    
    # Banking preferences
    preferred_banking_hours = serializers.ChoiceField(
        choices=[
            ('morning', 'Morning (8AM-12PM)'),
            ('afternoon', 'Afternoon (12PM-5PM)'),
            ('evening', 'Evening (5PM-8PM)'),
            ('anytime', 'Anytime'),
        ],
        required=False
    )
    communication_preference = serializers.ChoiceField(
        choices=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('both', 'Both'),
        ],
        default='email'
    )
    
    # Terms and conditions
    terms_accepted = serializers.BooleanField(required=True)
    marketing_consent = serializers.BooleanField(default=False)
    
    class Meta:
        model = PendingRegistration
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'default_currency', 'monthly_income', 'profile_picture',
            'address', 'city', 'country', 'postal_code',
            'employment_status', 'employer_name', 'job_title',
            'preferred_banking_hours', 'communication_preference',
            'terms_accepted', 'marketing_consent'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True},
        }
    
    def validate_terms_accepted(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the terms and conditions")
        return value
    
    def validate(self, data):
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError("Passwords do not match")
        return data


class RegistrationProgressSerializer(serializers.Serializer):
    """Serializer for tracking registration progress"""
    step = serializers.IntegerField()
    total_steps = serializers.IntegerField()
    current_step_name = serializers.CharField()
    completed_steps = serializers.ListField(child=serializers.CharField())
    next_step = serializers.CharField(required=False)
    can_proceed = serializers.BooleanField()


class RegistrationStatusSerializer(serializers.ModelSerializer):
    """Serializer for registration status updates"""
    estimated_approval_time = serializers.SerializerMethodField()
    next_actions = serializers.SerializerMethodField()
    
    class Meta:
        model = PendingRegistration
        fields = [
            'id', 'status', 'submitted_at', 'reviewed_at',
            'estimated_approval_time', 'next_actions', 'otp_verified'
        ]
    
    def get_estimated_approval_time(self, obj):
        """Calculate estimated approval time based on business hours"""
        if obj.status == 'pending':
            # Return estimated time (e.g., "2-4 business hours")
            return "2-4 business hours"
        return None
    
    def get_next_actions(self, obj):
        """Return next actions for the user"""
        if obj.status == 'pending' and not obj.otp_verified:
            return ["Verify your email with the OTP sent"]
        elif obj.status == 'pending' and obj.otp_verified:
            return ["Wait for admin approval", "Check your email for updates"]
        elif obj.status == 'approved':
            return ["Set your password", "Complete your profile"]
        elif obj.status == 'rejected':
            return ["Review rejection reason", "Contact support if needed"]
        return []


class UserOnboardingSerializer(serializers.ModelSerializer):
    """Serializer for user onboarding after approval"""
    onboarding_completed = serializers.SerializerMethodField()
    onboarding_steps = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'is_verified', 'onboarding_completed',
            'onboarding_steps'
        ]
    
    def get_onboarding_completed(self, obj):
        """Check if user has completed onboarding"""
        # Define onboarding completion criteria
        required_fields = ['phone_number', 'date_of_birth']
        return all(getattr(obj, field) for field in required_fields)
    
    def get_onboarding_steps(self, obj):
        """Return onboarding steps and their completion status"""
        steps = [
            {
                'id': 'profile_completion',
                'name': 'Complete Profile',
                'completed': bool(obj.first_name and obj.last_name),
                'required': True
            },
            {
                'id': 'phone_verification',
                'name': 'Verify Phone Number',
                'completed': obj.is_verified,
                'required': True
            },
            {
                'id': 'financial_preferences',
                'name': 'Set Financial Preferences',
                'completed': bool(obj.default_currency and obj.monthly_income),
                'required': False
            },
            {
                'id': 'security_setup',
                'name': 'Security Setup',
                'completed': True,  # Assuming they've set password
                'required': True
            }
        ]
        return steps 