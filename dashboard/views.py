from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
import json

# Import models
from wallet.models import EnhancedWallet, EnhancedWalletTransaction, Transaction, Budget, Goal
from mses.models import MSE, InputMSE, OutputMSE, ProductionMSE
from markets.models import BusinessTransaction, Customer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Get comprehensive dashboard statistics"""
    try:
        user = request.user
        
        # Get current date and month start
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Wallet Statistics
        wallets = EnhancedWallet.objects.filter(mse_id__in=MSE.objects.filter(user=user).values_list('id', flat=True))
        total_balance = wallets.aggregate(total=Sum('balance'))['total'] or 0
        active_wallets = wallets.filter(status='Active').count()
        total_wallets = wallets.count()
        
        # Transaction Statistics
        transactions = EnhancedWalletTransaction.objects.filter(
            wallet__in=wallets,
            created_at__gte=month_start
        )
        monthly_volume = transactions.aggregate(total=Sum('amount'))['total'] or 0
        monthly_transactions = transactions.count()
        
        # MSE Statistics
        mses = MSE.objects.filter(user=user)
        total_mses = mses.count()
        active_mses = mses.filter(status='active').count()
        
        # Business Transaction Statistics
        business_transactions = BusinessTransaction.objects.filter(
            mse__user=user,
            created_at__gte=month_start
        )
        monthly_business_volume = business_transactions.aggregate(total=Sum('amount'))['total'] or 0
        monthly_business_transactions = business_transactions.count()
        
        # Customer Statistics
        customers = Customer.objects.filter(mse__user=user)
        total_customers = customers.count()
        active_customers = customers.filter(status='active').count()
        
        # Budget Statistics
        budgets = Budget.objects.filter(user=user, status='active')
        total_budget = budgets.aggregate(total=Sum('total_amount'))['total'] or 0
        spent_budget = budgets.aggregate(total=Sum('spent_amount'))['total'] or 0
        budget_utilization = (spent_budget / total_budget * 100) if total_budget > 0 else 0
        
        # Goal Statistics
        goals = Goal.objects.filter(user=user, status='active')
        total_goal_target = goals.aggregate(total=Sum('target_amount'))['total'] or 0
        current_goal_amount = goals.aggregate(total=Sum('current_amount'))['total'] or 0
        goal_progress = (current_goal_amount / total_goal_target * 100) if total_goal_target > 0 else 0
        
        stats = {
            'wallets': {
                'total_balance': float(total_balance),
                'active_wallets': active_wallets,
                'total_wallets': total_wallets,
                'currency': 'USD'
            },
            'transactions': {
                'monthly_volume': float(monthly_volume),
                'monthly_count': monthly_transactions,
                'currency': 'USD'
            },
            'mses': {
                'total': total_mses,
                'active': active_mses
            },
            'business': {
                'monthly_volume': float(monthly_business_volume),
                'monthly_transactions': monthly_business_transactions,
                'currency': 'USD'
            },
            'customers': {
                'total': total_customers,
                'active': active_customers
            },
            'budgets': {
                'total_budget': float(total_budget),
                'spent_amount': float(spent_budget),
                'utilization_percentage': round(budget_utilization, 2),
                'currency': 'USD'
            },
            'goals': {
                'total_target': float(total_goal_target),
                'current_amount': float(current_goal_amount),
                'progress_percentage': round(goal_progress, 2),
                'currency': 'USD'
            },
            'summary': {
                'total_assets': float(total_balance),
                'monthly_activity': monthly_transactions + monthly_business_transactions,
                'active_entities': active_wallets + active_mses + active_customers
            }
        }
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Failed to fetch dashboard statistics'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_charts(request):
    """Get chart data for dashboard visualizations"""
    try:
        user = request.user
        
        # Get date range (last 12 months)
        now = timezone.now()
        months_data = []
        
        for i in range(12):
            month_date = now - timedelta(days=30*i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                month_end = now
            else:
                month_end = month_start + timedelta(days=32)
                month_end = month_end.replace(day=1) - timedelta(days=1)
            
            # Get wallets for this user
            wallets = EnhancedWallet.objects.filter(mse_id__in=MSE.objects.filter(user=user).values_list('id', flat=True))
            
            # Monthly transaction data
            monthly_transactions = EnhancedWalletTransaction.objects.filter(
                wallet__in=wallets,
                created_at__gte=month_start,
                created_at__lte=month_end
            )
            
            monthly_volume = monthly_transactions.aggregate(total=Sum('amount'))['total'] or 0
            transaction_count = monthly_transactions.count()
            
            # Business transaction data
            monthly_business = BusinessTransaction.objects.filter(
                mse__user=user,
                created_at__gte=month_start,
                created_at__lte=month_end
            )
            
            business_volume = monthly_business.aggregate(total=Sum('amount'))['total'] or 0
            business_count = monthly_business.count()
            
            months_data.append({
                'month': month_start.strftime('%Y-%m'),
                'month_name': month_start.strftime('%B %Y'),
                'wallet_volume': float(monthly_volume),
                'wallet_transactions': transaction_count,
                'business_volume': float(business_volume),
                'business_transactions': business_count,
                'total_volume': float(monthly_volume + business_volume),
                'total_transactions': transaction_count + business_count
            })
        
        # Transaction type distribution (last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        recent_transactions = EnhancedWalletTransaction.objects.filter(
            wallet__in=wallets,
            created_at__gte=thirty_days_ago
        )
        
        transaction_types = recent_transactions.values('type').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        type_distribution = []
        for tx_type in transaction_types:
            type_distribution.append({
                'type': tx_type['type'],
                'count': tx_type['count'],
                'amount': float(tx_type['total_amount'] or 0),
                'percentage': round((tx_type['count'] / recent_transactions.count()) * 100, 2) if recent_transactions.count() > 0 else 0
            })
        
        # Wallet balance distribution
        wallet_balances = []
        for wallet in wallets:
            wallet_balances.append({
                'wallet_name': wallet.mse_name,
                'account_type': wallet.account_type,
                'balance': float(wallet.balance),
                'currency': wallet.currency,
                'status': wallet.status
            })
        
        # Category distribution for transactions
        category_transactions = recent_transactions.values('category').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        category_distribution = []
        for cat in category_transactions:
            if cat['category']:  # Only include transactions with categories
                category_distribution.append({
                    'category': cat['category'],
                    'count': cat['count'],
                    'amount': float(cat['total_amount'] or 0),
                    'percentage': round((cat['count'] / recent_transactions.count()) * 100, 2) if recent_transactions.count() > 0 else 0
                })
        
        # Recent activity (last 10 transactions)
        recent_activity = []
        for tx in recent_transactions.order_by('-created_at')[:10]:
            recent_activity.append({
                'id': tx.id,
                'type': tx.type,
                'amount': float(tx.amount),
                'description': tx.description,
                'wallet_name': tx.wallet.mse_name,
                'date': tx.created_at.isoformat(),
                'status': tx.status
            })
        
        charts_data = {
            'monthly_trends': months_data,
            'transaction_types': type_distribution,
            'wallet_balances': wallet_balances,
            'category_distribution': category_distribution,
            'recent_activity': recent_activity,
            'summary': {
                'total_months': len(months_data),
                'total_transaction_types': len(type_distribution),
                'total_wallets': len(wallet_balances),
                'total_categories': len(category_distribution)
            }
        }
        
        return Response(charts_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Failed to fetch chart data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_overview(request):
    """Get dashboard overview data"""
    try:
        user = request.user
        
        # Quick stats
        wallets = EnhancedWallet.objects.filter(mse_id__in=MSE.objects.filter(user=user).values_list('id', flat=True))
        mses = MSE.objects.filter(user=user)
        
        overview = {
            'total_balance': float(wallets.aggregate(total=Sum('balance'))['total'] or 0),
            'active_wallets': wallets.filter(status='Active').count(),
            'total_mses': mses.count(),
            'active_mses': mses.filter(status='active').count(),
            'currency': 'USD',
            'last_updated': timezone.now().isoformat()
        }
        
        return Response(overview, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Failed to fetch overview data'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def dashboard_home(request):
    """Basic dashboard home view"""
    return JsonResponse({
        'message': 'Dashboard module is available',
        'status': 'success',
        'endpoints': {
            'stats': '/api/dashboard/stats/',
            'charts': '/api/dashboard/charts/',
            'overview': '/api/dashboard/overview/'
        }
    })
