from rest_framework import serializers
from .models import Market, Producer, Customer, Product, BusinessTransaction


class MarketSerializer(serializers.ModelSerializer):
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    
    class Meta:
        model = Market
        fields = '__all__'
        read_only_fields = ['mse']


class ProducerSerializer(serializers.ModelSerializer):
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    
    class Meta:
        model = Producer
        fields = '__all__'
        read_only_fields = ['mse']


class CustomerSerializer(serializers.ModelSerializer):
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['mse']


class ProductSerializer(serializers.ModelSerializer):
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['mse']


class BusinessTransactionSerializer(serializers.ModelSerializer):
    mse_name = serializers.CharField(source='mse.name', read_only=True)
    wallet_name = serializers.CharField(source='wallet.name', read_only=True)
    producer_name = serializers.CharField(source='producer.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = BusinessTransaction
        fields = '__all__'
        read_only_fields = ['mse'] 