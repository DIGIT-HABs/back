"""
Admin interface for messaging app.
"""

from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation_type', 'is_active', 'is_archived', 'last_message_at', 'created_at']
    list_filter = ['conversation_type', 'is_active', 'is_archived', 'created_at']
    search_fields = ['id', 'last_message']
    filter_horizontal = ['participants']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'message_type', 'read_by', 'created_at']
    list_filter = ['message_type', 'is_edited', 'is_deleted', 'created_at']
    search_fields = ['content', 'sender__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
