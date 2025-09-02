from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'phone_number', 'NIN', 'profile_image', 'role', 'is_approved', 'first_login', 'first_name', 'last_name']

class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = ['username', 'phone_number', 'NIN', 'role', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        user = CustomUser.objects.create(
            username=validated_data['username'],
            phone_number=validated_data['phone_number'],
            NIN=validated_data['NIN'],
            role=validated_data['role'],
            first_name=validated_data.get('first_name', ''),  # added
            last_name=validated_data.get('last_name', '')     # added
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
