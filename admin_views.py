from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from authentication.models import CustomUser
from authentication.serializers import UserDetailSerializer, UserCreateSerializer, UserUpdateSerializer
from mse.models import MSE, Wallet
from markets.models import Transaction, Customer, Supplier
from loans.models import GroupLoan, GroupLoanRepayment
from wallet.models import WalletTransaction
from partner_dashboard.permissions import IsSuperAdmin, CanManageUsers, CanManageMSE
from partner_dashboard.permissions import CanViewReports, CanExportData


class SuperAdminUserViewSet(viewsets.ModelViewSet):
    """Super Admin CRUD operations for users"""
    
    queryset = CustomUser.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsSuperAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by role if specified
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by approval status
        is_approved = self.request.query_params.get('is_approved')
        if is_approved is not None:
            queryset = queryset.filter(is_approved=is_approved.lower() == 'true')
        
        # Search by name or username
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(username__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a user account"""
        user = self.get_object()
        user.is_approved = True
        user.save()
        
        return Response({
            'message': f'User {user.username} approved successfully'
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a user account"""
        user = self.get_object()
        user.is_approved = False
        user.save()
        
        return Response({
            'message': f'User {user.username} rejected'
        })
    
    @action(detail=True, methods=['post'])
    def assign_agent(self, request, pk=None):
        """Assign a user to an agent"""
        user = self.get_object()
        agent_id = request.data.get('agent_id')
        
        if not agent_id:
            return Response({
                'error': 'Agent ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            agent = CustomUser.objects.get(id=agent_id, role='agent')
            user.assigned_agent = agent
            user.save()
            
            return Response({
                'message': f'User assigned to agent {agent.first_name} {agent.last_name}'
            })
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'Invalid agent ID'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get user statistics"""
        total_users = CustomUser.objects.count()
        total_approved = CustomUser.objects.filter(is_approved=True).count()
        total_pending = CustomUser.objects.filter(is_approved=False).count()
        
        role_counts = CustomUser.objects.values('role').annotate(
            count=Count('id')
        )
        
        recent_users = CustomUser.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return Response({
            'total_users': total_users,
            'total_approved': total_approved,
            'total_pending': total_pending,
            'recent_users': recent_users,
            'role_distribution': role_counts
        })


class SuperAdminMSEViewSet(viewsets.ModelViewSet):
    """Super Admin CRUD operations for MSEs"""
    
    queryset = MSE.objects.all()
    serializer_class = None  # Will be set based on action
    permission_classes = [IsSuperAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Filter by location
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
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
        """Approve an MSE"""
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
        """Reject an MSE"""
        mse = self.get_object()
        mse.status = 'rejected'
        mse.save()
        
        return Response({
            'message': f'MSE {mse.full_name} rejected'
        })
    
    @action(detail=True, methods=['post'])
    def assign_agent(self, request, pk=None):
        """Assign an MSE to an agent"""
        mse = self.get_object()
        agent_id = request.data.get('agent_id')
        
        if not agent_id:
            return Response({
                'error': 'Agent ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            agent = CustomUser.objects.get(id=agent_id, role='agent')
            mse.assigned_agent = agent
            mse.save()
            
            return Response({
                'message': f'MSE assigned to agent {agent.first_name} {agent.last_name}'
            })
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'Invalid agent ID'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get MSE statistics"""
        total_mse = MSE.objects.count()
        approved_mse = MSE.objects.filter(status='approved').count()
        pending_mse = MSE.objects.filter(status='pending').count()
        rejected_mse = MSE.objects.filter(status='rejected').count()
        
        category_counts = MSE.objects.values('category__name').annotate(
            count=Count('id')
        )
        
        location_counts = MSE.objects.values('location').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        recent_mse = MSE.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return Response({
            'total_mse': total_mse,
            'approved_mse': approved_mse,
            'pending_mse': pending_mse,
            'rejected_mse': rejected_mse,
            'recent_mse': recent_mse,
            'category_distribution': category_counts,
            'top_locations': location_counts
        })


class SuperAdminReportViewSet(viewsets.ViewSet):
    """Super Admin reports and analytics"""
    
    permission_classes = [IsSuperAdmin, CanViewReports]
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Get comprehensive dashboard summary"""
        
        # User statistics
        user_stats = {
            'total_users': CustomUser.objects.count(),
            'total_mse_users': CustomUser.objects.filter(role='mse').count(),
            'total_agents': CustomUser.objects.filter(role='agent').count(),
            'total_partners': CustomUser.objects.filter(role='partner').count(),
            'pending_approvals': CustomUser.objects.filter(is_approved=False).count(),
        }
        
        # MSE statistics
        mse_stats = {
            'total_mse': MSE.objects.count(),
            'approved_mse': MSE.objects.filter(status='approved').count(),
            'pending_mse': MSE.objects.filter(status='pending').count(),
            'rejected_mse': MSE.objects.filter(status='rejected').count(),
        }
        
        # Financial statistics
        financial_stats = {
            'total_wallet_balance': Wallet.objects.aggregate(
                total=Sum('balance')
            )['total'] or 0,
            'total_transactions': Transaction.objects.count(),
            'total_loans': GroupLoan.objects.count(),
            'active_loans': GroupLoan.objects.filter(status='active').count(),
        }
        
        # Recent activity
        recent_activity = {
            'new_users_today': CustomUser.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'new_mse_today': MSE.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'pending_approvals': CustomUser.objects.filter(
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
    def financial_report(self, request):
        """Get detailed financial report"""
        
        # Date range filtering
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Transaction statistics
        transactions = Transaction.objects.filter(
            transaction_date__gte=start_date
        )
        
        transaction_stats = {
            'total_transactions': transactions.count(),
            'total_amount': transactions.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'by_type': transactions.values('transaction_type').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
        }
        
        # Wallet statistics
        wallet_stats = {
            'total_balance': Wallet.objects.aggregate(
                total=Sum('balance')
            )['total'] or 0,
            'active_wallets': Wallet.objects.filter(is_active=True).count(),
            'total_wallets': Wallet.objects.count(),
        }
        
        # Loan statistics
        loan_stats = {
            'total_loans': GroupLoan.objects.count(),
            'active_loans': GroupLoan.objects.filter(status='active').count(),
            'total_loan_amount': GroupLoan.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'total_outstanding': GroupLoan.objects.filter(
                status='active'
            ).aggregate(
                total=Sum('outstanding_balance')
            )['total'] or 0,
        }
        
        return Response({
            'period': f'Last {days} days',
            'transaction_statistics': transaction_stats,
            'wallet_statistics': wallet_stats,
            'loan_statistics': loan_stats,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def user_activity_report(self, request):
        """Get user activity report"""
        
        # Date range filtering
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # User registration trends
        user_registrations = CustomUser.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'date': 'date(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Role distribution
        role_distribution = CustomUser.objects.values('role').annotate(
            count=Count('id')
        )
        
        # Approval statistics
        approval_stats = {
            'total_pending': CustomUser.objects.filter(is_approved=False).count(),
            'total_approved': CustomUser.objects.filter(is_approved=True).count(),
            'approval_rate': (
                CustomUser.objects.filter(is_approved=True).count() /
                CustomUser.objects.count() * 100
            ) if CustomUser.objects.count() > 0 else 0
        }
        
        # Agent performance
        agent_performance = CustomUser.objects.filter(
            role='agent'
        ).annotate(
            assigned_users_count=Count('assigned_mse_users')
        ).values(
            'id', 'first_name', 'last_name', 'assigned_users_count'
        ).order_by('-assigned_users_count')
        
        return Response({
            'period': f'Last {days} days',
            'user_registrations': user_registrations,
            'role_distribution': role_distribution,
            'approval_statistics': approval_stats,
            'agent_performance': agent_performance,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """Export data in various formats"""
        
        if not request.user.can_export_data:
            return Response({
                'error': 'You do not have permission to export data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # This would implement actual data export functionality
        # For now, return a message
        return Response({
            'message': 'Data export functionality will be implemented here',
            'available_formats': ['csv', 'excel', 'pdf']
        })
