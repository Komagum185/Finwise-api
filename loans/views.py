from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import LoanApplication, Loan, LoanSchedule, LoanPayment, LoanDocument
from .serializers import (
    LoanApplicationSerializer, LoanApplicationCreateSerializer, LoanApplicationReviewSerializer,
    LoanSerializer, LoanCreateSerializer, LoanSummarySerializer, LoanAnalyticsSerializer,
    LoanScheduleSerializer, LoanPaymentSerializer, LoanPaymentCreateSerializer,
    LoanDocumentSerializer, LoanDocumentCreateSerializer
)
from mses.models import MSE


class LoanApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for loan applications"""
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'risk_level']
    search_fields = ['purpose', 'business_plan', 'collateral_description']
    ordering_fields = ['requested_amount', 'created_at', 'submitted_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LoanApplication.objects.all()
        return LoanApplication.objects.filter(applicant=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return LoanApplicationCreateSerializer
        elif self.action in ['update', 'partial_update'] and self.request.user.is_staff:
            return LoanApplicationReviewSerializer
        return LoanApplicationSerializer

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a loan application"""
        application = self.get_object()
        
        if application.status != 'draft':
            return Response(
                {'error': 'Only draft applications can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = 'submitted'
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a loan application (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application = self.get_object()
        application.status = 'approved'
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a loan application (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can reject applications'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        application = self.get_object()
        application.status = 'rejected'
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.save()
        
        serializer = self.get_serializer(application)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_review(self, request):
        """Get applications pending review (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can view pending reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(status='submitted')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class LoanViewSet(viewsets.ModelViewSet):
    """ViewSet for loans"""
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'loan_type', 'payment_frequency']
    search_fields = ['mse__name']
    ordering_fields = ['principal_amount', 'created_at', 'maturity_date']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Loan.objects.all()
        user_mses = MSE.objects.filter(user=user)
        return Loan.objects.filter(mse__in=user_mses)

    def get_serializer_class(self):
        if self.action == 'create':
            return LoanCreateSerializer
        elif self.action == 'summary':
            return LoanSummarySerializer
        return LoanSerializer

    @action(detail=True, methods=['post'])
    def disburse(self, request, pk=None):
        """Disburse a loan (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can disburse loans'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        loan = self.get_object()
        
        if loan.status != 'active':
            return Response(
                {'error': 'Only active loans can be disbursed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if loan.disbursed_at:
            return Response(
                {'error': 'Loan has already been disbursed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan.disbursed_at = timezone.now()
        loan.save()
        
        # Create payment schedule
        self._create_payment_schedule(loan)
        
        serializer = self.get_serializer(loan)
        return Response(serializer.data)

    def _create_payment_schedule(self, loan):
        """Create payment schedule for a loan"""
        monthly_payment = loan.calculate_monthly_payment()
        remaining_principal = loan.principal_amount
        current_date = loan.disbursed_at.date()
        
        for i in range(1, loan.term_months + 1):
            # Calculate interest for this period
            monthly_interest = (remaining_principal * loan.interest_rate / 100) / 12
            principal_due = monthly_payment - monthly_interest
            
            # Adjust for last payment
            if i == loan.term_months:
                principal_due = remaining_principal
            
            # Calculate next payment date
            if loan.payment_frequency == 'monthly':
                next_date = current_date + timedelta(days=30 * i)
            elif loan.payment_frequency == 'biweekly':
                next_date = current_date + timedelta(days=14 * i)
            else:  # weekly
                next_date = current_date + timedelta(days=7 * i)
            
            # Create schedule entry
            LoanSchedule.objects.create(
                loan=loan,
                payment_number=i,
                due_date=next_date,
                principal_due=principal_due,
                interest_due=monthly_interest,
                total_due=principal_due + monthly_interest,
                balance_after_payment=remaining_principal - principal_due
            )
            
            remaining_principal -= principal_due

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Get payment schedule for a loan"""
        loan = self.get_object()
        schedules = loan.schedule.all()
        serializer = LoanScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get payments for a loan"""
        loan = self.get_object()
        payments = loan.payments.all()
        serializer = LoanPaymentSerializer(payments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get loan summary for user"""
        queryset = self.get_queryset()
        serializer = LoanSummarySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get loan analytics"""
        user = self.request.user
        queryset = self.get_queryset()
        
        # Basic analytics
        total_loans = queryset.count()
        active_loans = queryset.filter(status='active').count()
        total_disbursed = queryset.aggregate(total=Sum('principal_amount'))['total'] or Decimal('0.00')
        total_outstanding = queryset.aggregate(total=Sum('outstanding_balance'))['total'] or Decimal('0.00')
        total_repaid = queryset.aggregate(total=Sum('total_paid'))['total'] or Decimal('0.00')
        
        # Overdue analytics
        overdue_loans = queryset.filter(schedule__status='overdue').distinct().count()
        overdue_amount = queryset.filter(schedule__status='overdue').aggregate(
            total=Sum('schedule__get_remaining_amount')
        )['total'] or Decimal('0.00')
        
        # Additional metrics
        average_loan_amount = queryset.aggregate(avg=Avg('principal_amount'))['avg'] or Decimal('0.00')
        repayment_rate = (total_repaid / total_disbursed * 100) if total_disbursed > 0 else Decimal('0.00')
        
        # Monthly trends (last 12 months)
        monthly_disbursements = []
        monthly_repayments = []
        
        for i in range(12):
            month_start = timezone.now().date().replace(day=1) - timedelta(days=30 * i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            month_disbursed = queryset.filter(
                disbursed_at__date__range=[month_start, month_end]
            ).aggregate(total=Sum('principal_amount'))['total'] or Decimal('0.00')
            
            month_repaid = queryset.filter(
                payments__payment_date__date__range=[month_start, month_end]
            ).aggregate(total=Sum('payments__amount'))['total'] or Decimal('0.00')
            
            monthly_disbursements.append({
                'month': month_start.strftime('%Y-%m'),
                'amount': month_disbursed
            })
            monthly_repayments.append({
                'month': month_start.strftime('%Y-%m'),
                'amount': month_repaid
            })
        
        analytics_data = {
            'total_loans': total_loans,
            'active_loans': active_loans,
            'total_disbursed': total_disbursed,
            'total_outstanding': total_outstanding,
            'total_repaid': total_repaid,
            'overdue_loans': overdue_loans,
            'overdue_amount': overdue_amount,
            'average_loan_amount': average_loan_amount,
            'repayment_rate': repayment_rate,
            'monthly_disbursements': monthly_disbursements,
            'monthly_repayments': monthly_repayments
        }
        
        serializer = LoanAnalyticsSerializer(analytics_data)
        return Response(serializer.data)


class LoanScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for loan payment schedules"""
    serializer_class = LoanScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'loan__status']
    ordering_fields = ['due_date', 'payment_number']
    ordering = ['payment_number']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LoanSchedule.objects.all()
        user_mses = MSE.objects.filter(user=user)
        return LoanSchedule.objects.filter(loan__mse__in=user_mses)

    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get payments for a schedule"""
        schedule = self.get_object()
        payments = schedule.payments.all()
        serializer = LoanPaymentSerializer(payments, many=True)
        return Response(serializer.data)


class LoanPaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for loan payments"""
    serializer_class = LoanPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['payment_method', 'loan__status']
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LoanPayment.objects.all()
        user_mses = MSE.objects.filter(user=user)
        return LoanPayment.objects.filter(loan__mse__in=user_mses)

    def get_serializer_class(self):
        if self.action == 'create':
            return LoanPaymentCreateSerializer
        return LoanPaymentSerializer

    def perform_create(self, serializer):
        """Create payment and update loan/schedule"""
        payment = serializer.save()
        
        # Update schedule status
        schedule = payment.schedule
        if schedule.amount_paid >= schedule.total_due:
            schedule.status = 'paid'
        elif schedule.amount_paid > 0:
            schedule.status = 'partial'
        schedule.save()
        
        # Update loan totals
        loan = payment.loan
        loan.total_paid += payment.amount
        loan.outstanding_balance = loan.get_remaining_balance()
        loan.save()


class LoanDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for loan documents"""
    serializer_class = LoanDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['document_type', 'loan_application__status', 'loan__status']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LoanDocument.objects.all()
        return LoanDocument.objects.filter(uploaded_by=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return LoanDocumentCreateSerializer
        return LoanDocumentSerializer
