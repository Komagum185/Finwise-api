from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from .models import SalesData, ProductPerformance, MarketTrends, Predictions

User = get_user_model()


class SalesDataSerializer(serializers.ModelSerializer):
    """Sales data serializer with calculated fields"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    growth_rate = serializers.SerializerMethodField()
    customer_retention_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesData
        fields = [
            'id', 'user', 'user_name', 'date', 'revenue', 'orders', 'customers',
            'average_order_value', 'growth_rate', 'customer_retention_rate', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'growth_rate', 'customer_retention_rate', 'created_at']
    
    def get_growth_rate(self, obj):
        """Calculate growth rate compared to previous day"""
        previous_date = obj.date - timedelta(days=1)
        return obj.get_growth_rate(previous_date)
    
    def get_customer_retention_rate(self, obj):
        """Calculate customer retention rate compared to previous day"""
        previous_date = obj.date - timedelta(days=1)
        return obj.get_customer_retention_rate(previous_date)
    
    def validate(self, data):
        """Validate sales data"""
        if data.get('revenue') and data['revenue'] < 0:
            raise serializers.ValidationError("Revenue cannot be negative")
        if data.get('orders') and data['orders'] < 0:
            raise serializers.ValidationError("Orders cannot be negative")
        if data.get('customers') and data['customers'] < 0:
            raise serializers.ValidationError("Customers cannot be negative")
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProductPerformanceSerializer(serializers.ModelSerializer):
    """Product performance serializer with calculated fields"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    performance_score = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductPerformance
        fields = [
            'id', 'user', 'user_name', 'product_name', 'sales', 'revenue', 'growth',
            'category', 'period', 'period_display', 'performance_score', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'period_display', 'performance_score', 'created_at']
    
    def get_performance_score(self, obj):
        return obj.get_performance_score()
    
    def validate(self, data):
        """Validate product performance data"""
        if data.get('sales') and data['sales'] < 0:
            raise serializers.ValidationError("Sales cannot be negative")
        if data.get('revenue') and data['revenue'] < 0:
            raise serializers.ValidationError("Revenue cannot be negative")
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MarketTrendsSerializer(serializers.ModelSerializer):
    """Market trends serializer with calculated fields"""
    impact_display = serializers.CharField(source='get_impact_display', read_only=True)
    impact_score = serializers.SerializerMethodField()
    is_high_confidence = serializers.SerializerMethodField()
    is_critical_trend = serializers.SerializerMethodField()
    
    class Meta:
        model = MarketTrends
        fields = [
            'id', 'trend', 'impact', 'impact_display', 'description', 'confidence',
            'region', 'impact_score', 'is_high_confidence', 'is_critical_trend', 'created_at'
        ]
        read_only_fields = ['id', 'impact_display', 'impact_score', 'is_high_confidence', 'is_critical_trend', 'created_at']
    
    def get_impact_score(self, obj):
        return obj.get_impact_score()
    
    def get_is_high_confidence(self, obj):
        return obj.is_high_confidence()
    
    def get_is_critical_trend(self, obj):
        return obj.is_critical_trend()
    
    def validate_confidence(self, value):
        """Validate confidence percentage"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Confidence must be between 0 and 100")
        return value


class PredictionsSerializer(serializers.ModelSerializer):
    """Predictions serializer with calculated fields"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    trend_display = serializers.CharField(source='get_trend_display', read_only=True)
    change_percentage = serializers.SerializerMethodField()
    is_high_confidence_prediction = serializers.SerializerMethodField()
    prediction_category = serializers.SerializerMethodField()
    
    class Meta:
        model = Predictions
        fields = [
            'id', 'user', 'user_name', 'metric', 'current_value', 'predicted_value',
            'confidence', 'trend', 'trend_display', 'prediction_date', 'change_percentage',
            'is_high_confidence_prediction', 'prediction_category', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'trend_display', 'change_percentage',
                           'is_high_confidence_prediction', 'prediction_category', 'created_at']
    
    def get_change_percentage(self, obj):
        return obj.get_change_percentage()
    
    def get_is_high_confidence_prediction(self, obj):
        return obj.is_high_confidence_prediction()
    
    def get_prediction_category(self, obj):
        return obj.get_prediction_category()
    
    def validate(self, data):
        """Validate prediction data"""
        if data.get('current_value') and data['current_value'] < 0:
            raise serializers.ValidationError("Current value cannot be negative")
        if data.get('predicted_value') and data['predicted_value'] < 0:
            raise serializers.ValidationError("Predicted value cannot be negative")
        if data.get('confidence') and (data['confidence'] < 0 or data['confidence'] > 100):
            raise serializers.ValidationError("Confidence must be between 0 and 100")
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# Summary and Analytics Serializers
class SalesSummarySerializer(serializers.Serializer):
    """Sales summary statistics"""
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_orders = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    revenue_growth_rate = serializers.FloatField()
    customer_growth_rate = serializers.FloatField()
    recent_sales_data = serializers.ListField()


class ProductPerformanceSummarySerializer(serializers.Serializer):
    """Product performance summary statistics"""
    total_products = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_growth_rate = serializers.FloatField()
    top_performing_products = serializers.ListField()
    category_breakdown = serializers.ListField()


class MarketTrendsSummarySerializer(serializers.Serializer):
    """Market trends summary statistics"""
    total_trends = serializers.IntegerField()
    positive_trends = serializers.IntegerField()
    negative_trends = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    critical_trends = serializers.ListField()
    regional_breakdown = serializers.ListField()


class PredictionsSummarySerializer(serializers.Serializer):
    """Predictions summary statistics"""
    total_predictions = serializers.IntegerField()
    high_confidence_predictions = serializers.IntegerField()
    average_confidence = serializers.FloatField()
    trend_breakdown = serializers.ListField()
    recent_predictions = serializers.ListField()


class BusinessIntelligenceSerializer(serializers.Serializer):
    """Comprehensive business intelligence data"""
    sales_summary = SalesSummarySerializer()
    product_performance = ProductPerformanceSummarySerializer()
    market_trends = MarketTrendsSummarySerializer()
    predictions = PredictionsSummarySerializer()
    key_insights = serializers.ListField()
    recommendations = serializers.ListField()

