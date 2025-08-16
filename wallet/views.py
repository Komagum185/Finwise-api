from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    Category, Transaction, Budget, Goal, EnhancedWallet, 
    EnhancedWalletTransaction, WalletTransfer, WalletStatistics,
    PaymentTransaction, BulkPayment, BulkPaymentRecipient
)
from .serializers import (
    CategorySerializer, TransactionSerializer, BudgetSerializer, GoalSerializer,
    EnhancedWalletSerializer, EnhancedWalletTransactionSerializer,
    WalletTransferSerializer, WalletStatisticsSerializer,
    WalletTransactionRequestSerializer, WalletFilterSerializer,
    WalletSerializer, WalletTransactionSerializer,
    PaymentTransactionSerializer, BulkPaymentSerializer, BulkPaymentRecipientSerializer,
    PaymentSummarySerializer, BulkPaymentSummarySerializer
)
from mses.models import Wallet as MSEWallet, WalletTransaction as MSEWalletTransaction


# Enhanced Wallet ViewSets matching TypeScript interfaces
class EnhancedWalletViewSet(viewsets.ModelViewSet):
    """ViewSet for managing enhanced wallets matching TypeScript interface"""
    queryset = EnhancedWallet.objects.all()
    serializer_class = EnhancedWalletSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'account_type', 'currency']
    search_fields = ['mse_name', 'mse_code', 'account_number']
    ordering_fields = ['balance', 'created_at', 'transaction_count']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter wallets by user's MSEs"""
        user = self.request.user
        # Get MSE IDs associated with the user
        mse_ids = MSEWallet.objects.filter(mse__user=user).values_list('mse_id', flat=True)
        return EnhancedWallet.objects.filter(mse_id__in=mse_ids)

    @action(detail=False, methods=['get'])
    def account_types(self, request):
        """Get available account types"""
        types = [{'value': choice[0], 'label': choice[1]} 
                for choice in EnhancedWallet.ACCOUNT_TYPES]
        return Response(types)

    @action(detail=False, methods=['get'])
    def statuses(self, request):
        """Get available wallet statuses"""
        statuses = [{'value': choice[0], 'label': choice[1]} 
                   for choice in EnhancedWallet.STATUS_CHOICES]
        return Response(statuses)

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get wallet balance and basic info"""
        wallet = self.get_object()
        return Response({
            'wallet_id': wallet.id,
            'mse_name': wallet.mse_name,
            'account_number': wallet.account_number,
            'balance': wallet.balance,
            'currency': wallet.currency,
            'status': wallet.status
        })

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update wallet status"""
        wallet = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(EnhancedWallet.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        wallet.status = new_status
        wallet.save()
        
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get comprehensive wallet analytics"""
        wallet = self.get_object()
        
        # Get transaction statistics
        transactions = EnhancedWalletTransaction.objects.filter(wallet=wallet)
        
        # Monthly trends
        monthly_data = transactions.extra(
            select={'month': "EXTRACT(month FROM date)"}
        ).values('month').annotate(
            total_income=Sum('amount', filter=Q(type='credit')),
            total_expense=Sum('amount', filter=Q(type='debit')),
            transaction_count=Count('id')
        ).order_by('month')
        
        # Category breakdown
        category_data = transactions.values('category__name').annotate(
            total_amount=Sum('amount'),
            transaction_count=Count('id')
        ).order_by('-total_amount')[:10]
        
        # Balance history (last 30 days)
        from datetime import timedelta
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        balance_history = transactions.filter(
            date__gte=thirty_days_ago
        ).extra(
            select={'date': "DATE(date)"}
        ).values('date').annotate(
            daily_balance=Sum('amount', filter=Q(type='credit')) - Sum('amount', filter=Q(type='debit'))
        ).order_by('date')
        
        return Response({
            'wallet_id': wallet.id,
            'current_balance': wallet.balance,
            'currency': wallet.currency,
            'monthly_trends': list(monthly_data),
            'top_categories': list(category_data),
            'balance_history': list(balance_history),
            'total_transactions': transactions.count(),
            'last_transaction_date': transactions.order_by('-date').first().date if transactions.exists() else None
        })

    @action(detail=True, methods=['get'])
    def risk_assessment(self, request, pk=None):
        """Get wallet risk assessment"""
        wallet = self.get_object()
        
        # Calculate risk factors
        transactions = EnhancedWalletTransaction.objects.filter(wallet=wallet)
        recent_transactions = transactions.filter(
            date__gte=timezone.now().date() - timedelta(days=7)
        )
        
        # Risk indicators
        risk_factors = {
            'high_frequency_transactions': recent_transactions.count() > 20,
            'large_transactions': transactions.filter(amount__gt=wallet.balance * 0.5).exists(),
            'negative_balance_history': transactions.filter(
                type='debit', amount__gt=wallet.balance
            ).exists(),
            'unusual_patterns': recent_transactions.filter(
                amount__gt=wallet.balance * 0.3
            ).count() > 3
        }
        
        risk_score = sum(risk_factors.values())
        risk_level = 'LOW' if risk_score == 0 else 'MEDIUM' if risk_score <= 2 else 'HIGH'
        
        return Response({
            'wallet_id': wallet.id,
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'recommendations': self._get_risk_recommendations(risk_level, risk_factors)
        })

    def _get_risk_recommendations(self, risk_level, risk_factors):
        """Get risk mitigation recommendations"""
        recommendations = []
        
        if risk_factors['high_frequency_transactions']:
            recommendations.append("Consider implementing transaction limits")
        
        if risk_factors['large_transactions']:
            recommendations.append("Review large transaction patterns")
        
        if risk_factors['negative_balance_history']:
            recommendations.append("Monitor balance closely to avoid overdrafts")
        
        if risk_factors['unusual_patterns']:
            recommendations.append("Investigate unusual transaction patterns")
        
        if risk_level == 'HIGH':
            recommendations.append("Consider implementing additional security measures")
        
        return recommendations

    @action(detail=True, methods=['post'])
    def freeze_wallet(self, request, pk=None):
        """Freeze wallet for security"""
        wallet = self.get_object()
        
        if wallet.status == 'frozen':
            return Response(
                {'error': 'Wallet is already frozen'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        wallet.status = 'frozen'
        wallet.save()
        
        # Log the freeze action
        EnhancedWalletTransaction.objects.create(
            wallet=wallet,
            type='system',
            amount=0,
            description='Wallet frozen for security',
            status='completed',
            reference=f'FREEZE_{timezone.now().strftime("%Y%m%d_%H%M%S")}'
        )
        
        return Response({
            'message': 'Wallet frozen successfully',
            'wallet_id': wallet.id,
            'status': wallet.status
        })

    @action(detail=True, methods=['post'])
    def unfreeze_wallet(self, request, pk=None):
        """Unfreeze wallet"""
        wallet = self.get_object()
        
        if wallet.status != 'frozen':
            return Response(
                {'error': 'Wallet is not frozen'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        wallet.status = 'active'
        wallet.save()
        
        # Log the unfreeze action
        EnhancedWalletTransaction.objects.create(
            wallet=wallet,
            type='system',
            amount=0,
            description='Wallet unfrozen',
            status='completed',
            reference=f'UNFREEZE_{timezone.now().strftime("%Y%m%d_%H%M%S")}'
        )
        
        return Response({
            'message': 'Wallet unfrozen successfully',
            'wallet_id': wallet.id,
            'status': wallet.status
        })


class EnhancedWalletTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing enhanced wallet transactions matching TypeScript interface"""
    queryset = EnhancedWalletTransaction.objects.all()
    serializer_class = EnhancedWalletTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'status', 'category', 'wallet']
    search_fields = ['description', 'reference']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        """Filter transactions by user's wallets"""
        user = self.request.user
        mse_ids = MSEWallet.objects.filter(mse__user=user).values_list('mse_id', flat=True)
        wallet_ids = EnhancedWallet.objects.filter(mse_id__in=mse_ids).values_list('id', flat=True)
        return EnhancedWalletTransaction.objects.filter(wallet_id__in=wallet_ids)

    @action(detail=False, methods=['get'])
    def transaction_types(self, request):
        """Get available transaction types"""
        types = [{'value': choice[0], 'label': choice[1]} 
                for choice in EnhancedWalletTransaction.TRANSACTION_TYPES]
        return Response(types)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available transaction categories"""
        categories = [{'value': choice[0], 'label': choice[1]} 
                     for choice in EnhancedWalletTransaction.CATEGORY_CHOICES]
        return Response(categories)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary matching TypeScript interface"""
        user = request.user
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        # Get user's wallets
        mse_ids = MSEWallet.objects.filter(mse__user=user).values_list('mse_id', flat=True)
        wallets = EnhancedWallet.objects.filter(mse_id__in=mse_ids)
        
        summary = {
            'total_balance': wallets.aggregate(total=Sum('balance'))['total'] or 0,
            'total_wallets': wallets.count(),
            'active_wallets': wallets.filter(status='Active').count(),
            'monthly_volume': wallets.aggregate(total=Sum('monthly_volume'))['total'] or 0,
            'monthly_transactions': EnhancedWalletTransaction.objects.filter(
                wallet__in=wallets, 
                date__date__gte=month_start
            ).count(),
            'currency': 'USD'  # Default currency, can be enhanced
        }
        
        return Response(summary)

    @action(detail=False, methods=['post'])
    def create_transaction(self, request):
        """Create a new wallet transaction using WalletTransactionRequest format"""
        serializer = WalletTransactionRequestSerializer(data=request.data)
        if serializer.is_valid():
            wallet_id = serializer.validated_data['wallet_id']
            
            try:
                wallet = EnhancedWallet.objects.get(id=wallet_id)
            except EnhancedWallet.DoesNotExist:
                return Response(
                    {'error': 'Wallet not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create the transaction
            transaction = EnhancedWalletTransaction.objects.create(
                wallet=wallet,
                type=serializer.validated_data['type'],
                amount=serializer.validated_data['amount'],
                description=serializer.validated_data['description'],
                category=serializer.validated_data.get('category', ''),
                reference=serializer.validated_data.get('reference', ''),
                status='Completed'  # Default to completed for immediate transactions
            )
            
            # Update wallet balance
            if transaction.status == 'Completed':
                transaction.update_wallet_balance()
            
            response_serializer = EnhancedWalletTransactionSerializer(transaction)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WalletTransferViewSet(viewsets.ModelViewSet):
    """ViewSet for managing wallet transfers"""
    queryset = WalletTransfer.objects.all()
    serializer_class = WalletTransferSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'currency']
    search_fields = ['description']
    ordering_fields = ['amount', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter transfers by user's wallets"""
        user = self.request.user
        mse_ids = MSEWallet.objects.filter(mse__user=user).values_list('mse_id', flat=True)
        wallet_ids = EnhancedWallet.objects.filter(mse_id__in=mse_ids).values_list('id', flat=True)
        return WalletTransfer.objects.filter(
            Q(from_wallet_id__in=wallet_ids) | Q(to_wallet_id__in=wallet_ids)
        )

    @action(detail=False, methods=['post'])
    def execute_transfer(self, request):
        """Execute a wallet transfer between two wallets"""
        serializer = WalletTransferSerializer(data=request.data)
        if serializer.is_valid():
            from_wallet_id = request.data.get('from_wallet_id')
            to_wallet_id = request.data.get('to_wallet_id')
            amount = serializer.validated_data['amount']
            description = serializer.validated_data['description']
            currency = serializer.validated_data['currency']
            
            try:
                from_wallet = EnhancedWallet.objects.get(id=from_wallet_id)
                to_wallet = EnhancedWallet.objects.get(id=to_wallet_id)
            except EnhancedWallet.DoesNotExist:
                return Response(
                    {'error': 'One or both wallets not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validate transfer
            if from_wallet.balance < amount:
                return Response(
                    {'error': 'Insufficient balance in source wallet'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if from_wallet.currency != to_wallet.currency:
                return Response(
                    {'error': 'Cannot transfer between different currencies'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create transfer record
            transfer = WalletTransfer.objects.create(
                from_wallet=from_wallet,
                to_wallet=to_wallet,
                amount=amount,
                description=description,
                currency=currency,
                status='Pending'
            )
            
            # Create debit transaction
            debit_tx = EnhancedWalletTransaction.objects.create(
                wallet=from_wallet,
                type='Debit',
                amount=amount,
                description=f"Transfer to {to_wallet.account_number}: {description}",
                category='Transfer',
                reference=f"TRF-{transfer.id}",
                status='Completed'
            )
            
            # Create credit transaction
            credit_tx = EnhancedWalletTransaction.objects.create(
                wallet=to_wallet,
                type='Credit',
                amount=amount,
                description=f"Transfer from {from_wallet.account_number}: {description}",
                category='Transfer',
                reference=f"TRF-{transfer.id}",
                status='Completed'
            )
            
            # Update transfer with transaction references
            transfer.debit_transaction = debit_tx
            transfer.credit_transaction = credit_tx
            transfer.status = 'Completed'
            transfer.save()
            
            # Update wallet balances
            debit_tx.update_wallet_balance()
            credit_tx.update_wallet_balance()
            
            response_serializer = WalletTransferSerializer(transfer)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WalletStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for wallet statistics"""
    queryset = WalletStatistics.objects.all()
    serializer_class = WalletStatisticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter statistics by user's wallets"""
        user = self.request.user
        mse_ids = MSEWallet.objects.filter(mse__user=user).values_list('mse_id', flat=True)
        wallet_ids = EnhancedWallet.objects.filter(mse_id__in=mse_ids).values_list('id', flat=True)
        return WalletStatistics.objects.filter(wallet_id__in=wallet_ids)

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get overview statistics for all user wallets"""
        user = request.user
        mse_ids = MSEWallet.objects.filter(mse__user=user).values_list('mse_id', flat=True)
        wallets = EnhancedWallet.objects.filter(mse_id__in=mse_ids)
        
        # Aggregate statistics
        total_balance = wallets.aggregate(total=Sum('balance'))['total'] or 0
        total_wallets = wallets.count()
        active_wallets = wallets.filter(status='Active').count()
        monthly_volume = wallets.aggregate(total=Sum('monthly_volume'))['total'] or 0
        
        # Get monthly transaction count
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_transactions = EnhancedWalletTransaction.objects.filter(
            wallet__in=wallets,
            date__gte=month_start
        ).count()
        
        overview = {
            'total_balance': total_balance,
            'total_wallets': total_wallets,
            'active_wallets': active_wallets,
            'monthly_volume': monthly_volume,
            'monthly_transactions': monthly_transactions,
            'currency': 'USD'  # Default currency
        }
        
        return Response(overview)


# Legacy ViewSets for backward compatibility
class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing transaction categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available category types"""
        types = [{'value': choice[0], 'label': choice[1]} 
                for choice in Category.CATEGORY_TYPES]
        return Response(types)


class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet for managing legacy wallets"""
    queryset = MSEWallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['wallet_type', 'is_active', 'currency']
    search_fields = ['name', 'account_number']
    ordering_fields = ['name', 'balance', 'created_at']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available wallet types"""
        types = [{'value': choice[0], 'label': choice[1]} 
                for choice in MSEWallet.WALLET_TYPES]
        return Response(types)

    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get wallet balance"""
        wallet = self.get_object()
        return Response({
            'wallet_id': wallet.id,
            'wallet_name': wallet.name,
            'balance': wallet.balance,
            'currency': wallet.currency
        })


class WalletTransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing legacy wallet transactions"""
    queryset = MSEWalletTransaction.objects.all()
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transaction_type', 'status', 'category', 'wallet']
    search_fields = ['description', 'reference']
    ordering_fields = ['transaction_date', 'amount', 'created_at']
    ordering = ['-transaction_date']

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available transaction types"""
        types = [{'value': choice[0], 'label': choice[1]} 
                for choice in MSEWalletTransaction.TRANSACTION_TYPES]
        return Response(types)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary"""
        user = request.user
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        # Get user's wallets
        wallets = MSEWallet.objects.filter(mse__user=user)
        
        summary = {
            'total_balance': wallets.aggregate(total=Sum('balance'))['total'] or 0,
            'total_transactions_today': MSEWalletTransaction.objects.filter(
                wallet__in=wallets, transaction_date__date=today
            ).count(),
            'total_transactions_month': MSEWalletTransaction.objects.filter(
                wallet__in=wallets, transaction_date__date__gte=month_start
            ).count(),
            'monthly_income': MSEWalletTransaction.objects.filter(
                wallet__in=wallets, 
                transaction_type='credit',
                transaction_date__date__gte=month_start
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'monthly_expenses': MSEWalletTransaction.objects.filter(
                wallet__in=wallets, 
                transaction_type='debit',
                transaction_date__date__gte=month_start
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        return Response(summary)


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing financial transactions"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transaction_type', 'status', 'category', 'wallet', 'currency']
    search_fields = ['title', 'description', 'reference_number']
    ordering_fields = ['transaction_date', 'amount', 'created_at']
    ordering = ['-transaction_date']

    def get_queryset(self):
        """Filter transactions by current user"""
        return Transaction.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return TransactionCreateSerializer
        return TransactionSerializer

    def perform_create(self, serializer):
        """Set the user when creating a transaction"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available transaction types"""
        types = [{'value': choice[0], 'label': choice[1]} 
                for choice in Transaction.TRANSACTION_TYPES]
        return Response(types)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary for current user"""
        user = request.user
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        summary = {
            'total_transactions': Transaction.objects.filter(user=user).count(),
            'total_transactions_today': Transaction.objects.filter(
                user=user, transaction_date__date=today
            ).count(),
            'total_transactions_month': Transaction.objects.filter(
                user=user, transaction_date__date__gte=month_start
            ).count(),
            'monthly_income': Transaction.objects.filter(
                user=user, 
                transaction_type='income',
                transaction_date__date__gte=month_start
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'monthly_expenses': Transaction.objects.filter(
                user=user, 
                transaction_type='expense',
                transaction_date__date__gte=month_start
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        return Response(summary)


class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing budgets"""
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['budget_type', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'end_date', 'total_amount', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        """Filter budgets by current user"""
        return Budget.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return BudgetCreateSerializer
        return BudgetSerializer

    def perform_create(self, serializer):
        """Set the user when creating a budget"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available budget types"""
        types = [{'value': choice[0], 'label': choice[1]} 
                for choice in Budget.BUDGET_TYPES]
        return Response(types)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active budgets for current user"""
        active_budgets = Budget.objects.filter(
            user=request.user, 
            status='active',
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        )
        serializer = self.get_serializer(active_budgets, many=True)
        return Response(serializer.data)


class GoalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing financial goals"""
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['goal_type', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['target_date', 'target_amount', 'progress_percentage', 'created_at']
    ordering = ['-target_date']

    def get_queryset(self):
        """Filter goals by current user"""
        return Goal.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return GoalCreateSerializer
        return GoalSerializer

    def perform_create(self, serializer):
        """Set the user when creating a goal"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def types(self, request):
        """Get available goal types"""
        types = [{'value': choice[0], 'label': choice[1]} 
                for choice in Goal.GOAL_TYPES]
        return Response(types)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active goals for current user"""
        active_goals = Goal.objects.filter(
            user=request.user, 
            status='active'
        )
        serializer = self.get_serializer(active_goals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update goal progress"""
        goal = self.get_object()
        amount = request.data.get('amount', 0)
        
        if amount < 0:
            return Response(
                {'error': 'Amount cannot be negative'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        goal.current_amount += amount
        goal.save()
        
        serializer = self.get_serializer(goal)
        return Response(serializer.data)


# Payment Transaction ViewSets
class PaymentTransactionViewSet(viewsets.ModelViewSet):
    """Payment transaction management viewset"""
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transaction_type', 'provider', 'status']
    search_fields = ['phone_number', 'reference', 'description']
    ordering_fields = ['amount', 'timestamp', 'status']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        return PaymentTransaction.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel_transaction(self, request, pk=None):
        """Cancel a pending transaction"""
        transaction = self.get_object()
        
        if not transaction.can_be_cancelled():
            return Response(
                {'error': 'Transaction cannot be cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        transaction.status = 'cancelled'
        transaction.save()
        
        serializer = self.get_serializer(transaction)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm_transaction(self, request, pk=None):
        """Confirm a transaction with confirmation code"""
        transaction = self.get_object()
        confirmation_code = request.data.get('confirmation_code')
        
        if not confirmation_code:
            return Response(
                {'error': 'Confirmation code is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Here you would validate the confirmation code with the provider
        # For now, we'll simulate confirmation
        transaction.confirmation_code = confirmation_code
        transaction.status = 'completed'
        transaction.save()
        
        serializer = self.get_serializer(transaction)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get payment transaction summary statistics"""
        queryset = self.get_queryset()
        
        total_transactions = queryset.count()
        total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0
        successful_transactions = queryset.filter(status='completed').count()
        failed_transactions = queryset.filter(status='failed').count()
        total_fees = queryset.aggregate(total=Sum('fee'))['total'] or 0
        
        success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
        
        recent_transactions = queryset.order_by('-timestamp')[:10].values(
            'id', 'transaction_type', 'provider', 'amount', 'status', 'timestamp'
        )
        
        data = {
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'successful_transactions': successful_transactions,
            'failed_transactions': failed_transactions,
            'success_rate': success_rate,
            'total_fees': total_fees,
            'recent_transactions': list(recent_transactions),
        }
        
        serializer = PaymentSummarySerializer(data)
        return Response(serializer.data)


class BulkPaymentViewSet(viewsets.ModelViewSet):
    """Bulk payment management viewset"""
    serializer_class = BulkPaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'scheduled_date']
    search_fields = ['name']
    ordering_fields = ['total_amount', 'recipient_count', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return BulkPayment.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def process_bulk_payment(self, request, pk=None):
        """Process a bulk payment"""
        bulk_payment = self.get_object()
        
        if not bulk_payment.can_be_processed():
            return Response(
                {'error': 'Bulk payment cannot be processed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bulk_payment.mark_as_processing()
        
        # Here you would process each recipient
        # For now, we'll simulate processing
        recipients = bulk_payment.recipients.all()
        success_count = 0
        failure_count = 0
        
        for recipient in recipients:
            # Simulate processing with 90% success rate
            import random
            if random.random() < 0.9:
                recipient.mark_as_sent(f"REF_{recipient.id}")
                success_count += 1
            else:
                recipient.mark_as_failed("Failed")
                failure_count += 1
        
        if failure_count == 0:
            bulk_payment.mark_as_completed()
        else:
            bulk_payment.mark_as_failed()
        
        serializer = self.get_serializer(bulk_payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def schedule_bulk_payment(self, request, pk=None):
        """Schedule a bulk payment"""
        bulk_payment = self.get_object()
        scheduled_date = request.data.get('scheduled_date')
        
        if not scheduled_date:
            return Response(
                {'error': 'Scheduled date is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bulk_payment.scheduled_date = scheduled_date
        bulk_payment.status = 'scheduled'
        bulk_payment.save()
        
        serializer = self.get_serializer(bulk_payment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get bulk payment summary statistics"""
        queryset = self.get_queryset()
        
        total_bulk_payments = queryset.count()
        total_recipients = queryset.aggregate(total=Sum('recipient_count'))['total'] or 0
        total_amount_sent = queryset.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Calculate average success rate
        success_rates = []
        for bulk_payment in queryset:
            if bulk_payment.recipient_count > 0:
                success_rates.append(bulk_payment.get_success_rate())
        
        average_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        
        recent_bulk_payments = queryset.order_by('-created_at')[:5].values(
            'id', 'name', 'total_amount', 'recipient_count', 'status', 'created_at'
        )
        
        data = {
            'total_bulk_payments': total_bulk_payments,
            'total_recipients': total_recipients,
            'total_amount_sent': total_amount_sent,
            'average_success_rate': average_success_rate,
            'recent_bulk_payments': list(recent_bulk_payments),
        }
        
        serializer = BulkPaymentSummarySerializer(data)
        return Response(serializer.data)


class BulkPaymentRecipientViewSet(viewsets.ModelViewSet):
    """Bulk payment recipient management viewset"""
    serializer_class = BulkPaymentRecipientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'bulk_payment']
    search_fields = ['phone_number', 'name']
    ordering_fields = ['amount', 'created_at']
    ordering = ['created_at']
    
    def get_queryset(self):
        # Filter recipients by bulk payments owned by the user
        return BulkPaymentRecipient.objects.filter(bulk_payment__user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def retry_payment(self, request, pk=None):
        """Retry a failed payment"""
        recipient = self.get_object()
        
        if recipient.status != 'failed':
            return Response(
                {'error': 'Only failed payments can be retried'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Here you would retry the payment
        # For now, we'll simulate retry with 80% success rate
        import random
        if random.random() < 0.8:
            recipient.mark_as_sent(f"RETRY_REF_{recipient.id}")
            message = "Payment retry successful"
        else:
            recipient.mark_as_failed("Retry failed")
            message = "Payment retry failed"
        
        serializer = self.get_serializer(recipient)
        return Response({
            'message': message,
            'recipient': serializer.data
        })

