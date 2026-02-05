"""
Models for reviews and ratings system.
"""

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.auth.models import User
from apps.properties.models import Property
from apps.reservations.models import Reservation

_property = property



class Review(models.Model):
    """
    Model for client reviews of properties, agents, and reservations.
    """
    
    # Review Types
    REVIEW_TYPE_CHOICES = [
        ('property', 'Avis sur bien'),
        ('agent', 'Avis sur agent'),
        ('reservation', 'Avis sur réservation'),
        ('visit', 'Avis après visite'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES)
    
    # Relationships
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_written',
        help_text='Client qui a écrit l\'avis'
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True,
        help_text='Bien immobilier concerné'
    )
    agent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_received',
        null=True,
        blank=True,
        limit_choices_to={'role__in': ['agent', 'manager']},
        help_text='Agent concerné'
    )
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True,
        help_text='Réservation concernée'
    )
    
    # Rating and Content
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Note de 1 à 5 étoiles'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Titre de l\'avis'
    )
    comment = models.TextField(
        help_text='Commentaire détaillé'
    )
    
    # Detailed Ratings (optional)
    rating_communication = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text='Note pour la communication'
    )
    rating_professionalism = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text='Note pour le professionnalisme'
    )
    rating_value = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text='Note pour le rapport qualité/prix'
    )
    rating_cleanliness = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text='Note pour la propreté (bien)'
    )
    rating_location = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text='Note pour l\'emplacement (bien)'
    )
    
    # Moderation
    is_published = models.BooleanField(
        default=False,
        help_text='Avis publié et visible'
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Avis vérifié (client a effectué une réservation)'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='reviews_moderated',
        null=True,
        blank=True
    )
    moderation_notes = models.TextField(blank=True)
    
    # Response
    response = models.TextField(
        blank=True,
        help_text='Réponse de l\'agent/propriétaire'
    )
    response_date = models.DateTimeField(null=True, blank=True)
    response_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='review_responses',
        null=True,
        blank=True
    )
    
    # Helpful votes
    helpful_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', 'is_published']),
            models.Index(fields=['agent', 'is_published']),
            models.Index(fields=['author']),
            models.Index(fields=['-created_at']),
        ]
        # Un client ne peut laisser qu'un seul avis par réservation
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'reservation'],
                condition=models.Q(reservation__isnull=False),
                name='unique_review_per_reservation'
            )
        ]
    
    def __str__(self):
        return f"{self.review_type} - {self.rating}★ par {self.author.get_full_name()}"
    
    def publish(self, moderator=None):
        """Publish the review."""
        self.is_published = True
        self.moderated_at = timezone.now()
        if moderator:
            self.moderated_by = moderator
        self.save()
    
    def unpublish(self, moderator=None, reason=''):
        """Unpublish the review."""
        self.is_published = False
        self.moderated_at = timezone.now()
        if moderator:
            self.moderated_by = moderator
        if reason:
            self.moderation_notes = reason
        self.save()
    
    def add_response(self, response_text, responder):
        """Add agent/owner response."""
        self.response = response_text
        self.response_date = timezone.now()
        self.response_by = responder
        self.save()
    
    @_property
    def average_detailed_rating(self):
        """Calculate average of detailed ratings if available."""
        ratings = [
            r for r in [
                self.rating_communication,
                self.rating_professionalism,
                self.rating_value,
                self.rating_cleanliness,
                self.rating_location,
            ] if r is not None
        ]
        if ratings:
            return sum(ratings) / len(ratings)
        return self.rating


class ReviewHelpful(models.Model):
    """
    Model to track users who found a review helpful.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='helpful_votes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='helpful_review_votes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']
        indexes = [
            models.Index(fields=['review', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username} found review {self.review.id} helpful"
