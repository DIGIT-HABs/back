"""
Serializers for core app.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (
    Configuration, ActivityLog, Notification, 
    FileUpload, SystemStats, WebhookEvent
)

User = get_user_model()


class ConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for Configuration model."""
    
    class Meta:
        model = Configuration
        fields = [
            'id', 'key', 'value', 'value_type', 'description',
            'is_public', 'category', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_key(self, value):
        """Validate key uniqueness."""
        config = self.instance
        if Configuration.objects.filter(key=value).exclude(pk=config.pk if config else None).exists():
            raise serializers.ValidationError("Configuration key already exists.")
        return value
    
    def validate_value(self, value):
        """Validate value based on value_type."""
        config_type = self.initial_data.get('value_type', 'string')
        
        if config_type == 'integer':
            try:
                int(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError("Value must be an integer.")
        
        elif config_type == 'float':
            try:
                float(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError("Value must be a float.")
        
        elif config_type == 'boolean':
            if value not in ['true', 'false', '1', '0', True, False]:
                raise serializers.ValidationError("Value must be a boolean.")
        
        elif config_type == 'json':
            try:
                import json
                json.loads(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError("Value must be valid JSON.")
        
        return value


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for ActivityLog model."""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    ip_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'level', 'component', 'action', 'message',
            'user', 'user_name', 'ip_address', 'user_agent',
            'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_name(self, obj):
        """Get user full name."""
        return obj.user.get_full_name() if obj.user else None


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'priority', 'channel',
            'is_sent', 'sent_at', 'read_at', 'metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_sent', 'sent_at', 'created_at', 'updated_at'
        ]
    
    def validate_recipient_id(self, value):
        """Validate recipient ID format."""
        recipient_type = self.initial_data.get('recipient_type', 'user')
        if recipient_type == 'user' and not value:
            raise serializers.ValidationError("Recipient ID is required for user notifications.")
        return value


class FileUploadSerializer(serializers.ModelSerializer):
    """Serializer for FileUpload model."""
    
    file_url = serializers.CharField(source='file.url', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_type = serializers.SerializerMethodField()
    
    class Meta:
        model = FileUpload
        fields = [
            'id', 'file', 'file_url', 'original_name', 'file_size',
            'mime_type', 'file_type', 'uploaded_by', 'uploaded_by_name',
            'purpose', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_url', 'uploaded_by_name', 'created_at', 'updated_at'
        ]
    
    def get_file_type(self, obj):
        """Get file type from mime type."""
        mime_type = obj.mime_type or ''
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return 'document'
        else:
            return 'other'


class SystemStatsSerializer(serializers.ModelSerializer):
    """Serializer for SystemStats model."""
    
    class Meta:
        model = SystemStats
        fields = [
            'id', 'metric', 'value', 'value_type', 'period',
            'recorded_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'recorded_at', 'created_at', 'updated_at'
        ]


class WebhookEventSerializer(serializers.ModelSerializer):
    """Serializer for WebhookEvent model."""
    
    class Meta:
        model = WebhookEvent
        fields = [
            'id', 'event_type', 'payload', 'processed', 'processed_at',
            'retry_count', 'max_retries', 'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'processed_at', 'created_at', 'updated_at'
        ]
    
    def validate_retry_count(self, value):
        """Validate retry count doesn't exceed max retries."""
        max_retries = self.initial_data.get('max_retries', 3)
        if value > max_retries:
            raise serializers.ValidationError("Retry count cannot exceed max retries.")
        return value


class SystemHealthSerializer(serializers.Serializer):
    """Serializer for system health response."""
    
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    database = serializers.CharField()
    redis = serializers.CharField(required=False)
    version = serializers.CharField()
    environment = serializers.CharField()
    error = serializers.CharField(required=False)


class SystemStatsResponseSerializer(serializers.Serializer):
    """Serializer for system statistics response."""
    
    users = serializers.DictField()
    properties = serializers.DictField()
    system = serializers.DictField()
    timestamp = serializers.DateTimeField()


class APIVersionSerializer(serializers.Serializer):
    """Serializer for API version response."""
    
    api_version = serializers.CharField()
    django_version = serializers.CharField()
    framework_version = serializers.CharField()
    build_date = serializers.DateField()
    environment = serializers.CharField()
    documentation = serializers.URLField()
    redoc = serializers.URLField()


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check response."""
    
    status = serializers.ChoiceField(choices=['healthy', 'unhealthy'])
    timestamp = serializers.DateTimeField()
    database = serializers.ChoiceField(choices=['ok', 'error'])
    error = serializers.CharField(required=False)


class BulkConfigurationSerializer(serializers.Serializer):
    """Serializer for bulk configuration operations."""
    
    configurations = ConfigurationSerializer(many=True)
    
    def validate_configurations(self, value):
        """Validate configuration list."""
        if not value:
            raise serializers.ValidationError("At least one configuration is required.")
        return value