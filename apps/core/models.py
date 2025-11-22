"""
Core models for shared functionality.
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField


class TimestampedModel(models.Model):
    """Base model with created_at and updated_at timestamps."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class BaseModel(TimestampedModel):
    """Base model with common fields."""
    
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        """Soft delete instead of hard delete."""
        self.is_deleted = True
        self.save(using=using)
    
    def hard_delete(self, using=None, keep_parents=False):
        """Actually delete the object."""
        super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.save()


class Configuration(BaseModel):
    """Global configuration settings."""
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    value_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('json', 'JSON'),
            ('list', 'List'),
        ],
        default='string'
    )
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    category = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'configurations'
        verbose_name = 'Configuration'
        verbose_name_plural = 'Configurations'
        ordering = ['category', 'key']
    
    def __str__(self):
        return f"{self.key} = {self.value[:50]}"


class ActivityLog(BaseModel):
    """System activity logging."""
    
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    COMPONENT_CHOICES = [
        ('auth', 'Authentication'),
        ('properties', 'Properties'),
        ('clients', 'Clients'),
        ('reservations', 'Reservations'),
        ('payments', 'Payments'),
        ('notifications', 'Notifications'),
        ('api', 'API'),
        ('admin', 'Admin'),
        ('system', 'System'),
    ]
    
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    component = models.CharField(max_length=20, choices=COMPONENT_CHOICES)
    action = models.CharField(max_length=100)
    message = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activity_logs'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    traceback = models.TextField(blank=True)
    
    class Meta:
        db_table = 'activity_logs'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['component', 'level']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.level} - {self.component} - {self.action}"


class Notification(BaseModel):
    """System notifications."""
    
    RECIPIENT_CHOICES = [
        ('user', 'User'),
        ('agency', 'Agency'),
        ('all', 'All Users'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In App'),
    ]
    
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_CHOICES)
    recipient_id = models.CharField(max_length=100, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_type', 'recipient_id']),
            models.Index(fields=['is_sent', 'priority']),
        ]
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save()


class FileUpload(BaseModel):
    """Generic file upload tracking."""
    
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    original_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='uploaded_files'
    )
    purpose = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'file_uploads'
        verbose_name = 'File Upload'
        verbose_name_plural = 'File Uploads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploaded_by', 'created_at']),
            models.Index(fields=['purpose']),
        ]
    
    def __str__(self):
        return f"{self.original_name} ({self.file_size} bytes)"


class SystemStats(BaseModel):
    """System statistics and metrics."""
    
    STATS_CHOICES = [
        ('users_count', 'Total Users'),
        ('active_users', 'Active Users'),
        ('properties_count', 'Total Properties'),
        ('available_properties', 'Available Properties'),
        ('clients_count', 'Total Clients'),
        ('active_clients', 'Active Clients'),
        ('reservations_count', 'Total Reservations'),
        ('revenue_month', 'Monthly Revenue'),
        ('api_requests', 'API Requests'),
        ('storage_used', 'Storage Used'),
    ]
    
    metric = models.CharField(max_length=30, choices=STATS_CHOICES, unique=True)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    value_type = models.CharField(
        max_length=20,
        choices=[
            ('count', 'Count'),
            ('amount', 'Amount'),
            ('percentage', 'Percentage'),
            ('bytes', 'Bytes'),
        ],
        default='count'
    )
    period = models.CharField(
        max_length=20,
        choices=[
            ('realtime', 'Real-time'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='realtime'
    )
    recorded_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'system_stats'
        verbose_name = 'System Stat'
        verbose_name_plural = 'System Stats'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric', 'period']),
            models.Index(fields=['recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.metric}: {self.value} ({self.period})"


class WebhookEvent(BaseModel):
    """Webhook events for external integrations."""
    
    EVENT_CHOICES = [
        ('user_registered', 'User Registered'),
        ('property_created', 'Property Created'),
        ('property_updated', 'Property Updated'),
        ('reservation_created', 'Reservation Created'),
        ('payment_succeeded', 'Payment Succeeded'),
        ('notification_sent', 'Notification Sent'),
    ]
    
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    payload = models.JSONField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'webhook_events'
        verbose_name = 'Webhook Event'
        verbose_name_plural = 'Webhook Events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'processed']),
            models.Index(fields=['created_at']),
        ]
    
    def mark_as_processed(self):
        """Mark webhook as processed."""
        self.processed = True
        self.processed_at = timezone.now()
        self.save()
    
    def can_retry(self):
        """Check if webhook can be retried."""
        return self.retry_count < self.max_retries and not self.processed
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.save()