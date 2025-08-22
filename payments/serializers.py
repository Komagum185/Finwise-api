from rest_framework import serializers
from .models import PaymentProvider, QRPayment, ScheduledTransfer, PaymentTransaction


class PaymentProviderSerializer(serializers.ModelSerializer):
    """Serializer for PaymentProvider"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentProvider
        fields = [
            'id', 'name', 'provider_id', 'type', 'type_display', 'country', 'currency',
            'fee_percentage', 'fee_fixed', 'min_amount', 'max_amount', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentProviderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PaymentProvider"""
    
    class Meta:
        model = PaymentProvider
        fields = [
            'name', 'provider_id', 'type', 'country', 'currency',
            'fee_percentage', 'fee_fixed', 'min_amount', 'max_amount',
            'api_key', 'api_secret', 'webhook_url', 'status'
        ]
    
    def validate_provider_id(self, value):
        """Validate provider_id is unique"""
        if PaymentProvider.objects.filter(provider_id=value).exists():
            raise serializers.ValidationError("Provider ID already exists")
        return value


class QRPaymentSerializer(serializers.ModelSerializer):
    """Serializer for QRPayment"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = QRPayment
        fields = [
            'id', 'user', 'amount', 'currency', 'description', 'qr_code', 'qr_url',
            'status', 'status_display', 'created_at', 'expires_at', 'completed_at',
            'provider', 'provider_name', 'transaction_id', 'payer_phone', 'payer_name',
            'is_expired'
        ]
        read_only_fields = ['id', 'user', 'qr_code', 'qr_url', 'created_at', 'completed_at', 'is_expired']
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class QRPaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating QRPayment"""
    
    class Meta:
        model = QRPayment
        fields = ['amount', 'currency', 'description', 'provider']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Set expiry time (30 minutes from now)
        from django.utils import timezone
        from datetime import timedelta
        validated_data['expires_at'] = timezone.now() + timedelta(minutes=30)
        
        # Generate QR code (placeholder - would be implemented with actual QR generation)
        validated_data['qr_code'] = f"QR_CODE_{validated_data['amount']}_{validated_data['currency']}"
        
        return super().create(validated_data)


class ScheduledTransferSerializer(serializers.ModelSerializer):
    """Serializer for ScheduledTransfer"""
    frequency_display = serializers.CharField(source='get_frequency_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    is_due = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduledTransfer
        fields = [
            'id', 'user', 'from_wallet', 'to_wallet', 'phone_number', 'amount', 'currency',
            'description', 'frequency', 'frequency_display', 'next_execution', 'last_execution',
            'status', 'status_display', 'provider', 'provider_name', 'created_at', 'updated_at',
            'is_due'
        ]
        read_only_fields = ['id', 'user', 'last_execution', 'created_at', 'updated_at', 'is_due']
    
    def get_is_due(self, obj):
        return obj.is_due()


class ScheduledTransferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ScheduledTransfer"""
    
    class Meta:
        model = ScheduledTransfer
        fields = [
            'from_wallet', 'to_wallet', 'phone_number', 'amount', 'currency',
            'description', 'frequency', 'next_execution', 'provider'
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
    
    def validate(self, attrs):
        """Validate transfer data"""
        # Ensure either to_wallet or phone_number is provided
        if not attrs.get('to_wallet') and not attrs.get('phone_number'):
            raise serializers.ValidationError("Either to_wallet or phone_number must be provided")
        
        # Validate amount
        if attrs['amount'] <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        
        return attrs


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for PaymentTransaction"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'user', 'type', 'type_display', 'amount', 'currency', 'fees', 'net_amount',
            'provider', 'provider_name', 'reference', 'external_transaction_id', 'status',
            'status_display', 'created_at', 'processed_at', 'qr_payment', 'scheduled_transfer',
            'description', 'metadata'
        ]
        read_only_fields = [
            'id', 'user', 'fees', 'net_amount', 'reference', 'external_transaction_id',
            'created_at', 'processed_at', 'metadata'
        ]


class PaymentTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PaymentTransaction"""
    
    class Meta:
        model = PaymentTransaction
        fields = ['type', 'amount', 'currency', 'provider', 'description', 'qr_payment', 'scheduled_transfer']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Calculate fees and net amount
        provider = validated_data.get('provider')
        if provider:
            fees = provider.calculate_fees(validated_data['amount'])
            validated_data['fees'] = fees
            validated_data['net_amount'] = validated_data['amount'] - fees
        
        # Generate reference
        import uuid
        validated_data['reference'] = f"PAY_{uuid.uuid4().hex[:8].upper()}"
        
        return super().create(validated_data)


class PaymentStatisticsSerializer(serializers.Serializer):
    """Serializer for payment statistics"""
    total_transactions = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_fees = serializers.DecimalField(max_digits=10, decimal_places=2)
    success_rate = serializers.FloatField()
    currency = serializers.CharField()
    period = serializers.CharField()


class QRPaymentStatusSerializer(serializers.Serializer):
    """Serializer for QR payment status check"""
    qr_payment_id = serializers.UUIDField()
    
    def validate_qr_payment_id(self, value):
        """Validate QR payment exists"""
        try:
            QRPayment.objects.get(id=value)
        except QRPayment.DoesNotExist:
            raise serializers.ValidationError("QR payment not found")
        return value


class ScheduledTransferStatusSerializer(serializers.Serializer):
    """Serializer for scheduled transfer status update"""
    scheduled_transfer_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=ScheduledTransfer.STATUS_CHOICES)
    
    def validate_scheduled_transfer_id(self, value):
        """Validate scheduled transfer exists"""
        try:
            ScheduledTransfer.objects.get(id=value)
        except ScheduledTransfer.DoesNotExist:
            raise serializers.ValidationError("Scheduled transfer not found")
        return value
