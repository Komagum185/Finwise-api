from rest_framework import serializers
from .models import MSE, InputMSE, OutputMSE, ProductionMSE, MSECategory, Wallet, UserRole


class MSESerializer(serializers.ModelSerializer):
    """Serializer for MSE model"""
    class Meta:
        model = MSE
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class InputMSESerializer(serializers.ModelSerializer):
    """Serializer for InputMSE model"""
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    total_input_value = serializers.SerializerMethodField()
    
    class Meta:
        model = InputMSE
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_input_value(self, obj):
        return obj.get_total_input_value()


class OutputMSESerializer(serializers.ModelSerializer):
    """Serializer for OutputMSE model"""
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    total_sales_value = serializers.SerializerMethodField()
    
    class Meta:
        model = OutputMSE
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_sales_value(self, obj):
        return obj.get_total_sales_value()


class ProductionMSESerializer(serializers.ModelSerializer):
    """Serializer for ProductionMSE model"""
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    production_efficiency = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductionMSE
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_production_efficiency(self, obj):
        return obj.get_production_efficiency()


class MSECategorySerializer(serializers.ModelSerializer):
    """Serializer for MSECategory model"""
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    category_details = serializers.SerializerMethodField()
    
    class Meta:
        model = MSECategory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_category_details(self, obj):
        details = obj.get_category_details()
        if details:
            if isinstance(details, InputMSE):
                return InputMSESerializer(details).data
            elif isinstance(details, OutputMSE):
                return OutputMSESerializer(details).data
            elif isinstance(details, ProductionMSE):
                return ProductionMSESerializer(details).data
        return None


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet model"""
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    
    class Meta:
        model = Wallet
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    
    class Meta:
        model = UserRole
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# Comprehensive MSE serializer with all related data
class ComprehensiveMSESerializer(serializers.ModelSerializer):
    """Comprehensive serializer for MSE with all related data"""
    input_mse = InputMSESerializer(read_only=True)
    output_mse = OutputMSESerializer(read_only=True)
    production_mse = ProductionMSESerializer(read_only=True)
    category = MSECategorySerializer(read_only=True)
    wallets = WalletSerializer(many=True, read_only=True)
    user_roles = UserRoleSerializer(many=True, read_only=True)
    
    class Meta:
        model = MSE
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


# Category-specific serializers for API endpoints
class InputMSEListSerializer(serializers.ModelSerializer):
    """Serializer for listing Input MSEs"""
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    mse_status = serializers.CharField(source='mse.status', read_only=True)
    total_input_value = serializers.SerializerMethodField()
    
    class Meta:
        model = InputMSE
        fields = [
            'id', 'mse', 'mse_name', 'mse_status', 'input_categories', 
            'supplier_network_size', 'average_order_value', 'lead_time_days',
            'total_input_value', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_total_input_value(self, obj):
        return obj.get_total_input_value()


class OutputMSEListSerializer(serializers.ModelSerializer):
    """Serializer for listing Output MSEs"""
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    mse_status = serializers.CharField(source='mse.status', read_only=True)
    total_sales_value = serializers.SerializerMethodField()
    
    class Meta:
        model = OutputMSE
        fields = [
            'id', 'mse', 'mse_name', 'mse_status', 'output_categories',
            'customer_network_size', 'average_sale_value', 'sales_channels',
            'total_sales_value', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_total_sales_value(self, obj):
        return obj.get_total_sales_value()


class ProductionMSEListSerializer(serializers.ModelSerializer):
    """Serializer for listing Production MSEs"""
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    mse_status = serializers.CharField(source='mse.status', read_only=True)
    production_efficiency = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductionMSE
        fields = [
            'id', 'mse', 'mse_name', 'mse_status', 'production_capacity',
            'daily_production_target', 'equipment_list', 'production_efficiency',
            'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_production_efficiency(self, obj):
        return obj.get_production_efficiency() 