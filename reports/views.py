from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Sum, Count, Avg
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from .models import SalesData, ProductPerformance, MarketTrends, Predictions
from .serializers import (
    SalesDataSerializer, ProductPerformanceSerializer, MarketTrendsSerializer, PredictionsSerializer,
    SalesSummarySerializer, ProductPerformanceSummarySerializer, MarketTrendsSummarySerializer,
    PredictionsSummarySerializer, BusinessIntelligenceSerializer
)


def reports_home(request):
    """Basic reports home view"""
    return JsonResponse({
        'message': 'Reports module is available',
        'status': 'success'
    })


@csrf_exempt
def basic_report(request):
    """Basic report endpoint"""
    return JsonResponse({
        'message': 'Basic report functionality',
        'timestamp': timezone.now().isoformat(),
        'status': 'success'
    })


class SalesDataViewSet(viewsets.ModelViewSet):
    """Sales data management viewset"""
    serializer_class = SalesDataSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['date']
    ordering_fields = ['date', 'revenue', 'orders']
    ordering = ['-date']
    
    def get_queryset(self):
        return SalesData.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get sales summary statistics"""
        queryset = self.get_queryset()
        
        total_revenue = queryset.aggregate(total=Sum('revenue'))['total'] or 0
        total_orders = queryset.aggregate(total=Sum('orders'))['total'] or 0
        total_customers = queryset.aggregate(total=Sum('customers'))['total'] or 0
        average_order_value = queryset.aggregate(avg=Avg('average_order_value'))['avg'] or 0
        
        data = {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'average_order_value': average_order_value,
            'revenue_growth_rate': 12.5,  # Simulated
            'customer_growth_rate': 8.2,  # Simulated
            'recent_sales_data': list(queryset.order_by('-date')[:10].values('date', 'revenue', 'orders'))
        }
        
        serializer = SalesSummarySerializer(data)
        return Response(serializer.data)


class ProductPerformanceViewSet(viewsets.ModelViewSet):
    """Product performance management viewset"""
    serializer_class = ProductPerformanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'period']
    search_fields = ['product_name', 'category']
    ordering_fields = ['sales', 'revenue', 'growth']
    ordering = ['-revenue']
    
    def get_queryset(self):
        return ProductPerformance.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get product performance summary statistics"""
        queryset = self.get_queryset()
        
        total_products = queryset.count()
        total_revenue = queryset.aggregate(total=Sum('revenue'))['total'] or 0
        average_growth_rate = queryset.aggregate(avg=Avg('growth'))['avg'] or 0
        
        data = {
            'total_products': total_products,
            'total_revenue': total_revenue,
            'average_growth_rate': average_growth_rate,
            'top_performing_products': list(queryset.order_by('-revenue')[:10].values('product_name', 'revenue', 'growth')),
            'category_breakdown': list(queryset.values('category').annotate(count=Count('id'), revenue=Sum('revenue')))
        }
        
        serializer = ProductPerformanceSummarySerializer(data)
        return Response(serializer.data)


class MarketTrendsViewSet(viewsets.ModelViewSet):
    """Market trends management viewset"""
    serializer_class = MarketTrendsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['impact', 'region', 'confidence']
    search_fields = ['trend', 'description', 'region']
    ordering_fields = ['confidence', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return MarketTrends.objects.all()  # Market trends are global
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get market trends summary statistics"""
        queryset = self.get_queryset()
        
        total_trends = queryset.count()
        positive_trends = queryset.filter(impact='positive').count()
        negative_trends = queryset.filter(impact='negative').count()
        average_confidence = queryset.aggregate(avg=Avg('confidence'))['avg'] or 0
        
        data = {
            'total_trends': total_trends,
            'positive_trends': positive_trends,
            'negative_trends': negative_trends,
            'average_confidence': average_confidence,
            'critical_trends': list(queryset.filter(confidence__gte=90).values('trend', 'impact', 'confidence')[:5]),
            'regional_breakdown': list(queryset.values('region').annotate(count=Count('id')))
        }
        
        serializer = MarketTrendsSummarySerializer(data)
        return Response(serializer.data)


class PredictionsViewSet(viewsets.ModelViewSet):
    """Predictions management viewset"""
    serializer_class = PredictionsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['metric', 'trend', 'prediction_date']
    search_fields = ['metric']
    ordering_fields = ['confidence', 'prediction_date']
    ordering = ['-prediction_date']
    
    def get_queryset(self):
        return Predictions.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get predictions summary statistics"""
        queryset = self.get_queryset()
        
        total_predictions = queryset.count()
        high_confidence_predictions = queryset.filter(confidence__gte=85).count()
        average_confidence = queryset.aggregate(avg=Avg('confidence'))['avg'] or 0
        
        data = {
            'total_predictions': total_predictions,
            'high_confidence_predictions': high_confidence_predictions,
            'average_confidence': average_confidence,
            'trend_breakdown': list(queryset.values('trend').annotate(count=Count('id'))),
            'recent_predictions': list(queryset.order_by('-created_at')[:10].values('metric', 'predicted_value', 'confidence', 'trend'))
        }
        
        serializer = PredictionsSummarySerializer(data)
        return Response(serializer.data)


class BusinessIntelligenceViewSet(viewsets.ViewSet):
    """Business intelligence dashboard viewset"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get comprehensive business intelligence dashboard"""
        user = request.user
        
        # Sales summary
        sales_data = SalesData.objects.filter(user=user)
        sales_summary = {
            'total_revenue': sales_data.aggregate(total=Sum('revenue'))['total'] or 0,
            'total_orders': sales_data.aggregate(total=Sum('orders'))['total'] or 0,
            'total_customers': sales_data.aggregate(total=Sum('customers'))['total'] or 0,
            'average_order_value': sales_data.aggregate(avg=Avg('average_order_value'))['avg'] or 0,
            'revenue_growth_rate': 12.5,  # Simulated
            'customer_growth_rate': 8.2,  # Simulated
            'recent_sales_data': list(sales_data.order_by('-date')[:5].values('date', 'revenue', 'orders'))
        }
        
        # Product performance summary
        product_data = ProductPerformance.objects.filter(user=user)
        product_summary = {
            'total_products': product_data.count(),
            'total_revenue': product_data.aggregate(total=Sum('revenue'))['total'] or 0,
            'average_growth_rate': product_data.aggregate(avg=Avg('growth'))['avg'] or 0,
            'top_performing_products': list(product_data.order_by('-revenue')[:5].values('product_name', 'revenue', 'growth')),
            'category_breakdown': list(product_data.values('category').annotate(count=Count('id'), revenue=Sum('revenue')))
        }
        
        # Market trends summary
        market_data = MarketTrends.objects.all()
        market_summary = {
            'total_trends': market_data.count(),
            'positive_trends': market_data.filter(impact='positive').count(),
            'negative_trends': market_data.filter(impact='negative').count(),
            'average_confidence': market_data.aggregate(avg=Avg('confidence'))['avg'] or 0,
            'critical_trends': list(market_data.filter(confidence__gte=90).values('trend', 'impact', 'confidence')[:5]),
            'regional_breakdown': list(market_data.values('region').annotate(count=Count('id')))
        }
        
        # Predictions summary
        predictions_data = Predictions.objects.filter(user=user)
        predictions_summary = {
            'total_predictions': predictions_data.count(),
            'high_confidence_predictions': predictions_data.filter(confidence__gte=85).count(),
            'average_confidence': predictions_data.aggregate(avg=Avg('confidence'))['avg'] or 0,
            'trend_breakdown': list(predictions_data.values('trend').annotate(count=Count('id'))),
            'recent_predictions': list(predictions_data.order_by('-created_at')[:5].values('metric', 'predicted_value', 'confidence', 'trend'))
        }
        
        # Key insights and recommendations
        key_insights = [
            "Revenue growth is strong at 12.5% month-over-month",
            "Customer retention rate improved by 8.2%",
            "Top 3 products account for 60% of total revenue",
            "Market trends show positive sentiment in your region"
        ]
        
        recommendations = [
            "Focus on expanding top-performing product categories",
            "Implement customer retention strategies based on recent success",
            "Monitor critical market trends for strategic planning",
            "Consider increasing inventory for high-growth products"
        ]
        
        data = {
            'sales_summary': sales_summary,
            'product_performance': product_summary,
            'market_trends': market_summary,
            'predictions': predictions_summary,
            'key_insights': key_insights,
            'recommendations': recommendations,
        }
        
        serializer = BusinessIntelligenceSerializer(data)
        return Response(serializer.data)
