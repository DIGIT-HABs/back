"""
Admin configuration for core app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    Configuration, ActivityLog, Notification, 
    FileUpload, SystemStats, WebhookEvent
)


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    """Admin for Configuration model."""
    
    list_display = [
        'key', 'value_type', 'is_public', 'category', 'created_at'
    ]
    list_filter = [
        'value_type', 'is_public', 'category', 'created_at'
    ]
    search_fields = ['key', 'description', 'value']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Configuration', {
            'fields': ('key', 'value', 'value_type', 'description')
        }),
        ('Settings', {
            'fields': ('is_public', 'category')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make key readonly on edit."""
        readonly = list(self.readonly_fields)
        if obj:
            readonly.append('key')
        return readonly


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin for ActivityLog model."""
    
    list_display = [
        'level', 'component', 'action', 'user_display', 
        'ip_address', 'created_at'
    ]
    list_filter = [
        'level', 'component', 'action', 'created_at'
    ]
    search_fields = [
        'action', 'message', 'user__username', 
        'user__first_name', 'user__last_name'
    ]
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Log Information', {
            'fields': ('level', 'component', 'action', 'message')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Metadata', {
            'fields': ('metadata', 'traceback'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Prefetch related objects."""
        return super().get_queryset(request).select_related('user')
    
    def user_display(self, obj):
        """Display user information."""
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.username})"
        return "System"
    user_display.short_description = "User"
    user_display.admin_order_field = 'user__username'
    
    def has_add_permission(self, request):
        """Disable add permission for activity logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable change permission for activity logs."""
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification model."""
    
    list_display = [
        'title', 'recipient_display', 'priority', 'channel',
        'is_sent', 'read_at', 'created_at'
    ]
    list_filter = [
        'priority', 'channel', 'is_sent', 'recipient_type', 'created_at'
    ]
    search_fields = [
        'title', 'message', 'recipient_id'
    ]
    readonly_fields = [
        'is_sent', 'sent_at', 'created_at', 'updated_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Notification Content', {
            'fields': ('title', 'message', 'priority', 'channel')
        }),
        ('Recipient', {
            'fields': ('recipient_type', 'recipient_id')
        }),
        ('Status', {
            'fields': ('is_sent', 'sent_at', 'read_at')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_sent', 'mark_as_read']
    
    def recipient_display(self, obj):
        """Display recipient information."""
        if obj.recipient_type == 'user':
            return f"User: {obj.recipient_id}"
        elif obj.recipient_type == 'agency':
            return f"Agency: {obj.recipient_id}"
        else:
            return "All Users"
    recipient_display.short_description = "Recipient"
    
    def mark_as_sent(self, request, queryset):
        """Mark selected notifications as sent."""
        updated = queryset.update(
            is_sent=True,
            sent_at=admin.utils.now()
        )
        self.message_user(request, f"{updated} notifications marked as sent.")
    mark_as_sent.short_description = "Mark selected notifications as sent"
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        from django.utils import timezone
        updated = queryset.update(
            read_at=timezone.now()
        )
        self.message_user(request, f"{updated} notifications marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def has_add_permission(self, request):
        """Limit add permission to staff only."""
        return request.user.is_staff


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    """Admin for FileUpload model."""
    
    list_display = [
        'filename', 'file_type', 'file_size_display', 'uploaded_by',
        'purpose', 'created_at'
    ]
    list_filter = [
        'mime_type', 'purpose', 'created_at'
    ]
    search_fields = [
        'original_name', 'uploaded_by__username', 
        'uploaded_by__first_name', 'uploaded_by__last_name'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'file_size'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('File Information', {
            'fields': ('file', 'original_name', 'mime_type', 'file_size')
        }),
        ('Upload Details', {
            'fields': ('uploaded_by', 'purpose')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Prefetch related objects."""
        return super().get_queryset(request).select_related('uploaded_by')
    
    def filename(self, obj):
        """Display filename with download link."""
        if obj.file:
            url = obj.file.url
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                url, obj.original_name
            )
        return obj.original_name
    filename.short_description = "Filename"
    
    def file_type(self, obj):
        """Display file type."""
        if obj.mime_type:
            if obj.mime_type.startswith('image/'):
                return format_html(
                    '<span style="color: green;">🖼️ Image</span>'
                )
            elif obj.mime_type == 'application/pdf':
                return format_html(
                    '<span style="color: red;">📄 PDF</span>'
                )
            else:
                return obj.mime_type.split('/')[-1].upper()
        return "Unknown"
    file_type.short_description = "Type"
    
    def file_size_display(self, obj):
        """Display file size in human readable format."""
        if obj.file_size:
            size = obj.file_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        return "Unknown"
    file_size_display.short_description = "Size"


@admin.register(SystemStats)
class SystemStatsAdmin(admin.ModelAdmin):
    """Admin for SystemStats model."""
    
    list_display = [
        'metric', 'value', 'value_type', 'period', 'recorded_at'
    ]
    list_filter = [
        'metric', 'value_type', 'period', 'recorded_at'
    ]
    search_fields = ['metric']
    readonly_fields = [
        'created_at', 'updated_at', 'recorded_at'
    ]
    date_hierarchy = 'recorded_at'
    
    fieldsets = (
        ('Statistics', {
            'fields': ('metric', 'value', 'value_type', 'period')
        }),
        ('Metadata', {
            'fields': ('recorded_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Limit add permission to superusers only."""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Limit change permission to superusers only."""
        return request.user.is_superuser


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    """Admin for WebhookEvent model."""
    
    list_display = [
        'event_type', 'processed', 'retry_count', 'error_message', 'created_at'
    ]
    list_filter = [
        'event_type', 'processed', 'created_at'
    ]
    search_fields = ['event_type', 'error_message']
    readonly_fields = [
        'created_at', 'updated_at', 'processed_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'payload')
        }),
        ('Processing Status', {
            'fields': ('processed', 'processed_at', 'retry_count', 'max_retries')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processed', 'reset_retry_count']
    
    def get_queryset(self, request):
        """Order by creation date."""
        return super().get_queryset(request).order_by('-created_at')
    
    def mark_as_processed(self, request, queryset):
        """Mark selected webhooks as processed."""
        from django.utils import timezone
        updated = queryset.update(
            processed=True,
            processed_at=timezone.now()
        )
        self.message_user(request, f"{updated} webhooks marked as processed.")
    mark_as_processed.short_description = "Mark selected webhooks as processed"
    
    def reset_retry_count(self, request, queryset):
        """Reset retry count for selected webhooks."""
        updated = queryset.update(retry_count=0)
        self.message_user(request, f"Retry count reset for {updated} webhooks.")
    reset_retry_count.short_description = "Reset retry count"