"""
Admin configuration for reviews app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Review, ReviewHelpful


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for Review model."""
    
    list_display = [
        'id', 'review_type', 'author_name', 'rating_stars',
        'property_link', 'agent_link', 'is_published',
        'is_verified', 'helpful_count', 'created_at'
    ]
    list_filter = [
        'review_type', 'rating', 'is_published', 'is_verified',
        'created_at', 'moderated_at'
    ]
    search_fields = [
        'title', 'comment', 'author__first_name', 'author__last_name',
        'author__email', 'property__title'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'helpful_count',
        'average_detailed_rating'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': (
                'id', 'review_type', 'author', 'created_at', 'updated_at'
            )
        }),
        ('Relations', {
            'fields': ('property', 'agent', 'reservation')
        }),
        ('Évaluation', {
            'fields': (
                'rating', 'title', 'comment',
                'rating_communication', 'rating_professionalism',
                'rating_value', 'rating_cleanliness', 'rating_location',
                'average_detailed_rating'
            )
        }),
        ('Modération', {
            'fields': (
                'is_published', 'is_verified',
                'moderated_at', 'moderated_by', 'moderation_notes'
            )
        }),
        ('Réponse', {
            'fields': ('response', 'response_date', 'response_by')
        }),
        ('Statistiques', {
            'fields': ('helpful_count',)
        }),
    )
    
    def author_name(self, obj):
        """Display author name."""
        return obj.author.get_full_name()
    author_name.short_description = 'Auteur'
    
    def rating_stars(self, obj):
        """Display rating as stars."""
        stars = '⭐' * obj.rating
        return format_html('<span style="font-size: 16px;">{}</span>', stars)
    rating_stars.short_description = 'Note'
    
    def property_link(self, obj):
        """Display link to property."""
        if obj.property:
            return format_html(
                '<a href="/admin/properties/property/{}/change/">{}</a>',
                obj.property.id, obj.property.title
            )
        return '-'
    property_link.short_description = 'Bien'
    
    def agent_link(self, obj):
        """Display link to agent."""
        if obj.agent:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.agent.id, obj.agent.get_full_name()
            )
        return '-'
    agent_link.short_description = 'Agent'
    
    actions = ['publish_reviews', 'unpublish_reviews', 'verify_reviews']
    
    def publish_reviews(self, request, queryset):
        """Publish selected reviews."""
        count = 0
        for review in queryset:
            review.publish(moderator=request.user)
            count += 1
        self.message_user(request, f'{count} avis publié(s).')
    publish_reviews.short_description = 'Publier les avis sélectionnés'
    
    def unpublish_reviews(self, request, queryset):
        """Unpublish selected reviews."""
        count = 0
        for review in queryset:
            review.unpublish(moderator=request.user)
            count += 1
        self.message_user(request, f'{count} avis dépublié(s).')
    unpublish_reviews.short_description = 'Dépublier les avis sélectionnés'
    
    def verify_reviews(self, request, queryset):
        """Verify selected reviews."""
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} avis vérifié(s).')
    verify_reviews.short_description = 'Vérifier les avis sélectionnés'


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    """Admin interface for ReviewHelpful model."""
    
    list_display = ['id', 'review_preview', 'user_name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__first_name', 'user__last_name', 'review__title']
    readonly_fields = ['id', 'created_at']
    
    def review_preview(self, obj):
        """Display review preview."""
        return f"{obj.review.review_type} - {obj.review.rating}⭐"
    review_preview.short_description = 'Avis'
    
    def user_name(self, obj):
        """Display user name."""
        return obj.user.get_full_name()
    user_name.short_description = 'Utilisateur'
