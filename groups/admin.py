from django.contrib import admin
from .models import Group, GroupMembership, GroupWallet


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'description', 'created_by', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    ordering = ['name']


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = [
        'group', 'mse', 'joined_at', 'is_active'
    ]
    list_filter = ['is_active', 'joined_at']
    search_fields = ['group__name', 'mse__first_name', 'mse__last_name']
    readonly_fields = ['joined_at']
    ordering = ['-joined_at']


@admin.register(GroupWallet)
class GroupWalletAdmin(admin.ModelAdmin):
    list_display = [
        'group', 'balance', 'currency', 'created_at'
    ]
    list_filter = ['currency', 'created_at']
    search_fields = ['group__name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
