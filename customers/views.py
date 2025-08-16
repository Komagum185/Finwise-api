from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Customer, CustomerFeedback, SMSCampaign
from .serializers import (
    CustomerSerializer, CustomerFeedbackSerializer, SMSCampaignSerializer,
    CustomerSummarySerializer, CustomerAnalyticsSerializer, SMSCampaignSummarySerializer
)


class CustomerViewSet(viewsets.ModelViewSet):
    """Customer management viewset"""
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['customer_type', 'status', 'rating']
    search_fields = ['name', 'phone', 'email', 'location']
    ordering_fields = ['name', 'total_spent', 'rating', 'created_at', 'last_purchase']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Customer.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_purchase(self, request, pk=None):
        """Update customer purchase statistics"""
        customer = self.get_object()
        amount = request.data.get('amount', 0)
        
        if amount <= 0:
            return Response(
                {'error': 'Amount must be greater than zero'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        customer.update_purchase_stats(amount)
        return Response({'message': 'Purchase statistics updated successfully'})
    
    @action(detail=True, methods=['post'])
    def add_loyalty_points(self, request, pk=None):
        """Add loyalty points to customer"""
        customer = self.get_object()
        points = request.data.get('points', 0)
        
        if points <= 0:
            return Response(
                {'error': 'Points must be greater than zero'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        customer.add_loyalty_points(points)
        return Response({'message': 'Loyalty points added successfully'})
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get customer summary statistics"""
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_customers = queryset.count()
        active_customers = queryset.filter(status='active').count()
        vip_customers = queryset.filter(customer_type='vip').count()
        average_rating = queryset.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        total_revenue = queryset.aggregate(total=Sum('total_spent'))['total'] or 0
        
        # Calculate growth rate (customers added in last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        new_customers = queryset.filter(created_at__gte=thirty_days_ago).count()
        customer_growth_rate = (new_customers / total_customers * 100) if total_customers > 0 else 0
        
        # Top customers by total spent
        top_customers = queryset.order_by('-total_spent')[:5].values(
            'id', 'name', 'total_spent', 'total_purchases', 'rating'
        )
        
        # Recent feedback
        recent_feedback = CustomerFeedback.objects.filter(
            customer__user=request.user
        ).order_by('-created_at')[:5].values(
            'customer__name', 'rating', 'comment', 'created_at'
        )
        
        data = {
            'total_customers': total_customers,
            'active_customers': active_customers,
            'vip_customers': vip_customers,
            'average_rating': average_rating,
            'total_revenue': total_revenue,
            'customer_growth_rate': customer_growth_rate,
            'top_customers': list(top_customers),
            'recent_feedback': list(recent_feedback),
        }
        
        serializer = CustomerSummarySerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get customer analytics data"""
        queryset = self.get_queryset()
        
        # Customer types breakdown
        customer_types_breakdown = queryset.values('customer_type').annotate(
            count=Count('id')
        ).order_by('customer_type')
        
        # Revenue by customer type
        revenue_by_customer_type = queryset.values('customer_type').annotate(
            total_revenue=Sum('total_spent')
        ).order_by('customer_type')
        
        # Customer retention rate (customers with purchases in last 90 days)
        ninety_days_ago = timezone.now() - timedelta(days=90)
        active_customers = queryset.filter(last_purchase__gte=ninety_days_ago).count()
        retention_rate = (active_customers / queryset.count() * 100) if queryset.count() > 0 else 0
        
        # Average customer lifetime value
        avg_lifetime_value = queryset.aggregate(avg=Avg('total_spent'))['avg'] or 0
        
        # Customer satisfaction trends (last 6 months)
        six_months_ago = timezone.now() - timedelta(days=180)
        satisfaction_trends = CustomerFeedback.objects.filter(
            customer__user=request.user,
            created_at__gte=six_months_ago
        ).values('created_at__month').annotate(
            avg_rating=Avg('rating')
        ).order_by('created_at__month')
        
        # Loyalty points distribution
        loyalty_distribution = queryset.values('loyalty_points').annotate(
            count=Count('id')
        ).order_by('loyalty_points')
        
        data = {
            'customer_types_breakdown': list(customer_types_breakdown),
            'revenue_by_customer_type': list(revenue_by_customer_type),
            'customer_retention_rate': retention_rate,
            'average_customer_lifetime_value': avg_lifetime_value,
            'customer_satisfaction_trends': list(satisfaction_trends),
            'loyalty_points_distribution': list(loyalty_distribution),
        }
        
        serializer = CustomerAnalyticsSerializer(data)
        return Response(serializer.data)


class CustomerFeedbackViewSet(viewsets.ModelViewSet):
    """Customer feedback management viewset"""
    serializer_class = CustomerFeedbackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rating', 'date']
    search_fields = ['comment', 'product', 'customer__name']
    ordering_fields = ['rating', 'date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return CustomerFeedback.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_customer(self, request):
        """Get feedback grouped by customer"""
        customer_id = request.query_params.get('customer_id')
        if customer_id:
            queryset = self.get_queryset().filter(customer_id=customer_id)
        else:
            queryset = self.get_queryset()
        
        # Group by customer and calculate average rating
        feedback_by_customer = queryset.values('customer__name').annotate(
            avg_rating=Avg('rating'),
            feedback_count=Count('id')
        ).order_by('-avg_rating')
        
        return Response(feedback_by_customer)


class SMSCampaignViewSet(viewsets.ModelViewSet):
    """SMS campaign management viewset"""
    serializer_class = SMSCampaignSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'scheduled_date']
    search_fields = ['name', 'message']
    ordering_fields = ['status', 'scheduled_date', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return SMSCampaign.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send_campaign(self, request, pk=None):
        """Send SMS campaign"""
        campaign = self.get_object()
        
        if campaign.status != 'draft':
            return Response(
                {'error': 'Only draft campaigns can be sent'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Here you would integrate with actual SMS service
        # For now, we'll simulate sending
        success_count = len(campaign.recipients)  # Simulate 100% success
        failure_count = 0
        
        campaign.mark_as_sent(success_count, failure_count)
        return Response({'message': 'Campaign sent successfully'})
    
    @action(detail=True, methods=['post'])
    def schedule_campaign(self, request, pk=None):
        """Schedule SMS campaign"""
        campaign = self.get_object()
        scheduled_date = request.data.get('scheduled_date')
        
        if not scheduled_date:
            return Response(
                {'error': 'Scheduled date is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        campaign.scheduled_date = scheduled_date
        campaign.status = 'scheduled'
        campaign.save()
        
        return Response({'message': 'Campaign scheduled successfully'})
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get SMS campaign summary statistics"""
        queryset = self.get_queryset()
        
        total_campaigns = queryset.count()
        sent_campaigns = queryset.filter(status='sent').count()
        draft_campaigns = queryset.filter(status='draft').count()
        
        # Calculate average success rate
        sent_campaigns_data = queryset.filter(status='sent')
        total_success = sum(campaign.success_count for campaign in sent_campaigns_data)
        total_failures = sum(campaign.failure_count for campaign in sent_campaigns_data)
        average_success_rate = (total_success / (total_success + total_failures) * 100) if (total_success + total_failures) > 0 else 0
        
        # Total recipients and successful deliveries
        total_recipients = sum(campaign.get_total_recipients() for campaign in queryset)
        total_successful_deliveries = sum(campaign.success_count for campaign in sent_campaigns_data)
        
        # Recent campaigns
        recent_campaigns = queryset.order_by('-created_at')[:5].values(
            'id', 'name', 'status', 'success_count', 'failure_count', 'created_at'
        )
        
        data = {
            'total_campaigns': total_campaigns,
            'sent_campaigns': sent_campaigns,
            'draft_campaigns': draft_campaigns,
            'average_success_rate': average_success_rate,
            'total_recipients': total_recipients,
            'total_successful_deliveries': total_successful_deliveries,
            'recent_campaigns': list(recent_campaigns),
        }
        
        serializer = SMSCampaignSummarySerializer(data)
        return Response(serializer.data)
