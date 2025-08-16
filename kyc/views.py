from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import KYCDocument, BankAccount, MobileMoneyAccount, KYCVerification, VerificationRequest
from .serializers import (
    KYCDocumentSerializer, KYCDocumentCreateSerializer,
    BankAccountSerializer, BankAccountCreateSerializer,
    MobileMoneyAccountSerializer, MobileMoneyAccountCreateSerializer,
    KYCVerificationSerializer, KYCVerificationCreateSerializer,
    VerificationRequestSerializer, VerificationRequestCreateSerializer,
    KYCStatusSerializer, KYCStatisticsSerializer
)
from users.models import CustomUser


class KYCDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for KYC documents"""
    serializer_class = KYCDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['document_type', 'status']
    search_fields = ['document_number', 'filename']
    ordering_fields = ['uploaded_at', 'verified_at']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return KYCDocument.objects.all()
        return KYCDocument.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return KYCDocumentCreateSerializer
        return KYCDocumentSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a document (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        document = self.get_object()
        document.status = 'approved'
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        # Update KYC verification progress
        self._update_kyc_progress(document.user)
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a document (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can reject documents'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        document = self.get_object()
        document.status = 'rejected'
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)

    def _update_kyc_progress(self, user):
        """Update KYC verification progress for user"""
        try:
            kyc_verification = user.kyc_verification
            kyc_verification.documents_uploaded = user.kyc_documents.count()
            kyc_verification.documents_verified = user.kyc_documents.filter(status='approved').count()
            kyc_verification.update_verification_status()
        except KYCVerification.DoesNotExist:
            pass


class BankAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for bank accounts"""
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['account_type', 'status', 'currency']
    search_fields = ['bank_name', 'account_number', 'account_holder_name']
    ordering_fields = ['created_at', 'verified_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return BankAccount.objects.all()
        return BankAccount.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return BankAccountCreateSerializer
        return BankAccountSerializer

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a bank account (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can verify bank accounts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        bank_account = self.get_object()
        bank_account.status = 'verified'
        bank_account.verified_by = request.user
        bank_account.verified_at = timezone.now()
        bank_account.save()
        
        # Update KYC verification progress
        self._update_kyc_progress(bank_account.user)
        
        serializer = self.get_serializer(bank_account)
        return Response(serializer.data)

    def _update_kyc_progress(self, user):
        """Update KYC verification progress for user"""
        try:
            kyc_verification = user.kyc_verification
            kyc_verification.bank_accounts_verified = user.bank_accounts.filter(status='verified').count()
            kyc_verification.update_verification_status()
        except KYCVerification.DoesNotExist:
            pass


class MobileMoneyAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for mobile money accounts"""
    serializer_class = MobileMoneyAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['provider', 'status']
    search_fields = ['phone_number', 'account_name']
    ordering_fields = ['created_at', 'verified_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return MobileMoneyAccount.objects.all()
        return MobileMoneyAccount.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return MobileMoneyAccountCreateSerializer
        return MobileMoneyAccountSerializer

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a mobile money account (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can verify mobile money accounts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        mobile_account = self.get_object()
        mobile_account.status = 'verified'
        mobile_account.verified_by = request.user
        mobile_account.verified_at = timezone.now()
        mobile_account.save()
        
        # Update KYC verification progress
        self._update_kyc_progress(mobile_account.user)
        
        serializer = self.get_serializer(mobile_account)
        return Response(serializer.data)

    def _update_kyc_progress(self, user):
        """Update KYC verification progress for user"""
        try:
            kyc_verification = user.kyc_verification
            kyc_verification.mobile_accounts_verified = user.mobile_money_accounts.filter(status='verified').count()
            kyc_verification.update_verification_status()
        except KYCVerification.DoesNotExist:
            pass


class KYCVerificationViewSet(viewsets.ModelViewSet):
    """ViewSet for KYC verification status"""
    serializer_class = KYCVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['verification_level', 'status']
    search_fields = ['user__username', 'user__email']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return KYCVerification.objects.all()
        return KYCVerification.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return KYCVerificationCreateSerializer
        return KYCVerificationSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve KYC verification (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve KYC verification'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        kyc_verification = self.get_object()
        kyc_verification.status = 'approved'
        kyc_verification.verified_by = request.user
        kyc_verification.verified_at = timezone.now()
        kyc_verification.save()
        
        serializer = self.get_serializer(kyc_verification)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject KYC verification (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can reject KYC verification'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        kyc_verification = self.get_object()
        kyc_verification.status = 'rejected'
        kyc_verification.verified_by = request.user
        kyc_verification.verified_at = timezone.now()
        kyc_verification.save()
        
        serializer = self.get_serializer(kyc_verification)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_status(self, request):
        """Get current user's KYC status"""
        try:
            kyc_verification = request.user.kyc_verification
            serializer = self.get_serializer(kyc_verification)
            return Response(serializer.data)
        except KYCVerification.DoesNotExist:
            return Response(
                {'error': 'KYC verification not found. Please start the verification process.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get KYC statistics (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can view KYC statistics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Basic statistics
        total_users = CustomUser.objects.count()
        verified_users = KYCVerification.objects.filter(status='approved').count()
        pending_verifications = KYCVerification.objects.filter(status='pending_review').count()
        rejected_verifications = KYCVerification.objects.filter(status='rejected').count()
        
        # Calculate verification rate
        verification_rate = (verified_users / total_users * 100) if total_users > 0 else 0
        
        # Calculate average verification time
        verified_kyc = KYCVerification.objects.filter(
            status='approved',
            verified_at__isnull=False
        )
        if verified_kyc.exists():
            avg_time = verified_kyc.aggregate(
                avg_time=Avg('verified_at' - 'created_at')
            )['avg_time']
            average_verification_time = avg_time.total_seconds() / 3600  # Convert to hours
        else:
            average_verification_time = 0
        
        # Document statistics
        documents_uploaded = KYCDocument.objects.count()
        documents_verified = KYCDocument.objects.filter(status='approved').count()
        
        # Account statistics
        bank_accounts_verified = BankAccount.objects.filter(status='verified').count()
        mobile_accounts_verified = MobileMoneyAccount.objects.filter(status='verified').count()
        
        # Pending requests
        pending_requests = VerificationRequest.objects.filter(status='pending').count()
        
        # Monthly verifications (last 12 months)
        monthly_verifications = []
        for i in range(12):
            month_start = timezone.now().date().replace(day=1) - timedelta(days=30 * i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            month_verified = KYCVerification.objects.filter(
                status='approved',
                verified_at__date__range=[month_start, month_end]
            ).count()
            
            monthly_verifications.append({
                'month': month_start.strftime('%Y-%m'),
                'verified_count': month_verified
            })
        
        statistics_data = {
            'total_users': total_users,
            'verified_users': verified_users,
            'pending_verifications': pending_verifications,
            'rejected_verifications': rejected_verifications,
            'verification_rate': verification_rate,
            'average_verification_time': average_verification_time,
            'documents_uploaded': documents_uploaded,
            'documents_verified': documents_verified,
            'bank_accounts_verified': bank_accounts_verified,
            'mobile_accounts_verified': mobile_accounts_verified,
            'pending_requests': pending_requests,
            'monthly_verifications': monthly_verifications
        }
        
        serializer = KYCStatisticsSerializer(statistics_data)
        return Response(serializer.data)


class VerificationRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for verification requests"""
    serializer_class = VerificationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['request_type', 'status', 'priority']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return VerificationRequest.objects.all()
        return VerificationRequest.objects.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return VerificationRequestCreateSerializer
        return VerificationRequestSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve verification request (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can approve verification requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        verification_request = self.get_object()
        verification_request.status = 'approved'
        verification_request.reviewed_by = request.user
        verification_request.reviewed_at = timezone.now()
        verification_request.save()
        
        serializer = self.get_serializer(verification_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject verification request (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can reject verification requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        verification_request = self.get_object()
        verification_request.status = 'rejected'
        verification_request.reviewed_by = request.user
        verification_request.reviewed_at = timezone.now()
        verification_request.save()
        
        serializer = self.get_serializer(verification_request)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending verification requests (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only staff can view pending requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        queryset = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
