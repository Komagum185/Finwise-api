from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

from mses.models import MSE, Wallet
from markets.models import BusinessTransaction, Product, Customer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_overview(request):
    """Get dashboard overview data"""
    user_mses = MSE.objects.filter(user=request.user)
    
    # Recent transactions
    recent_transactions = BusinessTransaction.objects.filter(
        mse__in=user_mses
    ).order_by('-transaction_date')[:10]
    
    # Quick stats
    total_wallets = Wallet.objects.filter(mse__in=user_mses).count()
    total_customers = Customer.objects.filter(mse__in=user_mses).count()
    total_products = Product.objects.filter(mse__in=user_mses).count()
    
    # Recent activity
    recent_activity = []
    for transaction in recent_transactions:
        recent_activity.append({
            'type': 'transaction',
            'title': f"{transaction.get_transaction_type_display()} - {transaction.amount} {transaction.currency}",
            'description': transaction.description,
            'date': transaction.transaction_date,
            'mse': transaction.mse.name
        })
    
    data = {
        'quick_stats': {
            'total_mse': user_mses.count(),
            'total_wallets': total_wallets,
            'total_customers': total_customers,
            'total_products': total_products
        },
        'recent_transactions': list(recent_transactions.values(
            'id', 'transaction_type', 'amount', 'currency', 'description', 'transaction_date', 'status'
        )),
        'recent_activity': recent_activity
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    user_mses = MSE.objects.filter(user=request.user)
    
    # Monthly stats
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    monthly_income = BusinessTransaction.objects.filter(
        mse__in=user_mses,
        transaction_type__in=['sale', 'income'],
        status='completed',
        transaction_date__month=current_month,
        transaction_date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    monthly_expenses = BusinessTransaction.objects.filter(
        mse__in=user_mses,
        transaction_type__in=['purchase', 'expense'],
        status='completed',
        transaction_date__month=current_month,
        transaction_date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    monthly_profit = monthly_income - monthly_expenses
    
    # Growth stats (compare with previous month)
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1
    
    prev_monthly_income = BusinessTransaction.objects.filter(
        mse__in=user_mses,
        transaction_type__in=['sale', 'income'],
        status='completed',
        transaction_date__month=prev_month,
        transaction_date__year=prev_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    income_growth = ((monthly_income - prev_monthly_income) / prev_monthly_income * 100) if prev_monthly_income > 0 else 0
    
    data = {
        'current_month': {
            'income': monthly_income,
            'expenses': monthly_expenses,
            'profit': monthly_profit
        },
        'growth': {
            'income_growth': round(income_growth, 2)
        },
        'summary': {
            'total_transactions': BusinessTransaction.objects.filter(mse__in=user_mses).count(),
            'active_mse': user_mses.filter(status='active').count()
        }
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_charts(request):
    """Get dashboard chart data"""
    user_mses = MSE.objects.filter(user=request.user)
    
    # Monthly trend data (last 6 months)
    chart_data = []
    for i in range(6):
        month = timezone.now().month - i
        year = timezone.now().year
        if month <= 0:
            month += 12
            year -= 1
        
        monthly_income = BusinessTransaction.objects.filter(
            mse__in=user_mses,
            transaction_type__in=['sale', 'income'],
            status='completed',
            transaction_date__month=month,
            transaction_date__year=year
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        monthly_expenses = BusinessTransaction.objects.filter(
            mse__in=user_mses,
            transaction_type__in=['purchase', 'expense'],
            status='completed',
            transaction_date__month=month,
            transaction_date__year=year
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        chart_data.append({
            'month': f"{year}-{month:02d}",
            'income': monthly_income,
            'expenses': monthly_expenses,
            'profit': monthly_income - monthly_expenses
        })
    
    # Transaction type distribution
    transaction_types = BusinessTransaction.objects.filter(
        mse__in=user_mses,
        status='completed'
    ).values('transaction_type').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    data = {
        'monthly_trends': list(reversed(chart_data)),
        'transaction_distribution': list(transaction_types)
    }
    
    return Response(data)
