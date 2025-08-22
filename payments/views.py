from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import PaymentProvider, QRPayment, ScheduledTransfer, PaymentTransaction
from .serializers import (
    PaymentProviderSerializer, PaymentProviderCreateSerializer,
    QRPaymentSerializer, QRPaymentCreateSerializer,
    ScheduledTransferSerializer, ScheduledTransferCreateSerializer,
    PaymentTransactionSerializer, PaymentTransactionCreateSerializer,
    PaymentStatisticsSerializer, QRPaymentStatusSerializer,
    ScheduledTransferStatusSerializer
)


class PaymentProviderViewSet(viewsets.ModelViewSet):
    """ViewSet for PaymentProvider"""
    queryset = PaymentProvider.objects.all()
    serializer_class = PaymentProviderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentProviderCreateSerializer
        return PaymentProviderSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active payment providers"""
        providers = self.queryset.filter(status='active')
        serializer = self.get_serializer(providers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get providers filtered by type"""
        provider_type = request.query_params.get('type')
        country = request.query_params.get('country')
        
        queryset = self.queryset.filter(status='active')
        
        if provider_type:
            queryset = queryset.filter(type=provider_type)
        
        if country:
            queryset = queryset.filter(country=country)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def calculate_fees(self, request, pk=None):
        """Calculate fees for a given amount"""
        provider = self.get_object()
        amount = request.data.get('amount')
        
        if not amount:
            return Response(
                {'error': 'Amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = float(amount)
            fees = provider.calculate_fees(amount)
            is_valid = provider.is_amount_valid(amount)
            
            return Response({
                'provider': provider.name,
                'amount': amount,
                'fees': fees,
                'net_amount': amount - fees,
                'is_amount_valid': is_valid,
                'limits': {
                    'min': provider.min_amount,
                    'max': provider.max_amount
                }
            })
        except ValueError:
            return Response(
                {'error': 'Invalid amount'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class QRPaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for QRPayment"""
    serializer_class = QRPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return QRPayment.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QRPaymentCreateSerializer
        return QRPaymentSerializer
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get QR payment status"""
        qr_payment = self.get_object()
        serializer = self.get_serializer(qr_payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark QR payment as completed"""
        qr_payment = self.get_object()
        
        if qr_payment.status != 'pending':
            return Response(
                {'error': 'QR payment is not pending'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if qr_payment.is_expired():
            qr_payment.status = 'expired'
            qr_payment.save()
            return Response(
                {'error': 'QR payment has expired'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transaction_id = request.data.get('transaction_id')
        payer_phone = request.data.get('payer_phone')
        payer_name = request.data.get('payer_name')
        
        qr_payment.mark_completed(transaction_id, payer_phone, payer_name)
        
        # Create payment transaction
        PaymentTransaction.objects.create(
            user=request.user,
            type='qr_payment',
            amount=qr_payment.amount,
            currency=qr_payment.currency,
            provider=qr_payment.provider,
            description=qr_payment.description,
            qr_payment=qr_payment,
            status='completed',
            processed_at=timezone.now()
        )
        
        serializer = self.get_serializer(qr_payment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get expired QR payments"""
        expired_payments = self.get_queryset().filter(
            status='pending',
            expires_at__lt=timezone.now()
        )
        serializer = self.get_serializer(expired_payments, many=True)
        return Response(serializer.data)


class ScheduledTransferViewSet(viewsets.ModelViewSet):
    """ViewSet for ScheduledTransfer"""
    serializer_class = ScheduledTransferSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ScheduledTransfer.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduledTransferCreateSerializer
        return ScheduledTransferSerializer
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause scheduled transfer"""
        transfer = self.get_object()
        transfer.status = 'paused'
        transfer.save()
        serializer = self.get_serializer(transfer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume scheduled transfer"""
        transfer = self.get_object()
        transfer.status = 'active'
        transfer.save()
        serializer = self.get_serializer(transfer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel scheduled transfer"""
        transfer = self.get_object()
        transfer.status = 'cancelled'
        transfer.save()
        serializer = self.get_serializer(transfer)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due(self, request):
        """Get due scheduled transfers"""
        due_transfers = self.get_queryset().filter(
            status='active',
            next_execution__lte=timezone.now()
        )
        serializer = self.get_serializer(due_transfers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active scheduled transfers"""
        active_transfers = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(active_transfers, many=True)
        return Response(serializer.data)


class PaymentTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for PaymentTransaction"""
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PaymentTransaction.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentTransactionCreateSerializer
        return PaymentTransactionSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get payment statistics"""
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = self.get_queryset().filter(created_at__gte=start_date)
        
        total_transactions = queryset.count()
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        total_fees = queryset.aggregate(total=Sum('fees'))['total'] or 0
        completed_transactions = queryset.filter(status='completed').count()
        success_rate = (completed_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        stats = {
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'total_fees': total_fees,
            'success_rate': round(success_rate, 2),
            'currency': 'UGX',
            'period': f'Last {days} days'
        }
        
        serializer = PaymentStatisticsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get transactions by status"""
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = self.get_queryset().filter(status=status_filter)
        else:
            queryset = self.get_queryset()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get transactions by type"""
        type_filter = request.query_params.get('type')
        if type_filter:
            queryset = self.get_queryset().filter(type=type_filter)
        else:
            queryset = self.get_queryset()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry failed transaction"""
        transaction = self.get_object()
        
        if transaction.status != 'failed':
            return Response(
                {'error': 'Only failed transactions can be retried'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset transaction for retry
        transaction.status = 'pending'
        transaction.processed_at = None
        transaction.save()
        
        serializer = self.get_serializer(transaction)
        return Response(serializer.data)
