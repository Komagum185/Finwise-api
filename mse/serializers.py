from rest_framework import serializers
from .models import MSECategory, MSE, Wallet


class MSECategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MSECategory
        fields = ['id', 'name', 'description', 'created_at']


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'currency', 'created_at', 'updated_at']


class MSESerializer(serializers.ModelSerializer):
    wallet = WalletSerializer(read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=MSECategory.objects.all())

    class Meta:
        model = MSE
        fields = [
            'id', 'owner', 'first_name', 'last_name', 'nin', 'phone', 'email',
            'profile_image', 'category', 'location', 'status', 'created_at', 'updated_at', 'wallet'
        ]
        read_only_fields = ['owner', 'status']

    def create(self, validated_data):
        request = self.context['request']
        mse = MSE.objects.create(owner=request.user, **validated_data)
        Wallet.objects.create(mse=mse)
        return mse


