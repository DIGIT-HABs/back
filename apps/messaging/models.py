"""
Models for messaging system.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Conversation(models.Model):
    """
    Conversation between users (agent-client, agent-agent, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Participants
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        help_text="Participants de la conversation"
    )
    
    # Conversation metadata
    conversation_type = models.CharField(
        max_length=20,
        choices=[
            ('direct', 'Direct'),
            ('group', 'Groupe'),
            ('client_agent', 'Client-Agent'),
            ('agent_agent', 'Agent-Agent'),
        ],
        default='direct',
        help_text="Type de conversation"
    )
    
    # Related entities (optional)
    client = models.ForeignKey(
        'crm.ClientProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text="Client associé (si conversation client-agent)"
    )
    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text="Propriété associée à la conversation"
    )
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Conversation active")
    is_archived = models.BooleanField(default=False, help_text="Conversation archivée")
    
    # Last message info
    last_message = models.TextField(blank=True, help_text="Dernier message")
    last_message_at = models.DateTimeField(null=True, blank=True, help_text="Date du dernier message")
    last_message_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_messages',
        help_text="Auteur du dernier message"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agent_conversations'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['conversation_type', 'is_active']),
            models.Index(fields=['last_message_at']),
        ]
    
    def __str__(self):
        participants_names = ', '.join([p.get_full_name() or p.email for p in self.participants.all()[:2]])
        return f"Conversation: {participants_names}"
    
    def get_unread_count(self, user):
        """Get unread message count for a user."""
        return self.messages.filter(
            read_by__isnull=True
        ).exclude(sender=user).count()
    
    def mark_as_read(self, user):
        """Mark all messages as read for a user."""
        self.messages.filter(
            read_by__isnull=True
        ).exclude(sender=user).update(read_by=user, read_at=timezone.now())


class Message(models.Model):
    """
    Message in a conversation.
    """
    MESSAGE_TYPES = [
        ('text', 'Texte'),
        ('image', 'Image'),
        ('file', 'Fichier'),
        ('system', 'Système'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Conversation
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Conversation parente"
    )
    
    # Sender
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="Expéditeur du message"
    )
    
    # Message content
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='text',
        help_text="Type de message"
    )
    content = models.TextField(help_text="Contenu du message")
    
    # Attachments
    image = models.ImageField(
        upload_to='messages/images/',
        null=True,
        blank=True,
        help_text="Image attachée"
    )
    file = models.FileField(
        upload_to='messages/files/',
        null=True,
        blank=True,
        help_text="Fichier attaché"
    )
    
    # Read status
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_messages',
        help_text="Utilisateur qui a lu le message"
    )
    read_at = models.DateTimeField(null=True, blank=True, help_text="Date de lecture")
    
    # Status
    is_edited = models.BooleanField(default=False, help_text="Message modifié")
    is_deleted = models.BooleanField(default=False, help_text="Message supprimé")
    edited_at = models.DateTimeField(null=True, blank=True, help_text="Date de modification")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agent_messages'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['read_by', 'read_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.email} in {self.conversation.id}"
    
    def mark_as_read(self, user):
        """Mark message as read."""
        if not self.read_by:
            self.read_by = user
            self.read_at = timezone.now()
            self.save(update_fields=['read_by', 'read_at', 'updated_at'])
