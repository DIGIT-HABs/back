"""
Admin configuration for authentication app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, Agency, UserProfile


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    """Admin for Agency model."""
    
    list_display = [
        'name', 'license_number', 'subscription_type', 'is_active', 
        'subscription_start', 'subscription_end', 'days_remaining'
    ]
    list_filter = [
        'subscription_type', 'is_active', 'is_trial', 'country',
        'subscription_start', 'subscription_end'
    ]
    search_fields = ['name', 'license_number', 'email', 'city']
    readonly_fields = ['created_at', 'updated_at', 'users_count', 'properties_count', 'clients_count']
    
    fieldsets = (
        ('Informations de base', {
            'fields': (
                'name', 'legal_name', 'license_number', 'vat_number',
                'email', 'phone', 'website'
            )
        }),
        ('Adresse', {
            'fields': (
                'address_line1', 'address_line2', 'city', 
                'postal_code', 'country'
            )
        }),
        ('Abonnement', {
            'fields': (
                'subscription_type', 'subscription_start', 'subscription_end',
                'max_agents', 'max_properties', 'max_clients',
                'is_active', 'is_trial'
            )
        }),
        ('Fonctionnalités', {
            'fields': ('features',)
        }),
        ('Paramètres', {
            'fields': ('settings',)
        }),
        ('Statistiques', {
            'fields': (
                'users_count', 'properties_count', 'clients_count'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def days_remaining(self, obj):
        """Display days remaining for subscription."""
        days = obj.get_subscription_days_remaining()
        if days == 0:
            return format_html('<span style="color: red;">Expiré</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} jours</span>', days)
        else:
            return f"{days} jours"
    days_remaining.short_description = "Jours restants"
    
    def get_queryset(self, request):
        """Annotate query with counts."""
        return super().get_queryset(request).annotate(
            users_count=models.Count('user_set'),
            properties_count=models.Count('properties'),
            clients_count=models.Count('clients')
        )
    
    def users_count(self, obj):
        """Display user count."""
        return obj.users_count
    users_count.admin_order_field = 'users_count'
    users_count.short_description = "Utilisateurs"
    
    def properties_count(self, obj):
        """Display properties count."""
        return obj.properties_count
    properties_count.admin_order_field = 'properties_count'
    properties_count.short_description = "Biens"
    
    def clients_count(self, obj):
        """Display clients count."""
        return obj.clients_count
    clients_count.admin_order_field = 'clients_count'
    clients_count.short_description = "Clients"


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = (
        'agency', 'employee_id', 'position', 'department',
        'date_of_birth', 'nationality', 'language_preference',
        'timezone', 'work_hours_start', 'work_hours_end',
        'working_days', 'email_notifications', 'sms_notifications',
        'push_notifications'
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for User model."""
    
    list_display = [
        'username', 'email', 'first_name', 'last_name', 'is_verified',
        'is_active', 'last_login', 'login_count', 'agency_link'
    ]
    list_filter = [
        'is_staff', 'is_superuser', 'is_active', 'is_verified',
        'preferred_contact_method', 'last_login', 'date_joined'
    ]
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone']
    readonly_fields = [
        'last_login', 'date_joined', 'login_count', 'created_at', 
        'updated_at', 'last_activity', 'verified_at'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Informations personnelles', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone',
                'avatar', 'bio', 'date_of_birth'
            )
        }),
        ('Préférences', {
            'fields': ('preferred_contact_method',)
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'is_verified',
                'groups', 'user_permissions'
            )
        }),
        ('Sécurité', {
            'fields': ('failed_login_attempts', 'locked_until'),
            'classes': ('collapse',)
        }),
        ('Données GDPR', {
            'fields': (
                'privacy_consent', 'privacy_consent_date',
                'marketing_consent', 'marketing_consent_date'
            ),
            'classes': ('collapse',)
        }),
        ('Métriques', {
            'fields': (
                'last_login', 'date_joined', 'login_count', 'last_activity'
            ),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at', 'verified_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = (UserProfileInline,)
    actions = ['activate_users', 'deactivate_users', 'verify_users']
    
    def agency_link(self, obj):
        """Display agency link."""
        if hasattr(obj, 'profile') and obj.profile.agency:
            url = reverse('admin:auth_agency_change', args=[obj.profile.agency.id])
            return format_html('<a href="{}">{}</a>', url, obj.profile.agency.name)
        return "-"
    agency_link.short_description = "Agence"
    agency_link.admin_order_field = 'profile__agency__name'
    
    def activate_users(self, request, queryset):
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} utilisateurs activés.")
    activate_users.short_description = "Activer les utilisateurs sélectionnés"
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} utilisateurs désactivés.")
    deactivate_users.short_description = "Désactiver les utilisateurs sélectionnés"
    
    def verify_users(self, request, queryset):
        """Verify selected users."""
        from django.utils import timezone
        updated = queryset.update(
            is_verified=True, 
            verified_at=timezone.now()
        )
        self.message_user(request, f"{updated} utilisateurs vérifiés.")
    verify_users.short_description = "Vérifier les utilisateurs sélectionnés"
    
    def get_queryset(self, request):
        """Annotate query with agency name."""
        return super().get_queryset(request).select_related(
            'profile__agency'
        )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""
    
    list_display = [
        'user', 'agency', 'position', 'email_notifications',
        'sms_notifications', 'push_notifications'
    ]
    list_filter = [
        'agency', 'email_notifications', 'sms_notifications', 
        'push_notifications', 'language_preference'
    ]
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'agency__name']
    readonly_fields = [
        'properties_assigned', 'clients_assigned', 'sales_this_month',
        'sales_this_year', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'agency')
        }),
        ('Informations professionnelles', {
            'fields': (
                'employee_id', 'position', 'department',
                'date_of_birth', 'nationality', 'language_preference'
            )
        }),
        ('Préférences de travail', {
            'fields': (
                'timezone', 'work_hours_start', 'work_hours_end',
                'working_days'
            )
        }),
        ('Préférences de notification', {
            'fields': (
                'email_notifications', 'sms_notifications', 'push_notifications'
            )
        }),
        ('Performance', {
            'fields': (
                'properties_assigned', 'clients_assigned', 
                'sales_this_month', 'sales_this_year'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Prefetch related objects."""
        return super().get_queryset(request).select_related('user', 'agency')