"""
Serializers for reviews app.
"""

from rest_framework import serializers
from django.db.models import Avg
from apps.auth.serializers import UserSerializer
from apps.properties.serializers import PropertyListSerializer
from .models import Review, ReviewHelpful
from apps.auth.models import User


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review model."""
    
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    author_avatar = serializers.SerializerMethodField(source='author.avatar')
    property_title = serializers.CharField(source='property.title', read_only=True)
    agent_name = serializers.CharField(source='agent.get_full_name', read_only=True)
    response_by_name = serializers.CharField(source='response_by.get_full_name', read_only=True)
    is_author = serializers.SerializerMethodField()
    has_voted_helpful = serializers.SerializerMethodField()
    average_detailed_rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'review_type', 'author', 'author_name', 'author_avatar',
            'property', 'property_title', 'agent', 'agent_name', 'reservation',
            'rating', 'title', 'comment',
            'rating_communication', 'rating_professionalism', 'rating_value',
            'rating_cleanliness', 'rating_location', 'average_detailed_rating',
            'is_published', 'is_verified', 'moderated_at', 'moderated_by',
            'moderation_notes',
            'response', 'response_date', 'response_by', 'response_by_name',
            'helpful_count', 'has_voted_helpful',
            'created_at', 'updated_at', 'is_author',
        ]
        read_only_fields = [
            'id', 'author', 'is_published', 'is_verified', 'moderated_at',
            'moderated_by', 'helpful_count', 'response_date', 'response_by',
            'created_at', 'updated_at',
        ]
    
    def get_author_avatar(self, obj: Review):
        """Get author avatar URL."""
        avatar = getattr(obj.author, "avatar", None)
    # Pour un ImageField/FileField sans fichier, avatar existe mais avatar.name est vide
        if not avatar or not getattr(avatar, "name", ""):
            return None
        try:
            return avatar.url
        except Exception:
            return None
    
    def get_is_author(self, obj):
        """Check if current user is the author."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user
        return False
    
    def get_has_voted_helpful(self, obj):
        """Check if current user has voted this review as helpful."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.helpful_votes.filter(user=request.user).exists()
        return False


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""
    
    class Meta:
        model = Review
        fields = [
            'review_type', 'property', 'agent', 'reservation',
            'rating', 'title', 'comment',
            'rating_communication', 'rating_professionalism', 'rating_value',
            'rating_cleanliness', 'rating_location',
        ]
    
    def validate(self, data):
        """Validate review data."""
        review_type = data.get('review_type')
        
        # Validate that appropriate relationship is provided
        if review_type == 'property' and not data.get('property'):
            raise serializers.ValidationError({
                'property': 'Un bien immobilier est requis pour ce type d\'avis.'
            })
        
        if review_type == 'agent' and not data.get('agent'):
            raise serializers.ValidationError({
                'agent': 'Un agent est requis pour ce type d\'avis.'
            })
        
        if review_type == 'reservation' and not data.get('reservation'):
            raise serializers.ValidationError({
                'reservation': 'Une réservation est requise pour ce type d\'avis.'
            })
        
        # If reservation is provided, auto-set property and agent
        reservation = data.get('reservation')
        if reservation:
            data['property'] = reservation.property
            if reservation.assigned_agent:
                data['agent'] = reservation.assigned_agent
            # Mark as verified if reservation is completed
            if reservation.status == 'completed':
                data['is_verified'] = True
        
        return data
    
    def create(self, validated_data):
        """Create review with author from request."""
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)


class ReviewResponseSerializer(serializers.Serializer):
    """Serializer for adding agent/owner response to review."""
    
    response = serializers.CharField(required=True, min_length=10)
    
    def validate_response(self, value):
        """Validate response is not empty."""
        if not value.strip():
            raise serializers.ValidationError('La réponse ne peut pas être vide.')
        return value


class ReviewModerationSerializer(serializers.Serializer):
    """Serializer for moderating reviews."""
    
    is_published = serializers.BooleanField(required=True)
    moderation_notes = serializers.CharField(required=False, allow_blank=True)


class PropertyReviewSummarySerializer(serializers.Serializer):
    """Serializer for property review statistics."""
    
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()
    rating_distribution = serializers.DictField()
    verified_reviews_count = serializers.IntegerField()
    average_communication = serializers.FloatField()
    average_professionalism = serializers.FloatField()
    average_value = serializers.FloatField()
    average_cleanliness = serializers.FloatField()
    average_location = serializers.FloatField()


class AgentReviewSummarySerializer(serializers.Serializer):
    """Serializer for agent review statistics."""
    
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()
    rating_distribution = serializers.DictField()
    verified_reviews_count = serializers.IntegerField()
    average_communication = serializers.FloatField()
    average_professionalism = serializers.FloatField()
