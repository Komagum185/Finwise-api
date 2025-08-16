from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from .models import (
    Category, Budget, Goal, Transaction, UserProfile, RecurringTransaction, BusinessHealth
)

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
            'default_currency', 'monthly_income', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'is_verified']
    
    def get_profile_picture_url(self, obj):
        if obj.profile_picture:
            return self.context['request'].build_absolute_uri(obj.profile_picture.url)
        return None


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer with validation"""
    transaction_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'category_type', 'icon', 'color',
            'is_active', 'transaction_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'transaction_count']
    
    def get_transaction_count(self, obj):
        return obj.transactions.count()
    
    def validate_name(self, value):
        """Ensure category name is unique"""
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value


class BudgetSerializer(serializers.ModelSerializer):
    """Budget serializer with calculated fields"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    spent_amount = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()
    spent_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Budget
        fields = [
            'id', 'user', 'category', 'category_name', 'amount', 'period',
            'start_date', 'end_date', 'is_active', 'spent_amount',
            'remaining_amount', 'spent_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'spent_amount', 'remaining_amount', 
                           'spent_percentage', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate budget data"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("End date must be after start date.")
        
        # Check for overlapping budgets
        if Budget.objects.filter(
            user=self.context['request'].user,
            category=data['category'],
            start_date__lte=data['start_date'],
            end_date__gte=data['start_date'],
            is_active=True
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Budget period overlaps with existing budget.")
        
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class GoalSerializer(serializers.ModelSerializer):
    """Goal serializer with progress tracking"""
    progress_percentage = serializers.ReadOnlyField()
    remaining_amount = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = Goal
        fields = [
            'id', 'user', 'name', 'description', 'goal_type', 'target_amount',
            'current_amount', 'target_date', 'status', 'priority',
            'progress_percentage', 'remaining_amount', 'is_completed',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'progress_percentage', 'remaining_amount',
                           'is_completed', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate goal data"""
        if data.get('target_date'):
            from django.utils import timezone
            if data['target_date'] < timezone.now().date():
                raise serializers.ValidationError("Target date cannot be in the past.")
        
        if data.get('current_amount') and data.get('target_amount'):
            if data['current_amount'] > data['target_amount']:
                raise serializers.ValidationError("Current amount cannot exceed target amount.")
        
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    """Enhanced transaction serializer with validation"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'user_name', 'amount', 'description', 'transaction_type',
            'transaction_type_display', 'category', 'category_name', 'date', 
            'payment_method', 'payment_method_display', 'status', 'status_display',
            'reference', 'notes', 'receipt_image', 'location', 'tags', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'category_name', 
                           'transaction_type_display', 'payment_method_display', 
                           'status_display', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate transaction data"""
        if data.get('amount') and data['amount'] <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        
        if not data.get('description'):
            raise serializers.ValidationError("Description is required.")
        
        # Validate category type matches transaction type
        if data.get('category') and data.get('transaction_type'):
            category = data['category']
            transaction_type = data['transaction_type']
            
            if category.category_type not in ['both', transaction_type]:
                raise serializers.ValidationError(
                    f"Category '{category.name}' is not valid for {transaction_type} transactions."
                )
        
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class BusinessHealthSerializer(serializers.ModelSerializer):
    """Business health metrics serializer"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    health_status = serializers.SerializerMethodField()
    recommendations_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = BusinessHealth
        fields = [
            'id', 'user', 'user_name', 'financial_health', 'inventory_efficiency',
            'customer_satisfaction', 'overall_score', 'recommendations', 'health_status',
            'recommendations_summary', 'calculated_at'
        ]
        read_only_fields = ['id', 'user', 'user_name', 'overall_score', 'health_status',
                           'recommendations_summary', 'calculated_at']
    
    def get_health_status(self, obj):
        return obj.get_health_status()
    
    def get_recommendations_summary(self, obj):
        return obj.get_recommendations_summary()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    user = UserSerializer(read_only=True)
    total_balance = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'currency', 'monthly_income', 'emergency_fund_target',
            'notification_preferences', 'financial_goals', 'total_balance',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'total_balance', 'created_at', 'updated_at']


class RecurringTransactionSerializer(serializers.ModelSerializer):
    """Recurring transaction serializer"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = RecurringTransaction
        fields = '__all__'
        read_only_fields = ['user']
    
    def validate(self, data):
        """Validate recurring transaction data"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("End date must be after start date.")
        
        return data
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# Summary and Analytics Serializers
class FinancialSummarySerializer(serializers.Serializer):
    """Financial summary serializer"""
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    category_breakdown = serializers.ListField()
    recent_transactions = serializers.ListField()
    budget_status = serializers.ListField()
    goal_progress = serializers.ListField()


class CategoryBreakdownSerializer(serializers.Serializer):
    """Category breakdown serializer"""
    category_name = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = serializers.IntegerField()
    percentage = serializers.FloatField()


class BudgetStatusSerializer(serializers.Serializer):
    """Budget status serializer"""
    budget_id = serializers.IntegerField()
    category_name = serializers.CharField()
    budget_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    spent_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    spent_percentage = serializers.FloatField()
    status = serializers.CharField()  # 'on_track', 'warning', 'over_budget'


class GoalProgressSerializer(serializers.Serializer):
    """Goal progress serializer"""
    goal_id = serializers.IntegerField()
    goal_name = serializers.CharField()
    target_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    progress_percentage = serializers.FloatField()
    days_remaining = serializers.IntegerField()
    status = serializers.CharField()  # 'on_track', 'behind', 'completed' 