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
from partner_dashboard.permissions import IsMSE, MSEAccessPermission
from partner_dashboard.permissions import CanViewReports, CanExportData


class MSEWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """MSE access to their own wallet"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsMSE]
    
    def get_queryset(self):
        """Only show the MSE's own wallet"""
        return Wallet.objects.filter(mse__owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get wallet summary"""
        try:
            wallet = Wallet.objects.get(mse__owner=request.user)
            
            # Recent transactions
            recent_transactions = wallet.transactions.all().order_by('-created_at')[:10]
            
            transaction_data = []
            for transaction in recent_transactions:
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
                'balance': wallet.balance,
                'currency': wallet.currency,
                'account_number': wallet.account_number,
                'is_active': wallet.is_active,
                'last_transaction_date': wallet.last_transaction_date,
                'recent_transactions': transaction_data
            })
        except Wallet.DoesNotExist:
            return Response({
                'error': 'Wallet not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get all wallet transactions"""
        try:
            wallet = Wallet.objects.get(mse__owner=request.user)
            
            # Pagination
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size
            
            transactions = wallet.transactions.all().order_by('-created_at')[start:end]
            
            transaction_data = []
            for transaction in transactions:
                transaction_data.append({
                    'id': transaction.id,
                    'type': transaction.transaction_type,
                    'amount': transaction.amount,
                    'currency': transaction.currency,
                    'status': transaction.status,
                    'created_at': transaction.created_at,
                    'description': transaction.description,
                    'reference_number': transaction.reference_number
                })
            
            total_transactions = wallet.transactions.count()
            
            return Response({
                'transactions': transaction_data,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total_transactions,
                    'total_pages': (total_transactions + page_size - 1) // page_size
                }
            })
        except Wallet.DoesNotExist:
            return Response({
                'error': 'Wallet not found'
            }, status=status.HTTP_404_NOT_FOUND)


class MSELoanViewSet(viewsets.ReadOnlyModelViewSet):
    """MSE access to their own loans"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsMSE]
    
    def get_queryset(self):
        """Only show the MSE's own loans"""
        return GroupLoan.objects.filter(mse__owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get loan summary"""
        loans = GroupLoan.objects.filter(mse__owner=request.user)
        
        total_loans = loans.count()
        active_loans = loans.filter(status='active').count()
        completed_loans = loans.filter(status='completed').count()
        pending_loans = loans.filter(status='pending').count()
        
        total_borrowed = loans.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_outstanding = loans.filter(status='active').aggregate(
            total=Sum('outstanding_balance')
        )['total'] or 0
        
        return Response({
            'total_loans': total_loans,
            'active_loans': active_loans,
            'completed_loans': completed_loans,
            'pending_loans': pending_loans,
            'total_borrowed': total_borrowed,
            'total_outstanding': total_outstanding
        })
    
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """Get detailed loan information"""
        loan = self.get_object()
        
        # Get repayments
        repayments = loan.repayments.all().order_by('-payment_date')
        
        repayment_data = []
        for repayment in repayments:
            repayment_data.append({
                'id': repayment.id,
                'amount': repayment.amount,
                'type': repayment.repayment_type,
                'payment_method': repayment.payment_method,
                'payment_date': repayment.payment_date,
                'is_confirmed': repayment.is_confirmed,
                'reference_number': repayment.reference_number
            })
        
        return Response({
            'loan_id': loan.id,
            'amount': loan.amount,
            'term_months': loan.term_months,
            'interest_rate': loan.interest_rate,
            'status': loan.status,
            'purpose': loan.purpose,
            'created_at': loan.created_at,
            'approval_date': loan.approval_date,
            'disbursement_date': loan.disbursement_date,
            'monthly_payment': loan.monthly_payment,
            'outstanding_balance': loan.outstanding_balance,
            'repayments': repayment_data
        })


class MSECustomerViewSet(viewsets.ModelViewSet):
    """MSE management of their own customers"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsMSE]
    
    def get_queryset(self):
        """Only show the MSE's own customers"""
        return Customer.objects.filter(mse__owner=self.request.user)
    
    def get_queryset(self):
        queryset = Customer.objects.filter(mse__owner=self.request.user)
        
        # Filter by customer type
        customer_type = self.request.query_params.get('customer_type')
        if customer_type:
            queryset = queryset.filter(customer_type=customer_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
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
        """Get customer statistics"""
        customers = Customer.objects.filter(mse__owner=request.user)
        
        total_customers = customers.count()
        active_customers = customers.filter(is_active=True).count()
        
        type_counts = customers.values('customer_type').annotate(
            count=Count('id')
        )
        
        total_credit_limit = customers.aggregate(
            total=Sum('credit_limit')
        )['total'] or 0
        
        total_current_balance = customers.aggregate(
            total=Sum('current_balance')
        )['total'] or 0
        
        return Response({
            'total_customers': total_customers,
            'active_customers': active_customers,
            'type_distribution': type_counts,
            'total_credit_limit': total_credit_limit,
            'total_current_balance': total_current_balance
        })


class MSESupplierViewSet(viewsets.ModelViewSet):
    """MSE management of their own suppliers"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsMSE]
    
    def get_queryset(self):
        """Only show the MSE's own suppliers"""
        return Supplier.objects.filter(mse__owner=self.request.user)
    
    def get_queryset(self):
        queryset = Supplier.objects.filter(mse__owner=self.request.user)
        
        # Filter by supplier type
        supplier_type = self.request.query_params.get('supplier_type')
        if supplier_type:
            queryset = queryset.filter(supplier_type=supplier_type)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
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
        """Get supplier statistics"""
        suppliers = Supplier.objects.filter(mse__owner=request.user)
        
        total_suppliers = suppliers.count()
        active_suppliers = suppliers.filter(is_active=True).count()
        
        type_counts = suppliers.values('supplier_type').annotate(
            count=Count('id')
        )
        
        # Average rating
        avg_rating = suppliers.aggregate(
            avg_rating=Sum('rating') / Count('id')
        )['avg_rating'] or 0
        
        return Response({
            'total_suppliers': total_suppliers,
            'active_suppliers': active_suppliers,
            'type_distribution': type_counts,
            'average_rating': round(avg_rating, 2)
        })


class MSETransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """MSE access to their own transactions"""
    
    serializer_class = None  # Will be set based on action
    permission_classes = [IsMSE]
    
    def get_queryset(self):
        """Only show the MSE's own transactions"""
        return Transaction.objects.filter(mse__owner=self.request.user)
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(mse__owner=self.request.user)
        
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
        
        # Search by description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(description__icontains=search)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary"""
        transactions = Transaction.objects.filter(mse__owner=request.user)
        
        total_transactions = transactions.count()
        total_amount = transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        type_counts = transactions.values('transaction_type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Recent transactions
        recent_transactions = transactions.order_by('-transaction_date')[:5]
        
        recent_data = []
        for transaction in recent_transactions:
            recent_data.append({
                'id': transaction.id,
                'type': transaction.transaction_type,
                'amount': transaction.amount,
                'currency': transaction.currency,
                'date': transaction.transaction_date,
                'description': transaction.description
            })
        
        return Response({
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'type_distribution': type_counts,
            'recent_transactions': recent_data
        })


class MSEReportViewSet(viewsets.ViewSet):
    """MSE reports and analytics"""
    
    permission_classes = [IsMSE, CanViewReports]
    
    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Get dashboard summary"""
        
        # Get MSE data
        try:
            mse = MSE.objects.get(owner=request.user)
            wallet = Wallet.objects.get(mse=mse)
        except (MSE.DoesNotExist, Wallet.DoesNotExist):
            return Response({
                'error': 'MSE or wallet not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Financial summary
        financial_summary = {
            'wallet_balance': wallet.balance,
            'total_transactions': Transaction.objects.filter(mse=mse).count(),
            'total_loans': GroupLoan.objects.filter(mse=mse).count(),
            'active_loans': GroupLoan.objects.filter(mse=mse, status='active').count(),
        }
        
        # Customer summary
        customer_summary = {
            'total_customers': Customer.objects.filter(mse=mse).count(),
            'active_customers': Customer.objects.filter(mse=mse, is_active=True).count(),
            'total_credit_limit': Customer.objects.filter(mse=mse).aggregate(
                total=Sum('credit_limit')
            )['total'] or 0,
        }
        
        # Supplier summary
        supplier_summary = {
            'total_suppliers': Supplier.objects.filter(mse=mse).count(),
            'active_suppliers': Supplier.objects.filter(mse=mse, is_active=True).count(),
        }
        
        # Recent activity
        recent_activity = {
            'transactions_this_month': Transaction.objects.filter(
                mse=mse,
                transaction_date__gte=timezone.now().replace(day=1)
            ).count(),
            'new_customers_this_month': Customer.objects.filter(
                mse=mse,
                created_at__gte=timezone.now().replace(day=1)
            ).count(),
            'new_suppliers_this_month': Supplier.objects.filter(
                mse=mse,
                created_at__gte=timezone.now().replace(day=1)
            ).count(),
        }
        
        return Response({
            'mse_info': {
                'name': mse.full_name,
                'business_name': mse.business_name,
                'category': mse.category.name,
                'location': mse.location,
                'status': mse.status
            },
            'financial_summary': financial_summary,
            'customer_summary': customer_summary,
            'supplier_summary': supplier_summary,
            'recent_activity': recent_activity,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def income_report(self, request):
        """Get income report"""
        
        # Date range filtering
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        mse = MSE.objects.get(owner=request.user)
        
        # Sales transactions
        sales_transactions = Transaction.objects.filter(
            mse=mse,
            transaction_type='sale',
            transaction_date__gte=start_date
        )
        
        total_sales = sales_transactions.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        sales_by_date = sales_transactions.extra(
            select={'date': 'date(transaction_date)'}
        ).values('date').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('date')
        
        # Top selling products
        top_products = sales_transactions.values('product__name').annotate(
            total_sales=Sum('amount'),
            total_quantity=Sum('quantity')
        ).order_by('-total_sales')[:10]
        
        return Response({
            'period': f'Last {days} days',
            'total_sales': total_sales,
            'sales_by_date': sales_by_date,
            'top_products': top_products,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def stock_report(self, request):
        """Get stock/inventory report"""
        
        mse = MSE.objects.get(owner=request.user)
        
        # Product inventory
        products = Product.objects.filter(mse=mse)
        
        total_products = products.count()
        total_stock_value = products.aggregate(
            total=Sum('unit_price' * 'stock_quantity')
        )['total'] or 0
        
        low_stock_products = products.filter(stock_quantity__lt=10).values(
            'name', 'stock_quantity', 'unit_price'
        )
        
        product_categories = products.values('category').annotate(
            count=Count('id'),
            total_stock=Sum('stock_quantity')
        )
        
        return Response({
            'total_products': total_products,
            'total_stock_value': total_stock_value,
            'low_stock_products': low_stock_products,
            'product_categories': product_categories,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def loan_report(self, request):
        """Get loan report"""
        
        mse = MSE.objects.get(owner=request.user)
        
        # Loan summary
        loans = GroupLoan.objects.filter(mse=mse)
        
        total_loans = loans.count()
        active_loans = loans.filter(status='active').count()
        total_borrowed = loans.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_outstanding = loans.filter(status='active').aggregate(
            total=Sum('outstanding_balance')
        )['total'] or 0
        
        # Loan status distribution
        status_distribution = loans.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Recent repayments
        recent_repayments = GroupLoanRepayment.objects.filter(
            loan__mse=mse
        ).order_by('-payment_date')[:10]
        
        repayment_data = []
        for repayment in recent_repayments:
            repayment_data.append({
                'loan_amount': repayment.loan.amount,
                'repayment_amount': repayment.amount,
                'type': repayment.repayment_type,
                'date': repayment.payment_date,
                'status': 'Confirmed' if repayment.is_confirmed else 'Pending'
            })
        
        return Response({
            'total_loans': total_loans,
            'active_loans': active_loans,
            'total_borrowed': total_borrowed,
            'total_outstanding': total_outstanding,
            'status_distribution': status_distribution,
            'recent_repayments': repayment_data,
            'generated_at': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """Export MSE data"""
        
        if not request.user.can_export_data:
            return Response({
                'error': 'You do not have permission to export data'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # This would implement actual data export functionality
        return Response({
            'message': 'Data export functionality will be implemented here',
            'available_formats': ['csv', 'excel', 'pdf']
        })
