"""
Admin configuration for CRM app.
"""

from django.contrib import admin
from .models import ClientProfile, Lead, ClientInteraction, PropertyInterest


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Admin for ClientProfile model."""
    
    list_display = ['user', 'status', 'priority_level', 'financing_status', 'conversion_score', 'created_at']
    list_filter = ['status', 'priority_level', 'financing_status', 'preferred_contact_method', 'marital_status', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'conversion_score', 'total_properties_viewed', 'total_inquiries_made', 'last_property_view', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Informations personnelles', {
            'fields': ('date_of_birth', 'nationality', 'marital_status')
        }),
        ('Préférences de contact', {
            'fields': ('preferred_contact_method', 'preferred_contact_time')
        }),
        ('Préférences de propriété', {
            'fields': ('max_budget', 'min_budget', 'preferred_property_types', 'preferred_locations', 
                      'min_bedrooms', 'max_bedrooms', 'min_area', 'max_area')
        }),
        ('Préférences de localisation', {
            'fields': ('preferred_cities', 'max_distance_from_center')
        }),
        ('Informations financières', {
            'fields': ('financing_status', 'credit_score_range')
        }),
        ('Préférences additionnelles', {
            'fields': ('must_have_features', 'deal_breakers', 'lifestyle_notes')
        }),
        ('Statut et activité', {
            'fields': ('status', 'priority_level', 'last_property_view', 'total_properties_viewed', 
                      'total_inquiries_made', 'conversion_score')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin for Lead model."""
    
    list_display = ['full_name', 'email', 'phone', 'status', 'qualification', 'source', 'assigned_agent', 'score', 'created_at']
    list_filter = ['status', 'qualification', 'source', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'company']
    readonly_fields = ['id', 'score', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations du lead', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'company')
        }),
        ('Détails du lead', {
            'fields': ('source', 'status', 'qualification')
        }),
        ('Intérêt pour la propriété', {
            'fields': ('property_type_interest', 'budget_range', 'location_interest', 'timeframe')
        }),
        ('Attribution', {
            'fields': ('assigned_agent', 'agency')
        }),
        ('Évaluation', {
            'fields': ('score', 'notes', 'next_action', 'next_action_date')
        }),
        ('Conversion', {
            'fields': ('converted_to_client', 'conversion_date', 'lost_reason')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )


@admin.register(ClientInteraction)
class ClientInteractionAdmin(admin.ModelAdmin):
    """Admin for ClientInteraction model."""
    
    list_display = ['client', 'agent', 'interaction_type', 'channel', 'subject', 'status', 'scheduled_date', 'created_at']
    list_filter = ['interaction_type', 'channel', 'outcome', 'status', 'priority', 'scheduled_date', 'created_at']
    search_fields = ['client__username', 'agent__username', 'subject', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Participants', {
            'fields': ('client', 'agent')
        }),
        ('Détails de l\'interaction', {
            'fields': ('interaction_type', 'channel', 'subject', 'content', 'outcome')
        }),
        ('Planification', {
            'fields': ('scheduled_date', 'completed_date', 'duration_minutes')
        }),
        ('Objets liés', {
            'fields': ('content_type', 'object_id')
        }),
        ('Suivi', {
            'fields': ('requires_follow_up', 'follow_up_date', 'follow_up_completed')
        }),
        ('Priorité et statut', {
            'fields': ('priority', 'status')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )


@admin.register(PropertyInterest)
class PropertyInterestAdmin(admin.ModelAdmin):
    """Admin for PropertyInterest model."""
    
    list_display = ['client', 'property', 'interaction_type', 'interest_level', 'match_score', 'status', 'interaction_date']
    list_filter = ['interaction_type', 'interest_level', 'status', 'interaction_date']
    search_fields = ['client__username', 'property__title', 'notes']
    readonly_fields = ['id', 'match_score', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Client et propriété', {
            'fields': ('client', 'property')
        }),
        ('Interaction', {
            'fields': ('interaction_type', 'interaction_date', 'notes')
        }),
        ('Intérêt', {
            'fields': ('interest_level', 'match_score')
        }),
        ('Statut', {
            'fields': ('status',)
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )
