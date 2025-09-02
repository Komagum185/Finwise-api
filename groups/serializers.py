from rest_framework import serializers
from .models import Group, GroupMembership, GroupWallet


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'description', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']

    def create(self, validated_data):
        request = self.context['request']
        return Group.objects.create(created_by=request.user, **validated_data)


class GroupMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupMembership
        fields = ['id', 'group', 'mse', 'joined_at', 'is_active']
        read_only_fields = ['joined_at']


class GroupWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupWallet
        fields = ['id', 'group', 'balance', 'currency', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


