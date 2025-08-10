from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

from mses.models import MSE
from markets.models import BusinessTransaction, Product


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def income_report(request):
    """Generate income report"""
    user_mses = MSE.objects.filter(user=request.user)
    transactions = BusinessTransaction.objects.filter(
        mse__in=user_mses,
        transaction_type__in=['sale', 'income'],
        status='completed'
    )
    
    # Calculate income by period
    period = request.GET.get('period', 'month')
    if period == 'week':
        transactions = transactions.filter(
            transaction_date__gte=timezone.now() - timedelta(days=7)
        )
    elif period == 'month':
        transactions = transactions.filter(
            transaction_date__gte=timezone.now() - timedelta(days=30)
        )
    elif period == 'year':
        transactions = transactions.filter(
            transaction_date__gte=timezone.now() - timedelta(days=365)
        )
    
    total_income = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    
    data = {
        'period': period,
        'total_income': total_income,
        'transaction_count': transactions.count(),
        'transactions': list(transactions.values('id', 'amount', 'currency', 'description', 'transaction_date'))
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_report(request):
    """Generate stock report"""
    user_mses = MSE.objects.filter(user=request.user)
    products = Product.objects.filter(mse__in=user_mses, is_active=True)
    
    stock_data = []
    for product in products:
        stock_data.append({
            'product_name': product.name,
            'current_stock': product.stock_quantity,
            'unit_price': product.unit_price,
            'total_value': product.stock_quantity * product.unit_price,
            'unit': product.unit
        })
    
    total_stock_value = sum(item['total_value'] for item in stock_data)
    
    data = {
        'total_products': products.count(),
        'total_stock_value': total_stock_value,
        'stock_items': stock_data
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def purchases_report(request):
    """Generate purchases report"""
    user_mses = MSE.objects.filter(user=request.user)
    transactions = BusinessTransaction.objects.filter(
        mse__in=user_mses,
        transaction_type='purchase',
        status='completed'
    )
    
    period = request.GET.get('period', 'month')
    if period == 'week':
        transactions = transactions.filter(
            transaction_date__gte=timezone.now() - timedelta(days=7)
        )
    elif period == 'month':
        transactions = transactions.filter(
            transaction_date__gte=timezone.now() - timedelta(days=30)
        )
    elif period == 'year':
        transactions = transactions.filter(
            transaction_date__gte=timezone.now() - timedelta(days=365)
        )
    
    total_purchases = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    
    data = {
        'period': period,
        'total_purchases': total_purchases,
        'transaction_count': transactions.count(),
        'transactions': list(transactions.values('id', 'amount', 'currency', 'description', 'transaction_date'))
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report(request):
    """Generate sales report"""
    user_mses = MSE.objects.filter(user=request.user)
    transactions = BusinessTransaction.objects.filter(
        mse__in=user_mses,
        transaction_type='sale',
        status='completed'
    )
    
    period = request.GET.get('period', 'month')
    if period == 'week':
        transactions = transactions.filter(
            transaction_date__gte=timezone.now() - timedelta(days=7)
        )
    elif period == 'month':
        transactions = transactions.filter(
            transaction_date__gte=timezone.now() - timedelta(days=30)
        )
    elif period == 'year':
        transactions = transactions.filter(
            transaction_date__gte=timezone.now() - timedelta(days=365)
        )
    
    total_sales = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    
    data = {
        'period': period,
        'total_sales': total_sales,
        'transaction_count': transactions.count(),
        'transactions': list(transactions.values('id', 'amount', 'currency', 'description', 'transaction_date'))
    }
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics_report(request):
    """Generate comprehensive analytics report"""
    user_mses = MSE.objects.filter(user=request.user)
    
    # Business summary
    total_mse = user_mses.count()
    total_transactions = BusinessTransaction.objects.filter(mse__in=user_mses).count()
    total_customers = user_mses.aggregate(Count('customers'))['customers__count'] or 0
    total_products = Product.objects.filter(mse__in=user_mses).count()
    
    # Financial summary
    income_transactions = BusinessTransaction.objects.filter(
        mse__in=user_mses,
        transaction_type__in=['sale', 'income'],
        status='completed'
    )
    expense_transactions = BusinessTransaction.objects.filter(
        mse__in=user_mses,
        transaction_type__in=['purchase', 'expense'],
        status='completed'
    )
    
    total_revenue = income_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = expense_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    net_profit = total_revenue - total_expenses
    
    # Market analytics
    market_data = []
    for market_type in ['input', 'output']:
        market_transactions = BusinessTransaction.objects.filter(
            mse__in=user_mses,
            status='completed'
        )
        if market_type == 'input':
            market_transactions = market_transactions.filter(transaction_type='purchase')
        else:
            market_transactions = market_transactions.filter(transaction_type='sale')
        
        transaction_count = market_transactions.count()
        total_amount = market_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        percentage = (total_amount / total_revenue * 100) if total_revenue > 0 else 0
        
        market_data.append({
            'market_type': market_type,
            'transaction_count': transaction_count,
            'total_amount': total_amount,
            'percentage': round(percentage, 2)
        })
    
    data = {
        'business_summary': {
            'total_mse': total_mse,
            'total_transactions': total_transactions,
            'total_customers': total_customers,
            'total_products': total_products
        },
        'financial_summary': {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_profit': net_profit
        },
        'market_analytics': market_data
    }
    
    return Response(data)
