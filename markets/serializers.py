from rest_framework import serializers
from .models import Customer, Supplier, Product, Transaction, Notification


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'mse', 'name', 'phone_number', 'created_at']
        read_only_fields = ['created_at']


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'mse', 'name', 'phone_number', 'created_at']
        read_only_fields = ['created_at']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'mse', 'name', 'price', 'unit', 'created_at']
        read_only_fields = ['created_at']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'mse', 'type', 'product', 'counterparty_name', 'amount', 'quantity', 'created_at']
        read_only_fields = ['created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'mse', 'message', 'is_read', 'created_at']
        read_only_fields = ['created_at']


