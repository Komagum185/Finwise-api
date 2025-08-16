from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Customer, CustomerFeedback, SMSCampaign

User = get_user_model()


class CustomerSerializer(serializers.ModelSerializer):
    """Customer serializer with calculated fields"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    customer_tier = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'user', 'user_name', 'name', 'phone', 'email', 'location',
            'customer_type', 'customer_type_display', 'total_purchases', 'total_spent',
            'last_purchase', 'average_order_value', 'loyalty_points', 'rating',
            'status', 'status_display', 'notes', 'favorite_products', 'customer_tier',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'customer_type_display', 
                           'status_display', 'average_order_value', 'customer_tier',
                           'created_at', 'updated_at']
    
    def get_customer_tier(self, obj):
        return obj.get_customer_tier()
    
    def validate_phone(self, value):
        """Validate phone number uniqueness for the user"""
        user = self.context['request'].user
        if Customer.objects.filter(user=user, phone=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("A customer with this phone number already exists.")
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CustomerFeedbackSerializer(serializers.ModelSerializer):
    """Customer feedback serializer"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = CustomerFeedback
        fields = [
            'id', 'customer', 'customer_name', 'user', 'user_name', 'rating',
            'comment', 'product', 'date', 'created_at'
        ]
        read_only_fields = ['id', 'customer_name', 'user', 'user_name', 'created_at']
    
    def validate(self, data):
        """Validate feedback data"""
        if data.get('rating') and (data['rating'] < 1 or data['rating'] > 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SMSCampaignSerializer(serializers.ModelSerializer):
    """SMS campaign serializer"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_recipients = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = SMSCampaign
        fields = [
            'id', 'user', 'user_name', 'name', 'message', 'recipients',
            'scheduled_date', 'status', 'status_display', 'sent_date',
            'success_count', 'failure_count', 'total_recipients', 'success_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'status_display', 'sent_date',
                           'success_count', 'failure_count', 'total_recipients', 
                           'success_rate', 'created_at', 'updated_at']
    
    def get_total_recipients(self, obj):
        return obj.get_total_recipients()
    
    def get_success_rate(self, obj):
        return obj.get_success_rate()
    
    def validate_message(self, value):
        """Validate SMS message length"""
        if len(value.strip()) == 0:
            raise serializers.ValidationError("Message cannot be empty")
        if len(value) > 160:
            raise serializers.ValidationError("SMS message cannot exceed 160 characters")
        return value
    
    def validate_recipients(self, value):
        """Validate recipients list"""
        if not isinstance(value, list) or len(value) == 0:
            raise serializers.ValidationError("Recipients must be a non-empty list")
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# Summary and Analytics Serializers
class CustomerSummarySerializer(serializers.Serializer):
    """Customer summary statistics"""
    total_customers = serializers.IntegerField()
    active_customers = serializers.IntegerField()
    vip_customers = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    customer_growth_rate = serializers.FloatField()
    top_customers = serializers.ListField()
    recent_feedback = serializers.ListField()


class CustomerAnalyticsSerializer(serializers.Serializer):
    """Customer analytics data"""
    customer_types_breakdown = serializers.ListField()
    revenue_by_customer_type = serializers.ListField()
    customer_retention_rate = serializers.FloatField()
    average_customer_lifetime_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    customer_satisfaction_trends = serializers.ListField()
    loyalty_points_distribution = serializers.ListField()


class SMSCampaignSummarySerializer(serializers.Serializer):
    """SMS campaign summary statistics"""
    total_campaigns = serializers.IntegerField()
    sent_campaigns = serializers.IntegerField()
    draft_campaigns = serializers.IntegerField()
    average_success_rate = serializers.FloatField()
    total_recipients = serializers.IntegerField()
    total_successful_deliveries = serializers.IntegerField()
    recent_campaigns = serializers.ListField()
