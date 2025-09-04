from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from authentication.models import CustomUser
from mse.models import MSE, Wallet
from markets.models import Transaction, Customer, Supplier, Product
from loans.models import GroupLoan, GroupLoanRepayment
from wallet.models import WalletTransaction
from partner_dashboard.permissions import IsPartner, PartnerAccessPermission
from partner_dashboard.permissions import CanViewReports, CanExportData


class PartnerMSEViewSet(viewsets.ReadOnlyModelViewSet):
    """Partner access to partner-linked MSEs"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsPartner]
    
    def get_queryset(self):
        """Only show MSEs linked to this partner through assigned agent"""
        return MSE.objects.filter(owner__assigned_agent=self.request.user.assigned_agent)
    
    def get_queryset(self):
        queryset = MSE.objects.filter(owner__assigned_agent=self.request.user.assigned_agent)
        
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
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get statistics for partner-linked MSEs"""
        linked_mses = MSE.objects.filter(owner__assigned_agent=request.user.assigned_agent)
        
        total_mse = linked_mses.count()
        approved_mse = linked_mses.filter(status='approved').count()
        pending_mse = linked_mses.filter(status='pending').count()
        rejected_mse = linked_mses.filter(status='rejected').count()
        
        category_counts = linked_mses.values('category__name').annotate(
            count=Count('id')
        )
        
        location_counts = linked_mses.values('location').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'total_linked_mse': total_mse,
            'approved_mse': approved_mse,
            'pending_mse': pending_mse,
            'rejected_mse': rejected_mse,
            'category_distribution': category_counts,
            'top_locations': location_counts
        })


class PartnerCustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """Partner access to customer data from linked MSEs"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsPartner]
    
    def get_queryset(self):
        """Only show customers from MSEs linked to this partner"""
        return Customer.objects.filter(mse__owner__assigned_agent=self.request.user.assigned_agent)
    
    def get_queryset(self):
        queryset = Customer.objects.filter(mse__owner__assigned_agent=self.request.user.assigned_agent)
        
        # Filter by customer type
        customer_type = self.request.query_params.get('customer_type')
        if customer_type:
            queryset = queryset.filter(customer_type=customer_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by MSE
        mse_id = self.request.query_params.get('mse_id')
        if mse_id:
            queryset = queryset.filter(mse_id=mse_id)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(business_name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get customer statistics for partner-linked MSEs"""
        linked_customers = Customer.objects.filter(
            mse__owner__assigned_agent=request.user.assigned_agent
        )
        
        total_customers = linked_customers.count()
        active_customers = linked_customers.filter(is_active=True).count()
        
        type_counts = linked_customers.values('customer_type').annotate(
            count=Count('id')
        )
        
        mse_counts = linked_customers.values('mse__first_name', 'mse__last_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        total_credit_limit = linked_customers.aggregate(
            total=Sum('credit_limit')
        )['total'] or 0
        
        return Response({
            'total_customers': total_customers,
            'active_customers': active_customers,
            'type_distribution': type_counts,
            'top_mse_by_customers': mse_counts,
            'total_credit_limit': total_credit_limit
        })


class PartnerSupplierViewSet(viewsets.ReadOnlyModelViewSet):
    """Partner access to supplier data from linked MSEs"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsPartner]
    
    def get_queryset(self):
        """Only show suppliers from MSEs linked to this partner"""
        return Supplier.objects.filter(mse__owner__assigned_agent=self.request.user.assigned_agent)
    
    def get_queryset(self):
        queryset = Supplier.objects.filter(mse__owner__assigned_agent=self.request.user.assigned_agent)
        
        # Filter by supplier type
        supplier_type = self.request.query_params.get('supplier_type')
        if supplier_type:
            queryset = queryset.filter(supplier_type=supplier_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by MSE
        mse_id = self.request.query_params.get('mse_id')
        if mse_id:
            queryset = queryset.filter(mse_id=mse_id)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(business_name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get supplier statistics for partner-linked MSEs"""
        linked_suppliers = Supplier.objects.filter(
            mse__owner__assigned_agent=request.user.assigned_agent
        )
        
        total_suppliers = linked_suppliers.count()
        active_suppliers = linked_suppliers.filter(is_active=True).count()
        
        type_counts = linked_suppliers.values('supplier_type').annotate(
            count=Count('id')
        )
        
        mse_counts = linked_suppliers.values('mse__first_name', 'mse__last_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Average rating
        avg_rating = linked_suppliers.aggregate(
            avg_rating=Sum('rating') / Count('id')
        )['avg_rating'] or 0
        
        return Response({
            'total_suppliers': total_suppliers,
            'active_suppliers': active_suppliers,
            'type_distribution': type_counts,
            'top_mse_by_suppliers': mse_counts,
            'average_rating': round(avg_rating, 2)
        })


class PartnerTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Partner access to transaction data from linked MSEs"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsPartner]
    
    def get_queryset(self):
        """Only show transactions from MSEs linked to this partner"""
        return Transaction.objects.filter(mse__owner__assigned_agent=self.request.user.assigned_agent)
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(mse__owner__assigned_agent=self.request.user.assigned_agent)
        
        # Filter by transaction type
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(transaction_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(transaction_date__lte=end_date)
        
        # Filter by MSE
        mse_id = self.request.query_params.get('mse_id')
        if mse_id:
            queryset = queryset.filter(mse_id=mse_id)
        
        # Search by description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(description__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary for partner-linked MSEs"""
        linked_transactions = Transaction.objects.filter(
            mse__owner__assigned_agent=request.user.assigned_agent
        )
        
        total_transactions = linked_transactions.count()
        total_amount = linked_transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        type_counts = linked_transactions.values('transaction_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        mse_counts = linked_transactions.values('mse__first_name', 'mse__last_name').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')[:10]
        
        return Response({
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'type_distribution': type_counts,
            'top_mse_by_transactions': mse_counts
        })


class PartnerModalViewSet(viewsets.ViewSet):
    """Partner detailed lists for modals"""
    
    permission_classes = [IsPartner]
    
    @action(detail=False, methods=['get'])
    def mse_list(self, request):
        """Get detailed MSE list for modal display"""
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        linked_mses = MSE.objects.filter(
            owner__assigned_agent=request.user.assigned_agent
        ).select_related('category', 'owner')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            linked_mses = linked_mses.filter(status=status_filter)
        
        category_filter = request.query_params.get('category')
        if category_filter:
            linked_mses = linked_mses.filter(category__name=category_filter)
        
        # Search
        search = request.query_params.get('search')
        if search:
            linked_mses = linked_mses.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(business_name__icontains=search)
            )
        
        total_count = linked_mses.count()
        mses = linked_mses[start:end]
        
        mse_data = []
        for mse in mses:
            mse_data.append({
                'id': mse.id,
                'name': mse.full_name,
                'business_name': mse.business_name,
                'category': mse.category.name,
                'location': mse.location,
                'status': mse.status,
                'owner_name': f"{mse.owner.first_name} {mse.owner.last_name}",
                'owner_phone': mse.owner.phone_number,
                'created_at': mse.created_at,
                'approval_date': mse.approval_date
            })
        
        return Response({
            'mses': mse_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })
    
    @action(detail=False, methods=['get'])
    def customer_list(self, request):
        """Get detailed customer list for modal display"""
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        linked_customers = Customer.objects.filter(
            mse__owner__assigned_agent=request.user.assigned_agent
        ).select_related('mse', 'mse__owner')
        
        # Apply filters
        customer_type = request.query_params.get('customer_type')
        if customer_type:
            linked_customers = linked_customers.filter(customer_type=customer_type)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            linked_customers = linked_customers.filter(is_active=is_active.lower() == 'true')
        
        # Search
        search = request.query_params.get('search')
        if search:
            linked_customers = linked_customers.filter(
                Q(name__icontains=search) |
                Q(business_name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        total_count = linked_customers.count()
        customers = linked_customers[start:end]
        
        customer_data = []
        for customer in customers:
            customer_data.append({
                'id': customer.id,
                'name': customer.name,
                'customer_type': customer.customer_type,
                'business_name': customer.business_name,
                'phone': customer.phone,
                'email': customer.email,
                'credit_limit': customer.credit_limit,
                'current_balance': customer.current_balance,
                'mse_name': customer.mse.full_name,
                'mse_owner': f"{customer.mse.owner.first_name} {customer.mse.owner.last_name}",
                'created_at': customer.created_at
            })
        
        return Response({
            'customers': customer_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })
    
    @action(detail=False, methods=['get'])
    def supplier_list(self, request):
        """Get detailed supplier list for modal display"""
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        linked_suppliers = Supplier.objects.filter(
            mse__owner__assigned_agent=request.user.assigned_agent
        ).select_related('mse', 'mse__owner')
        
        # Apply filters
        supplier_type = request.query_params.get('supplier_type')
        if supplier_type:
            linked_suppliers = linked_suppliers.filter(supplier_type=supplier_type)
        
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            linked_suppliers = linked_suppliers.filter(is_active=is_active.lower() == 'true')
        
        # Search
        search = request.query_params.get('search')
        if search:
            linked_suppliers = linked_suppliers.filter(
                Q(name__icontains=search) |
                Q(business_name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        total_count = linked_suppliers.count()
        suppliers = linked_suppliers[start:end]
        
        supplier_data = []
        for supplier in suppliers:
            supplier_data.append({
                'id': supplier.id,
                'name': supplier.name,
                'supplier_type': supplier.supplier_type,
                'business_name': supplier.business_name,
                'phone': supplier.phone,
                'email': supplier.email,
                'rating': supplier.rating,
                'credit_terms': supplier.credit_terms,
                'mse_name': supplier.mse.full_name,
                'mse_owner': f"{supplier.mse.owner.first_name} {supplier.mse.owner.last_name}",
                'created_at': supplier.created_at
            })
        
        return Response({
            'suppliers': supplier_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })
    
    @action(detail=False, methods=['get'])
    def transaction_list(self, request):
        """Get detailed transaction list for modal display"""
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        linked_transactions = Transaction.objects.filter(
            mse__owner__assigned_agent=request.user.assigned_agent
        ).select_related('mse', 'mse__owner', 'customer', 'supplier', 'product')
        
        # Apply filters
        transaction_type = request.query_params.get('transaction_type')
        if transaction_type:
            linked_transactions = linked_transactions.filter(transaction_type=transaction_type)
        
        # Date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            linked_transactions = linked_transactions.filter(transaction_date__gte=start_date)
        if end_date:
            linked_transactions = linked_transactions.filter(transaction_date__lte=end_date)
        
        # Search
        search = request.query_params.get('search')
        if search:
            linked_transactions = linked_transactions.filter(
                description__icontains=search
            )
        
        total_count = linked_transactions.count()
        transactions = linked_transactions[start:end]
        
        transaction_data = []
        for transaction in transactions:
            transaction_data.append({
                'id': transaction.id,
                'transaction_type': transaction.transaction_type,
                'amount': transaction.amount,
                'currency': transaction.currency,
                'quantity': transaction.quantity,
                'description': transaction.description,
                'reference_number': transaction.reference_number,
                'transaction_date': transaction.transaction_date,
                'mse_name': transaction.mse.full_name,
                'mse_owner': f"{transaction.mse.owner.first_name} {transaction.mse.owner.last_name}",
                'customer_name': transaction.customer.name if transaction.customer else None,
                'supplier_name': transaction.supplier.name if transaction.supplier else None,
                'product_name': transaction.product.name if transaction.product else None
            })
        
        return Response({
            'transactions': transaction_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        })


class PartnerReportViewSet(viewsets.ViewSet):
    """Partner reports and analytics"""
    
    permission_classes = [IsPartner, CanViewReports]
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Get partner dashboard summary"""
        
        # MSE statistics
        linked_mses = MSE.objects.filter(owner__assigned_agent=request.user.assigned_agent)
        mse_stats = {
            'total_linked_mse': linked_mses.count(),
            'approved_mse': linked_mses.filter(status='approved').count(),
            'pending_mse': linked_mses.filter(status='pending').count(),
            'rejected_mse': linked_mses.filter(status='rejected').count(),
        }
        
        # Financial statistics
        linked_wallets = Wallet.objects.filter(mse__owner__assigned_agent=request.user.assigned_agent)
        financial_stats = {
            'total_wallet_balance': linked_wallets.aggregate(
                total=Sum('balance')
            )['total'] or 0,
            'total_wallets': linked_wallets.count(),
            'active_wallets': linked_wallets.filter(is_active=True).count(),
        }
        
        # Transaction statistics
        linked_transactions = Transaction.objects.filter(
            mse__owner__assigned_agent=request.user.assigned_agent
        )
        transaction_stats = {
            'total_transactions': linked_transactions.count(),
            'total_amount': linked_transactions.aggregate(
                total=Sum('amount')
            )['total'] or 0,
        }
        
        # Customer and supplier statistics
        customer_stats = {
            'total_customers': Customer.objects.filter(
                mse__owner__assigned_agent=request.user.assigned_agent
            ).count(),
        }
        
        supplier_stats = {
            'total_suppliers': Supplier.objects.filter(
                mse__owner__assigned_agent=request.user.assigned_agent
            ).count(),
        }
        
        return Response({
            'partner_info': {
                'institution': request.user.partner_institution,
                'assigned_agent': request.user.assigned_agent.first_name if request.user.assigned_agent else None
            },
            'mse_statistics': mse_stats,
            'financial_statistics': financial_stats,
            'transaction_statistics': transaction_stats,
            'customer_statistics': customer_stats,
            'supplier_statistics': supplier_stats,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def mse_performance_report(self, request):
        """Get MSE performance report for partner-linked MSEs"""
        
        # Date range filtering
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        linked_mses = MSE.objects.filter(owner__assigned_agent=request.user.assigned_agent)
        
        # MSE registration trends
        mse_registrations = linked_mses.filter(
            created_at__gte=start_date
        ).extra(
            select={'date': 'date(created_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        # Category distribution
        category_distribution = linked_mses.values('category__name').annotate(
            count=Count('id')
        )
        
        # Status distribution
        status_distribution = linked_mses.values('status').annotate(
            count=Count('id')
        )
        
        # Location distribution
        location_distribution = linked_mses.values('location').annotate(
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
    def financial_summary_report(self, request):
        """Get financial summary report for partner-linked MSEs"""
        
        # Date range filtering
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        linked_transactions = Transaction.objects.filter(
            mse__owner__assigned_agent=request.user.assigned_agent,
            transaction_date__gte=start_date
        )
        
        # Transaction statistics
        transaction_stats = {
            'total_transactions': linked_transactions.count(),
            'total_amount': linked_transactions.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'by_type': linked_transactions.values('transaction_type').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
        }
        
        # Wallet statistics
        linked_wallets = Wallet.objects.filter(mse__owner__assigned_agent=request.user.assigned_agent)
        wallet_stats = {
            'total_balance': linked_wallets.aggregate(
                total=Sum('balance')
            )['total'] or 0,
            'active_wallets': linked_wallets.filter(is_active=True).count(),
            'total_wallets': linked_wallets.count(),
        }
        
        # Top performing MSEs by transaction volume
        top_mse_by_volume = linked_transactions.values('mse__first_name', 'mse__last_name').annotate(
            transaction_count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')[:10]
        
        return Response({
            'period': f'Last {days} days',
            'transaction_statistics': transaction_stats,
            'wallet_statistics': wallet_stats,
            'top_mse_by_volume': top_mse_by_volume,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """Export partner data"""
        
        if not request.user.can_export_data:
            return Response({
                'error': 'You do not have permission to export data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # This would implement actual data export functionality
        return Response({
            'message': 'Data export functionality will be implemented here',
            'available_formats': ['csv', 'excel', 'pdf']
        })
