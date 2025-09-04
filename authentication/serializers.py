from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for general use"""
    roles_display = serializers.SerializerMethodField()
    accessible_dashboards = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone_number',
            'is_super_admin', 'is_agent', 'is_mse', 'is_partner',
            'is_approved', 'first_login', 'roles_display', 'accessible_dashboards'
        ]
        read_only_fields = ['id', 'is_approved', 'first_login']
    
    def get_roles_display(self, obj):
        """Get human-readable roles"""
        roles = []
        if obj.is_super_admin:
            roles.append('Super Admin')
        if obj.is_agent:
            roles.append('Agent')
        if obj.is_mse:
            roles.append('MSE')
        if obj.is_partner:
            roles.append('Partner')
        return ', '.join(roles) if roles else 'User'
    
    def get_accessible_dashboards(self, obj):
        """Get list of dashboards user can access"""
        return obj.get_accessible_dashboards()

class UserDetailSerializer(UserSerializer):
    """Detailed user serializer with additional fields"""
    assigned_agent = serializers.SerializerMethodField()
    assigned_users = serializers.SerializerMethodField()
    capabilities = serializers.ListField(read_only=True)
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'mse_name', 'partner_institution', 'assigned_agent', 
            'assigned_users', 'capabilities', 'date_joined'
        ]
    
    def get_assigned_agent(self, obj):
        """Get assigned agent details"""
        if obj.assigned_agent:
            return {
                'id': obj.assigned_agent.id,
                'username': obj.assigned_agent.username,
                'full_name': f"{obj.assigned_agent.first_name} {obj.assigned_agent.last_name}"
            }
        return None
    
    def get_assigned_users(self, obj):
        """Get users assigned to this agent"""
        if obj.is_agent:
            users = obj.get_assigned_users()
            return [{
                'id': user.id,
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}",
                'roles': user.roles_display
            } for user in users]
        return []

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone_number', 'NIN',
            'password', 'password_confirm', 'is_super_admin', 'is_agent', 'is_mse', 'is_partner',
            'mse_name', 'partner_institution'
        ]
    
    def validate(self, attrs):
        """Validate user creation data"""
        # Check password confirmation
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Default to MSE if no role specified
        if not any([attrs.get('is_super_admin'), attrs.get('is_agent'), 
                   attrs.get('is_mse'), attrs.get('is_partner')]):
            attrs['is_mse'] = True
        
        # Validate role-specific requirements
        if attrs.get('is_mse') and not attrs.get('mse_name'):
            raise serializers.ValidationError("MSE users must have an MSE name")
        
        if attrs.get('is_partner') and not attrs.get('partner_institution'):
            raise serializers.ValidationError("Partner users must have an institution name")
        
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users"""
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'NIN',
            'is_super_admin', 'is_agent', 'is_mse', 'is_partner',
            'mse_name', 'partner_institution', 'is_approved'
        ]
    
    def validate(self, attrs):
        """Validate update data"""
        # Validate role-specific requirements
        if attrs.get('is_mse') and not attrs.get('mse_name'):
            raise serializers.ValidationError("MSE users must have an MSE name")
        
        if attrs.get('is_partner') and not attrs.get('partner_institution'):
            raise serializers.ValidationError("Partner users must have an institution name")
        
        # At least one role must be selected
        if not any([attrs.get('is_super_admin'), attrs.get('is_agent'), 
                   attrs.get('is_mse'), attrs.get('is_partner')]):
            raise serializers.ValidationError("User must have at least one role")
        
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password change data"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        """Validate login credentials"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            if not user.is_approved:
                raise serializers.ValidationError("User account is not approved")
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Must include username and password")
        
        return attrs

class UserSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for user lists"""
    roles_display = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone_number',
            'is_super_admin', 'is_agent', 'is_mse', 'is_partner',
            'is_approved', 'roles_display'
        ]
    
    def get_roles_display(self, obj):
        """Get human-readable roles"""
        roles = []
        if obj.is_super_admin:
            roles.append('Super Admin')
        if obj.is_agent:
            roles.append('Agent')
        if obj.is_mse:
            roles.append('MSE')
        if obj.is_partner:
            roles.append('Partner')
        return ', '.join(roles) if roles else 'User'

class AgentAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for assigning users to agents"""
    assigned_agent = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(is_agent=True),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = CustomUser
        fields = ['assigned_agent']
    
    def validate_assigned_agent(self, value):
        """Validate agent assignment"""
        if value and not value.is_agent:
            raise serializers.ValidationError("Assigned user must be an agent")
        return value

class UserDashboardDataSerializer(serializers.ModelSerializer):
    """Serializer for user dashboard data"""
    roles_display = serializers.SerializerMethodField()
    accessible_dashboards = serializers.SerializerMethodField()
    capabilities = serializers.ListField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'is_super_admin', 'is_agent', 'is_mse', 'is_partner',
            'roles_display', 'accessible_dashboards', 'capabilities',
            'mse_name', 'partner_institution'
        ]
    
    def get_roles_display(self, obj):
        """Get human-readable roles"""
        roles = []
        if obj.is_super_admin:
            roles.append('Super Admin')
        if obj.is_agent:
            roles.append('Agent')
        if obj.is_mse:
            roles.append('MSE')
        if obj.is_partner:
            roles.append('Partner')
        return ', '.join(roles) if roles else 'User'
    
    def get_accessible_dashboards(self, obj):
        """Get list of dashboards user can access"""
        return obj.get_accessible_dashboards()
