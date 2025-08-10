from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Market, Producer, Customer, Product, BusinessTransaction
from .serializers import MarketSerializer, ProducerSerializer, CustomerSerializer, ProductSerializer, BusinessTransactionSerializer
from mses.models import MSE


class MarketViewSet(viewsets.ModelViewSet):
    """ViewSet for market management"""
    serializer_class = MarketSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['market_type', 'is_active']
    search_fields = ['name', 'location', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_mses = MSE.objects.filter(user=self.request.user)
        return Market.objects.filter(mse__in=user_mses)
    
    @action(detail=False, methods=['get'])
    def input(self, request):
        """Get input markets"""
        queryset = self.get_queryset().filter(market_type='input')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def output(self, request):
        """Get output markets"""
        queryset = self.get_queryset().filter(market_type='output')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProducerViewSet(viewsets.ModelViewSet):
    """ViewSet for producer/supplier management"""
    serializer_class = ProducerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'contact_person', 'products_supplied']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_mses = MSE.objects.filter(user=self.request.user)
        return Producer.objects.filter(mse__in=user_mses)


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for customer management"""
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'contact_person', 'email']
    ordering_fields = ['name', 'credit_limit', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_mses = MSE.objects.filter(user=self.request.user)
        return Customer.objects.filter(mse__in=user_mses)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for product management"""
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'unit_price', 'stock_quantity', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_mses = MSE.objects.filter(user=self.request.user)
        return Product.objects.filter(mse__in=user_mses)


class BusinessTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for business transactions"""
    serializer_class = BusinessTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transaction_type', 'status', 'currency']
    search_fields = ['description', 'reference_number']
    ordering_fields = ['amount', 'transaction_date', 'created_at']
    ordering = ['-transaction_date']
    
    def get_queryset(self):
        user_mses = MSE.objects.filter(user=self.request.user)
        return BusinessTransaction.objects.filter(mse__in=user_mses)
