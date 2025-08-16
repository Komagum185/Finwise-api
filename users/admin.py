from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PendingRegistration, OTPVerification, User, PendingUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for CustomUser model"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'status', 'is_verified', 'is_active', 'date_joined']
    list_filter = ['role', 'status', 'is_verified', 'is_active', 'date_joined', 'employment_status']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'business_type', 'business_location']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'date_of_birth')}),
        ('Business Information', {'fields': ('role', 'business_type', 'business_location', 'business_description')}),
        ('Profile', {'fields': ('profile_picture', 'address', 'city', 'country', 'postal_code')}),
        ('Employment', {'fields': ('employment_status', 'employer_name', 'job_title')}),
        ('Financial', {'fields': ('default_currency', 'monthly_income')}),
        ('Preferences', {'fields': ('preferred_banking_hours', 'communication_preference')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'registration_date')}),
        ('Status', {'fields': ('status', 'is_verified', 'onboarding_completed', 'onboarding_completed_at')}),
        ('Terms', {'fields': ('terms_accepted_at', 'marketing_consent')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Admin interface for User model matching TypeScript interface"""
    list_display = ['name', 'email', 'role', 'mse_type', 'mse_code', 'company', 'is_active', 'created_at']
    list_filter = ['role', 'mse_type', 'is_active', 'created_at']
    search_fields = ['name', 'email', 'company', 'mse_code']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'role')
        }),
        ('MSE Information', {
            'fields': ('mse_type', 'mse_code', 'company')
        }),
        ('Contact Information', {
            'fields': ('phone', 'location')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    """Admin interface for PendingUser model matching TypeScript interface"""
    list_display = ['name', 'email', 'phone', 'company', 'mse_type', 'status', 'registration_date', 'otp_verified']
    list_filter = ['mse_type', 'status', 'otp_verified', 'registration_date', 'send_sms', 'subscribe']
    search_fields = ['name', 'email', 'company', 'phone']
    ordering = ['-registration_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('MSE Information', {
            'fields': ('mse_type', 'company_id')
        }),
        ('Enhanced Registration', {
            'fields': ('gender', 'branch_id', 'group_id', 'cause', 'nationality')
        }),
        ('Preferences', {
            'fields': ('send_sms', 'subscribe')
        }),
        ('Status & Review', {
            'fields': ('status', 'reviewed_at', 'reviewed_by', 'rejection_reason')
        }),
        ('OTP Verification', {
            'fields': ('otp_code', 'otp_created_at', 'otp_verified'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('registration_date',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['registration_date', 'otp_created_at']
    
    actions = ['approve_users', 'reject_users']
    
    def approve_users(self, request, queryset):
        """Approve selected pending users"""
        updated = queryset.update(status='Approved')
        self.message_user(request, f'{updated} users were successfully approved.')
    approve_users.short_description = "Approve selected users"
    
    def reject_users(self, request, queryset):
        """Reject selected pending users"""
        updated = queryset.update(status='Rejected')
        self.message_user(request, f'{updated} users were successfully rejected.')
    reject_users.short_description = "Reject selected users"


@admin.register(PendingRegistration)
class PendingRegistrationAdmin(admin.ModelAdmin):
    """Admin interface for PendingRegistration model"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'status', 'submitted_at', 'otp_verified']
    list_filter = ['status', 'otp_verified', 'submitted_at', 'default_currency']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'date_of_birth')
        }),
        ('Financial Information', {
            'fields': ('default_currency', 'monthly_income')
        }),
        ('Status & Review', {
            'fields': ('status', 'reviewed_at', 'reviewed_by', 'rejection_reason')
        }),
        ('OTP Verification', {
            'fields': ('otp_code', 'otp_created_at', 'otp_verified'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['submitted_at', 'otp_created_at']
    
    actions = ['approve_registrations', 'reject_registrations']
    
    def approve_registrations(self, request, queryset):
        """Approve selected pending registrations"""
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} registrations were successfully approved.')
    approve_registrations.short_description = "Approve selected registrations"
    
    def reject_registrations(self, request, queryset):
        """Reject selected pending registrations"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} registrations were successfully rejected.')
    reject_registrations.short_description = "Reject selected registrations"


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    """Admin interface for OTPVerification model"""
    list_display = ['user', 'purpose', 'otp_code', 'created_at', 'expires_at', 'is_used', 'is_expired']
    list_filter = ['purpose', 'is_used', 'created_at']
    search_fields = ['user__username', 'user__email', 'otp_code']
    ordering = ['-created_at']
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('user', 'purpose', 'otp_code')
        }),
        ('Status', {
            'fields': ('is_used', 'is_expired')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at')
        })
    )
    
    readonly_fields = ['created_at', 'expires_at', 'is_expired']
    
    def is_expired(self, obj):
        """Check if OTP is expired"""
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
