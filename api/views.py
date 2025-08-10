from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta, date
from decimal import Decimal
import calendar

from .models import (
    Category, Budget, Goal, Transaction, UserProfile, RecurringTransaction
)
from .serializers import (
    CategorySerializer, BudgetSerializer, GoalSerializer, TransactionSerializer,
    UserProfileSerializer, RecurringTransactionSerializer,
    FinancialSummarySerializer, CategoryBreakdownSerializer, BudgetStatusSerializer,
    GoalProgressSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """Category management with filtering and analytics"""
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        return Category.objects.all()
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for a specific category"""
        category = self.get_object()
        transactions = Transaction.objects.filter(
            user=request.user,
            category=category
        ).order_by('-date')
        
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics for a specific category"""
        category = self.get_object()
        user = request.user
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date and end_date:
            transactions = Transaction.objects.filter(
                user=user,
                category=category,
                date__range=[start_date, end_date]
            )
        else:
            # Default to current month
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
            transactions = Transaction.objects.filter(
                user=user,
                category=category,
                date__range=[start_date, end_date]
            )
        
        total_amount = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        transaction_count = transactions.count()
        
        # Monthly breakdown
        monthly_data = transactions.extra(
            select={'month': "EXTRACT(month FROM date)"}
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        return Response({
            'category': CategorySerializer(category).data,
            'period': {'start_date': start_date, 'end_date': end_date},
            'total_amount': total_amount,
            'transaction_count': transaction_count,
            'monthly_breakdown': monthly_data
        })


class BudgetViewSet(viewsets.ModelViewSet):
    """Budget management with automatic calculations"""
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['period', 'is_active', 'category']
    search_fields = ['category__name']
    ordering_fields = ['start_date', 'amount']
    ordering = ['-start_date']
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get budget overview for current period"""
        user = request.user
        today = timezone.now().date()
        
        # Get current month budgets
        current_month_start = today.replace(day=1)
        current_month_end = today
        
        budgets = Budget.objects.filter(
            user=user,
            start_date__lte=current_month_end,
            end_date__gte=current_month_start,
            is_active=True
        )
        
        budget_data = []
        total_budget = Decimal('0.00')
        total_spent = Decimal('0.00')
        
        for budget in budgets:
            spent = budget.spent_amount
            remaining = budget.remaining_amount
            percentage = budget.spent_percentage
            
            budget_data.append({
                'id': budget.id,
                'category': budget.category.name,
                'budget_amount': budget.amount,
                'spent_amount': spent,
                'remaining_amount': remaining,
                'spent_percentage': percentage,
                'status': 'over_budget' if spent > budget.amount else 'on_track'
            })
            
            total_budget += budget.amount
            total_spent += spent
        
        return Response({
            'budgets': budget_data,
            'summary': {
                'total_budget': total_budget,
                'total_spent': total_spent,
                'total_remaining': total_budget - total_spent,
                'overall_percentage': (total_spent / total_budget * 100) if total_budget > 0 else 0
            }
        })
    
    @action(detail=True, methods=['post'])
    def adjust_amount(self, request, pk=None):
        """Adjust budget amount"""
        budget = self.get_object()
        new_amount = request.data.get('amount')
        
        if not new_amount:
            return Response(
                {'error': 'Amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_amount = Decimal(new_amount)
            if new_amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        budget.amount = new_amount
        budget.save()
        
        return Response({
            'message': 'Budget amount updated successfully',
            'budget': BudgetSerializer(budget).data
        })


class GoalViewSet(viewsets.ModelViewSet):
    """Goal management with progress tracking"""
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['goal_type', 'status', 'priority']
    search_fields = ['name', 'description']
    ordering_fields = ['target_date', 'priority', 'created_at']
    ordering = ['-priority', '-created_at']
    
    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update goal progress"""
        goal = self.get_object()
        amount = request.data.get('amount')
        
        if not amount:
            return Response(
                {'error': 'Amount is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = Decimal(amount)
            if amount < 0:
                raise ValueError("Amount cannot be negative")
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update current amount
        goal.current_amount += amount
        
        # Check if goal is completed
        if goal.current_amount >= goal.target_amount:
            goal.status = 'completed'
            goal.current_amount = goal.target_amount  # Cap at target amount
        
        goal.save()
        
        return Response({
            'message': 'Goal progress updated successfully',
            'goal': GoalSerializer(goal).data,
            'progress_percentage': goal.progress_percentage,
            'remaining_amount': goal.remaining_amount,
            'is_completed': goal.is_completed
        })
    
    @action(detail=False, methods=['get'])
    def progress_summary(self, request):
        """Get summary of all goals progress"""
        goals = self.get_queryset()
        
        total_goals = goals.count()
        completed_goals = goals.filter(status='completed').count()
        active_goals = goals.filter(status='active').count()
        
        total_target = goals.aggregate(total=Sum('target_amount'))['total'] or Decimal('0.00')
        total_current = goals.aggregate(total=Sum('current_amount'))['total'] or Decimal('0.00')
        total_remaining = total_target - total_current
        
        # Goals by priority
        high_priority = goals.filter(priority__in=[1, 2]).count()
        medium_priority = goals.filter(priority=3).count()
        low_priority = goals.filter(priority__in=[4, 5]).count()
        
        return Response({
            'summary': {
                'total_goals': total_goals,
                'completed_goals': completed_goals,
                'active_goals': active_goals,
                'completion_rate': (completed_goals / total_goals * 100) if total_goals > 0 else 0
            },
            'financial': {
                'total_target': total_target,
                'total_current': total_current,
                'total_remaining': total_remaining,
                'overall_progress': (total_current / total_target * 100) if total_target > 0 else 0
            },
            'priorities': {
                'high': high_priority,
                'medium': medium_priority,
                'low': low_priority
            }
        })


class TransactionViewSet(viewsets.ModelViewSet):
    """Enhanced transaction management with filtering and analytics"""
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'category', 'status', 'date']
    search_fields = ['description', 'notes', 'location']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date', '-created_at']
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get transaction summary for specified period"""
        user = request.user
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date and end_date:
            transactions = Transaction.objects.filter(
                user=user,
                date__range=[start_date, end_date]
            )
        else:
            # Default to current month
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
            transactions = Transaction.objects.filter(
                user=user,
                date__range=[start_date, end_date]
            )
        
        # Calculate totals
        income = transactions.filter(transaction_type='income').aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')
        expenses = transactions.filter(transaction_type='expense').aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')
        transfers = transactions.filter(transaction_type='transfer').aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')
        
        net_income = income - expenses
        
        # Category breakdown
        category_breakdown = transactions.values('category__name', 'transaction_type').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Monthly trend
        monthly_trend = transactions.extra(
            select={'month': "EXTRACT(month FROM date)"}
        ).values('month', 'transaction_type').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        return Response({
            'period': {'start_date': start_date, 'end_date': end_date},
            'summary': {
                'total_income': income,
                'total_expenses': expenses,
                'total_transfers': transfers,
                'net_income': net_income,
                'transaction_count': transactions.count()
            },
            'category_breakdown': category_breakdown,
            'monthly_trend': monthly_trend
        })
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get comprehensive transaction analytics"""
        user = request.user
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date and end_date:
            transactions = Transaction.objects.filter(
                user=user,
                date__range=[start_date, end_date]
            )
        else:
            # Default to current month
            today = timezone.now().date()
            start_date = today.replace(day=1)
            end_date = today
            transactions = Transaction.objects.filter(
                user=user,
                date__range=[start_date, end_date]
            )
        
        # Basic analytics
        total_transactions = transactions.count()
        total_amount = transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        avg_amount = transactions.aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
        
        # Transaction type distribution
        type_distribution = transactions.values('transaction_type').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        # Top categories
        top_categories = transactions.values('category__name').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-total')[:10]
        
        # Daily spending pattern
        daily_pattern = transactions.filter(transaction_type='expense').extra(
            select={'day_of_week': "EXTRACT(dow FROM date)"}
        ).values('day_of_week').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('day_of_week')
        
        return Response({
            'period': {'start_date': start_date, 'end_date': end_date},
            'overview': {
                'total_transactions': total_transactions,
                'total_amount': total_amount,
                'average_amount': avg_amount
            },
            'type_distribution': type_distribution,
            'top_categories': top_categories,
            'daily_pattern': daily_pattern
        })


class UserProfileViewSet(viewsets.ModelViewSet):
    """User profile management"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        return get_object_or_404(UserProfile, user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get user dashboard data"""
        user = request.user
        today = timezone.now().date()
        
        # Current month transactions
        month_start = today.replace(day=1)
        month_transactions = Transaction.objects.filter(
            user=user,
            date__gte=month_start
        )
        
        # Monthly totals
        monthly_income = month_transactions.filter(transaction_type='income').aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')
        monthly_expenses = month_transactions.filter(transaction_type='expense').aggregate(
            total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Recent transactions
        recent_transactions = Transaction.objects.filter(user=user).order_by('-date')[:5]
        
        # Active budgets
        active_budgets = Budget.objects.filter(
            user=user,
            start_date__lte=today,
            end_date__gte=today,
            is_active=True
        )
        
        # Active goals
        active_goals = Goal.objects.filter(
            user=user,
            status='active'
        ).order_by('-priority')[:5]
        
        return Response({
            'monthly_summary': {
                'income': monthly_income,
                'expenses': monthly_expenses,
                'net': monthly_income - monthly_expenses
            },
            'recent_transactions': TransactionSerializer(recent_transactions, many=True).data,
            'active_budgets': BudgetSerializer(active_budgets, many=True).data,
            'active_goals': GoalSerializer(active_goals, many=True).data,
            'total_balance': user.profile.total_balance if hasattr(user, 'profile') else Decimal('0.00')
        })


class RecurringTransactionViewSet(viewsets.ModelViewSet):
    """Recurring transaction management"""
    serializer_class = RecurringTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'frequency', 'is_active']
    search_fields = ['description']
    ordering_fields = ['next_due_date', 'amount']
    ordering = ['next_due_date']
    
    def get_queryset(self):
        return RecurringTransaction.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming recurring transactions"""
        today = timezone.now().date()
        upcoming = self.get_queryset().filter(
            next_due_date__gte=today,
            is_active=True
        ).order_by('next_due_date')[:10]
        
        return Response({
            'upcoming_transactions': RecurringTransactionSerializer(upcoming, many=True).data
        })
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process a recurring transaction"""
        recurring = self.get_object()
        
        # Create a new transaction
        transaction = Transaction.objects.create(
            user=request.user,
            amount=recurring.amount,
            description=recurring.description,
            transaction_type=recurring.transaction_type,
            category=recurring.category,
            date=recurring.next_due_date,
            status='completed'
        )
        
        # Update next due date
        if recurring.frequency == 'daily':
            recurring.next_due_date += timedelta(days=1)
        elif recurring.frequency == 'weekly':
            recurring.next_due_date += timedelta(weeks=1)
        elif recurring.frequency == 'monthly':
            # Add one month
            if recurring.next_due_date.month == 12:
                recurring.next_due_date = recurring.next_due_date.replace(
                    year=recurring.next_due_date.year + 1, month=1
                )
            else:
                recurring.next_due_date = recurring.next_due_date.replace(
                    month=recurring.next_due_date.month + 1
                )
        elif recurring.frequency == 'yearly':
            recurring.next_due_date = recurring.next_due_date.replace(
                year=recurring.next_due_date.year + 1
            )
        
        # Check if we've reached the end date
        if recurring.end_date and recurring.next_due_date > recurring.end_date:
            recurring.is_active = False
        
        recurring.save()
        
        return Response({
            'message': 'Recurring transaction processed successfully',
            'transaction': TransactionSerializer(transaction).data,
            'next_due_date': recurring.next_due_date
        })
