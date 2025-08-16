from django.contrib import admin
from .models import (
    Category, Budget, Goal, Transaction, UserProfile, RecurringTransaction, BusinessHealth
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'is_active', 'created_at']
    list_filter = ['category_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'period', 'start_date', 'end_date', 'is_active']
    list_filter = ['period', 'is_active', 'start_date', 'category']
    search_fields = ['user__username', 'category__name']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'goal_type', 'target_amount', 'current_amount', 'status', 'priority']
    list_filter = ['goal_type', 'status', 'priority', 'target_date']
    search_fields = ['user__username', 'name', 'description']
    date_hierarchy = 'target_date'
    ordering = ['-priority', '-created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'description', 'transaction_type', 'payment_method', 'category', 'date', 'status']
    list_filter = ['transaction_type', 'payment_method', 'category', 'status', 'date', 'user']
    search_fields = ['description', 'notes', 'reference', 'user__username', 'category__name']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'monthly_income', 'emergency_fund_target']
    list_filter = ['currency', 'created_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-created_at']


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'description', 'amount', 'transaction_type', 'frequency', 'next_due_date', 'is_active']
    list_filter = ['transaction_type', 'frequency', 'is_active', 'next_due_date']
    search_fields = ['description', 'user__username']
    date_hierarchy = 'next_due_date'
    ordering = ['next_due_date']


@admin.register(BusinessHealth)
class BusinessHealthAdmin(admin.ModelAdmin):
    list_display = ['user', 'financial_health', 'inventory_efficiency', 'customer_satisfaction', 'overall_score', 'calculated_at']
    list_filter = ['calculated_at', 'user']
    search_fields = ['user__username', 'user__email']
    ordering = ['-calculated_at']
    readonly_fields = ['id', 'overall_score', 'calculated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
