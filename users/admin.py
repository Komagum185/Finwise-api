from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_verified', 'is_staff', 'is_active']
    list_filter = ['is_verified', 'is_staff', 'is_active', 'date_joined', 'default_currency']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Financial Settings', {
            'fields': ('default_currency', 'monthly_income', 'is_verified')
        }),
        ('Additional Info', {
            'fields': ('phone_number', 'date_of_birth', 'profile_picture')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Financial Settings', {
            'fields': ('default_currency', 'monthly_income')
        }),
        ('Additional Info', {
            'fields': ('phone_number', 'date_of_birth')
        }),
    )
