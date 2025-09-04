from rest_framework import serializers
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for general use"""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    rights_display = serializers.CharField(source='get_rights_display', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone_number',
            'role', 'role_display', 'rights', 'rights_display', 'is_approved',
            'mse_name', 'partner_institution', 'assigned_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer for admin use"""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    rights_display = serializers.CharField(source='get_rights_display', read_only=True)
    assigned_users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone_number',
            'NIN', 'profile_image', 'role', 'role_display', 'rights', 'rights_display',
            'is_approved', 'first_login', 'mse_name', 'partner_institution',
            'assigned_agent', 'assigned_users_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_assigned_users_count(self, obj):
        """Get count of users assigned to this agent"""
        if obj.role == 'agent':
            return obj.assigned_mse_users.count()
        return 0


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email', 'phone_number',
            'NIN', 'password', 'confirm_password', 'role', 'mse_name',
            'partner_institution', 'assigned_agent'
        ]
    
    def validate(self, attrs):
        """Validate password confirmation and role-specific fields"""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Validate role-specific requirements
        role = attrs.get('role')
        if role == 'mse' and not attrs.get('mse_name'):
            raise serializers.ValidationError("MSE users must have an MSE name")
        
        if role == 'partner' and not attrs.get('partner_institution'):
            raise serializers.ValidationError("Partner users must have an institution name")
        
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('confirm_password')
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
            'first_name', 'last_name', 'email', 'phone_number', 'profile_image',
            'mse_name', 'partner_institution', 'assigned_agent', 'is_approved'
        ]
    
    def validate(self, attrs):
        """Validate role-specific requirements"""
        user = self.instance
        role = user.role
        
        if role == 'mse' and not attrs.get('mse_name'):
            raise serializers.ValidationError("MSE users must have an MSE name")
        
        if role == 'partner' and not attrs.get('partner_institution'):
            raise serializers.ValidationError("Partner users must have an institution name")
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserSummarySerializer(serializers.ModelSerializer):
    """Lightweight user serializer for lists and summaries"""
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'full_name', 'role', 'role_display',
            'is_approved', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class AgentAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for agent assignment operations"""
    
    assigned_users = UserSummarySerializer(source='assigned_mse_users', many=True, read_only=True)
    assigned_users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'first_name', 'last_name', 'role',
            'assigned_users', 'assigned_users_count'
        ]
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'role']
    
    def get_assigned_users_count(self, obj):
        return obj.assigned_mse_users.count()
