from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta

User = get_user_model()


class NotificationType(models.Model):
    """Types of notifications available in the system"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    template = models.TextField(help_text="Notification template with placeholders")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Type"
        verbose_name_plural = "Notification Types"
    
    def __str__(self):
        return self.name


class Notification(models.Model):
    """Main notification model"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
        ('all', 'All Methods'),
    ]
    
    # Recipient
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification details
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Priority and status
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Delivery settings
    delivery_methods = models.JSONField(default=list, help_text="List of delivery methods")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Related object (optional)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['priority', 'created_at']),
            models.Index(fields=['scheduled_at', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    @property
    def is_read(self):
        """Check if notification has been read"""
        return self.status == 'read'
    
    @property
    def is_delivered(self):
        """Check if notification has been delivered"""
        return self.status in ['delivered', 'read']
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.status = 'read'
        self.read_at = timezone.now()
        self.save()
    
    def mark_as_delivered(self):
        """Mark notification as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_failed(self):
        """Mark notification as failed"""
        self.status = 'failed'
        self.save()


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # General preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    
    # Frequency preferences
    daily_digest = models.BooleanField(default=True)
    weekly_summary = models.BooleanField(default=True)
    instant_notifications = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(default='22:00:00')
    quiet_hours_end = models.TimeField(default='08:00:00')
    
    # Type-specific preferences
    type_preferences = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled:
            return False
        
        current_time = timezone.now().time()
        start_time = self.quiet_hours_start
        end_time = self.quiet_hours_end
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:  # Quiet hours span midnight
            return current_time >= start_time or current_time <= end_time


class NotificationTemplate(models.Model):
    """Templates for different types of notifications"""
    
    name = models.CharField(max_length=100, unique=True)
    notification_type = models.ForeignKey(NotificationType, on_delete=models.CASCADE)
    
    # Template content
    subject_template = models.CharField(max_length=255)
    message_template = models.TextField()
    html_template = models.TextField(blank=True, help_text="HTML version for email notifications")
    
    # Variables
    variables = models.JSONField(default=list, help_text="List of available variables")
    
    # Localization
    language = models.CharField(max_length=10, default='en')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"
        unique_together = ['name', 'language']
    
    def __str__(self):
        return f"{self.name} ({self.language})"


class NotificationDeliveryLog(models.Model):
    """Log of notification delivery attempts"""
    
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='delivery_logs')
    
    # Delivery attempt details
    delivery_method = models.CharField(max_length=20)
    attempt_number = models.PositiveIntegerField(default=1)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('retry', 'Retry'),
    ])
    
    # Error details
    error_message = models.TextField(blank=True)
    error_code = models.CharField(max_length=100, blank=True)
    
    # Delivery metadata
    delivery_metadata = models.JSONField(default=dict, blank=True)
    
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Notification Delivery Log"
        verbose_name_plural = "Notification Delivery Logs"
        ordering = ['-attempted_at']
    
    def __str__(self):
        return f"{self.notification.title} - {self.delivery_method} - {self.status}"


class NotificationGroup(models.Model):
    """Groups for bulk notifications"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Group members
    users = models.ManyToManyField(User, related_name='notification_groups')
    
    # Group settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Group"
        verbose_name_plural = "Notification Groups"
    
    def __str__(self):
        return self.name
    
    def add_user(self, user):
        """Add user to notification group"""
        self.users.add(user)
    
    def remove_user(self, user):
        """Remove user from notification group"""
        self.users.remove(user)
    
    def get_active_users(self):
        """Get active users in the group"""
        return self.users.filter(is_active=True)
