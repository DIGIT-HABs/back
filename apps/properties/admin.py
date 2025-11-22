"""
Admin configuration for properties app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Property, PropertyImage, PropertyDocument, PropertyVisit, PropertyHistory, PropertySearch


class PropertyImageInline(admin.TabularInline):
    """Inline admin for property images."""
    model = PropertyImage
    extra = 1
    fields = ['image', 'title', 'is_primary', 'order']
    readonly_fields = ['id']


class PropertyDocumentInline(admin.TabularInline):
    """Inline admin for property documents."""
    model = PropertyDocument
    extra = 0
    fields = ['title', 'document_type', 'document_file', 'is_public']
    readonly_fields = ['id', 'file_size', 'mime_type']


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    """Admin for Property model."""
    
    list_display = [
        'title', 'property_type', 'status', 'price_display', 
        'city', 'bedrooms', 'bathrooms', 'surface_area', 
        'is_featured', 'agent', 'created_at'
    ]
    list_filter = [
        'property_type', 'status', 'is_featured', 'is_public',
        'city', 'has_parking', 'has_pool', 'has_elevator',
        'furnished', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'address_line1', 
        'city', 'postal_code', 'agent__username'
    ]
    readonly_fields = ['id', 'price_per_sqm', 'view_count', 'inquiry_count', 'created_at', 'updated_at', 'published_at']
    inlines = [PropertyImageInline, PropertyDocumentInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'description', 'property_type', 'status')
        }),
        ('Localisation', {
            'fields': ('address_line1', 'address_line2', 'city', 'postal_code', 'country', 'latitude', 'longitude')
        }),
        ('Informations financières', {
            'fields': ('price', 'price_per_sqm')
        }),
        ('Détails de la propriété', {
            'fields': ('surface_area', 'usable_area', 'garden_area', 'rooms', 'bedrooms', 'bathrooms', 'toilets')
        }),
        ('Caractéristiques du bâtiment', {
            'fields': ('floor', 'total_floors', 'year_built')
        }),
        ('Énergie et environnement', {
            'fields': ('energy_class', 'ges_class', 'heating_type')
        }),
        ('Équipements', {
            'fields': ('has_balcony', 'has_terrace', 'has_garden', 'has_garage', 'has_parking', 
                      'has_elevator', 'has_fireplace', 'has_pool', 'has_air_conditioning', 'has_security_system')
        }),
        ('Ameublement', {
            'fields': ('furnished', 'furnished_level')
        }),
        ('Disponibilité', {
            'fields': ('available_from',)
        }),
        ('Propriétaire', {
            'fields': ('owner_name', 'owner_phone', 'owner_email')
        }),
        ('Agence et agent', {
            'fields': ('agency', 'agent')
        }),
        ('Équipements et caractéristiques supplémentaires', {
            'fields': ('amenities', 'additional_features')
        }),
        ('SEO et marketing', {
            'fields': ('meta_title', 'meta_description', 'featured_image')
        }),
        ('Paramètres', {
            'fields': ('is_featured', 'is_public', 'show_price')
        }),
        ('Métadonnées', {
            'fields': ('id', 'view_count', 'inquiry_count', 'created_at', 'updated_at', 'published_at')
        }),
    )
    
    def price_display(self, obj):
        """Display formatted price."""
        return f"{obj.price:,.0f} FCFA"
    price_display.short_description = "Prix"


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    """Admin for PropertyImage model."""
    
    list_display = ['property', 'title', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['property__title', 'title']
    readonly_fields = ['id', 'file_size', 'width', 'height', 'created_at']
    ordering = ['property', 'order']


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    """Admin for PropertyDocument model."""
    
    list_display = ['property', 'title', 'document_type', 'is_public', 'requires_auth', 'created_at']
    list_filter = ['document_type', 'is_public', 'requires_auth', 'created_at']
    search_fields = ['property__title', 'title']
    readonly_fields = ['id', 'file_size', 'mime_type', 'created_at']


@admin.register(PropertyVisit)
class PropertyVisitAdmin(admin.ModelAdmin):
    """Admin for PropertyVisit model."""
    
    list_display = [
        'property', 'client', 'visit_type', 'scheduled_date', 
        'status', 'agent', 'created_at'
    ]
    list_filter = ['visit_type', 'status', 'scheduled_date', 'created_at']
    search_fields = ['property__title', 'client__email', 'visitor_name', 'visitor_email', 'visitor_phone']
    readonly_fields = ['id', 'confirmed_at', 'completed_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Propriété et Client', {
            'fields': ('property', 'client')
        }),
        ('Détails de la visite', {
            'fields': ('visit_type', 'scheduled_date', 'duration_minutes')
        }),
        ('Informations du visiteur (legacy)', {
            'fields': ('visitor_name', 'visitor_email', 'visitor_phone', 'visitor_count')
        }),
        ('Statut', {
            'fields': ('status', 'agent')
        }),
        ('Notes et feedback', {
            'fields': ('notes', 'visitor_notes', 'agent_notes', 'feedback', 'rating')
        }),
        ('Métadonnées', {
            'fields': ('id', 'confirmed_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )


@admin.register(PropertyHistory)
class PropertyHistoryAdmin(admin.ModelAdmin):
    """Admin for PropertyHistory model."""
    
    list_display = ['property', 'action', 'field_name', 'changed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['property__title', 'changed_by__username']
    readonly_fields = ['id', 'property', 'action', 'field_name', 'old_value', 'new_value', 'changed_by', 'change_reason', 'ip_address', 'user_agent', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PropertySearch)
class PropertySearchAdmin(admin.ModelAdmin):
    """Admin for PropertySearch model."""
    
    list_display = ['user', 'name', 'frequency', 'email_notifications', 'sms_notifications', 'is_active', 'created_at']
    list_filter = ['frequency', 'email_notifications', 'sms_notifications', 'is_active', 'created_at']
    search_fields = ['user__username', 'name', 'description']
    readonly_fields = ['id', 'last_run', 'results_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'agency')
        }),
        ('Recherche', {
            'fields': ('name', 'description', 'search_criteria')
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'sms_notifications', 'frequency')
        }),
        ('Statut', {
            'fields': ('is_active', 'last_run', 'results_count')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at')
        }),
    )
