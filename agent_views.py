from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from authentication.models import CustomUser
from authentication.serializers import UserSummarySerializer, UserUpdateSerializer
from mse.models import MSE, Wallet
from markets.models import Transaction, Customer, Supplier
from loans.models import GroupLoan, GroupLoanRepayment
from wallet.models import WalletTransaction
from partner_dashboard.permissions import IsAgent, AgentAccessPermission
from partner_dashboard.permissions import CanViewReports, CanExportData


class AgentMSEViewSet(viewsets.ModelViewSet):
    """Agent management of assigned MSEs"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsAgent]
    
    def get_queryset(self):
        """Only show MSEs assigned to this agent"""
        return MSE.objects.filter(assigned_agent=self.request.user)
    
    def get_queryset(self):
        queryset = MSE.objects.filter(assigned_agent=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(business_name__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an assigned MSE"""
        mse = self.get_object()
        mse.status = 'approved'
        mse.approval_date = timezone.now()
        mse.approved_by = request.user
        mse.save()
        
        return Response({
            'message': f'MSE {mse.full_name} approved successfully'
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an assigned MSE"""
        mse = self.get_object()
        mse.status = 'rejected'
        mse.save()
        
        return Response({
            'message': f'MSE {mse.full_name} rejected'
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics for assigned MSEs"""
        assigned_mses = MSE.objects.filter(assigned_agent=request.user)
        
        total_mse = assigned_mses.count()
        approved_mse = assigned_mses.filter(status='approved').count()
        pending_mse = assigned_mses.filter(status='pending').count()
        rejected_mse = assigned_mses.filter(status='rejected').count()
        
        category_counts = assigned_mses.values('category__name').annotate(
            count=Count('id')
        )
        
        recent_mse = assigned_mses.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return Response({
            'total_assigned_mse': total_mse,
            'approved_mse': approved_mse,
            'pending_mse': pending_mse,
            'rejected_mse': rejected_mse,
            'recent_mse': recent_mse,
            'category_distribution': category_counts
        })


class AgentWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """Agent view of assigned MSE wallets"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsAgent]
    
    def get_queryset(self):
        """Only show wallets of assigned MSEs"""
        return Wallet.objects.filter(mse__assigned_agent=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get wallet summary for assigned MSEs"""
        assigned_wallets = Wallet.objects.filter(mse__assigned_agent=request.user)
        
        total_balance = assigned_wallets.aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        active_wallets = assigned_wallets.filter(is_active=True).count()
        total_wallets = assigned_wallets.count()
        
        # Top wallets by balance
        top_wallets = assigned_wallets.order_by('-balance')[:5].values(
            'mse__first_name', 'mse__last_name', 'balance', 'currency'
        )
        
        return Response({
            'total_balance': total_balance,
            'active_wallets': active_wallets,
            'total_wallets': total_wallets,
            'top_wallets': top_wallets
        })
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get transactions for a specific wallet"""
        wallet = self.get_object()
        transactions = wallet.transactions.all().order_by('-created_at')[:50]
        
        # This would need a proper serializer
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'id': transaction.id,
                'type': transaction.transaction_type,
                'amount': transaction.amount,
                'currency': transaction.currency,
                'status': transaction.status,
                'created_at': transaction.created_at,
                'description': transaction.description
            })
        
        return Response({
            'wallet_id': wallet.id,
            'mse_name': wallet.mse.full_name,
            'transactions': transaction_data
        })


class AgentRegistrationViewSet(viewsets.ReadOnlyModelViewSet):
    """Agent tracking of registration status for assigned users"""
    
    serializer_class = UserSummarySerializer
    permission_classes = [IsAgent]
    
    def get_queryset(self):
        """Only show users assigned to this agent"""
        return CustomUser.objects.filter(assigned_agent=self.request.user)
    
    def get_queryset(self):
        queryset = CustomUser.objects.filter(assigned_agent=self.request.user)
        
        # Filter by approval status
        is_approved = self.request.query_params.get('is_approved')
        if is_approved is not None:
            queryset = queryset.filter(is_approved=is_approved.lower() == 'true')
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get pending approvals for assigned users"""
        pending_users = CustomUser.objects.filter(
            assigned_agent=request.user,
            is_approved=False
        )
        
        return Response({
            'pending_count': pending_users.count(),
            'pending_users': UserSummarySerializer(pending_users, many=True).data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get registration statistics for assigned users"""
        assigned_users = CustomUser.objects.filter(assigned_agent=request.user)
        
        total_users = assigned_users.count()
        approved_users = assigned_users.filter(is_approved=True).count()
        pending_users = assigned_users.filter(is_approved=False).count()
        
        role_counts = assigned_users.values('role').annotate(
            count=Count('id')
        )
        
        recent_users = assigned_users.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return Response({
            'total_assigned_users': total_users,
            'approved_users': approved_users,
            'pending_users': pending_users,
            'recent_users': recent_users,
            'role_distribution': role_counts
        })


class AgentReportViewSet(viewsets.ViewSet):
    """Agent reports and analytics for assigned users"""
    
    permission_classes = [IsAgent, CanViewReports]
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Get dashboard summary for assigned users"""
        
        # User statistics
        assigned_users = CustomUser.objects.filter(assigned_agent=request.user)
        user_stats = {
            'total_assigned_users': assigned_users.count(),
            'total_mse_users': assigned_users.filter(role='mse').count(),
            'total_partner_users': assigned_users.filter(role='partner').count(),
            'pending_approvals': assigned_users.filter(is_approved=False).count(),
        }
        
        # MSE statistics
        assigned_mses = MSE.objects.filter(assigned_agent=request.user)
        mse_stats = {
            'total_assigned_mse': assigned_mses.count(),
            'approved_mse': assigned_mses.filter(status='approved').count(),
            'pending_mse': assigned_mses.filter(status='pending').count(),
            'rejected_mse': assigned_mses.filter(status='rejected').count(),
        }
        
        # Financial statistics
        assigned_wallets = Wallet.objects.filter(mse__assigned_agent=request.user)
        financial_stats = {
            'total_wallet_balance': assigned_wallets.aggregate(
                total=Sum('balance')
            )['total'] or 0,
            'total_wallets': assigned_wallets.count(),
            'active_wallets': assigned_wallets.filter(is_active=True).count(),
        }
        
        # Recent activity
        recent_activity = {
            'new_users_this_week': assigned_users.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'new_mse_this_week': assigned_mses.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'pending_approvals': assigned_users.filter(
                is_approved=False
            ).count(),
        }
        
        return Response({
            'user_statistics': user_stats,
            'mse_statistics': mse_stats,
            'financial_statistics': financial_stats,
            'recent_activity': recent_activity,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def user_performance_report(self, request):
        """Get performance report for assigned users"""
        
        # Date range filtering
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        assigned_users = CustomUser.objects.filter(assigned_agent=request.user)
        
        # User registration trends
        user_registrations = assigned_users.filter(
            created_at__gte=start_date
        ).extra(
            select={'date': 'date(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Role distribution
        role_distribution = assigned_users.values('role').annotate(
            count=Count('id')
        )
        
        # Approval statistics
        approval_stats = {
            'total_pending': assigned_users.filter(is_approved=False).count(),
            'total_approved': assigned_users.filter(is_approved=True).count(),
            'approval_rate': (
                assigned_users.filter(is_approved=True).count() /
                assigned_users.count() * 100
            ) if assigned_users.count() > 0 else 0
        }
        
        return Response({
            'period': f'Last {days} days',
            'user_registrations': user_registrations,
            'role_distribution': role_distribution,
            'approval_statistics': approval_stats,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def mse_performance_report(self, request):
        """Get MSE performance report for assigned MSEs"""
        
        # Date range filtering
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        assigned_mses = MSE.objects.filter(assigned_agent=request.user)
        
        # MSE registration trends
        mse_registrations = assigned_mses.filter(
            created_at__gte=start_date
        ).extra(
            select={'date': 'date(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Category distribution
        category_distribution = assigned_mses.values('category__name').annotate(
            count=Count('id')
        )
        
        # Status distribution
        status_distribution = assigned_mses.values('status').annotate(
            count=Count('id')
        )
        
        # Location distribution
        location_distribution = assigned_mses.values('location').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'period': f'Last {days} days',
            'mse_registrations': mse_registrations,
            'category_distribution': category_distribution,
            'status_distribution': status_distribution,
            'top_locations': location_distribution,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """Export data for assigned users"""
        
        if not request.user.can_export_data:
            return Response({
                'error': 'You do not have permission to export data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # This would implement actual data export functionality
        return Response({
            'message': 'Data export functionality will be implemented here',
            'available_formats': ['csv', 'excel', 'pdf']
        })
