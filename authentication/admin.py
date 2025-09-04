from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'username', 'first_name', 'last_name', 'phone_number', 'NIN',
        'is_super_admin', 'is_agent', 'is_mse', 'is_partner', 'is_approved'
    ]
    list_filter = [
        'is_super_admin', 'is_agent', 'is_mse', 'is_partner', 
        'is_approved', 'is_active', 'date_joined'
    ]
    search_fields = [
        'username', 'first_name', 'last_name', 'phone_number', 'NIN', 'email'
    ]
    readonly_fields = ['date_joined', 'last_login']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'NIN', 'profile_image')
        }),
        ('Roles & Permissions', {
            'fields': (
                'is_super_admin', 'is_agent', 'is_mse', 'is_partner',
                'is_staff', 'is_active', 'is_approved', 'first_login'
            )
        }),
        ('Role-Specific Information', {
            'fields': ('mse_name', 'assigned_agent', 'partner_institution')
        }),
        ('Capabilities', {
            'fields': ('capabilities',),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'first_name', 'last_name', 'phone_number', 'NIN'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assigned_agent')
