"""
Views for reviews management API.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Avg, Count, Case, When, IntegerField
from django.utils import timezone

from .models import Review, ReviewHelpful
from .serializers import (
    ReviewSerializer, ReviewCreateSerializer, ReviewResponseSerializer,
    ReviewModerationSerializer, PropertyReviewSummarySerializer,
    AgentReviewSummarySerializer
)
from .permissions import (
    IsReviewAuthorOrReadOnly, CanModerateReviews, CanRespondToReview,
    CanCreateReview, CanVoteHelpful
)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    """
    
    queryset = Review.objects.select_related(
        'author', 'property', 'agent', 'reservation', 'moderated_by', 'response_by'
    ).prefetch_related('helpful_votes')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'review_type': ['exact'],
        'property': ['exact'],
        'agent': ['exact'],
        'reservation': ['exact'],
        'rating': ['exact', 'gte', 'lte'],
        'is_published': ['exact'],
        'is_verified': ['exact'],
    }
    search_fields = ['title', 'comment', 'author__first_name', 'author__last_name']
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return ReviewCreateSerializer
        elif self.action == 'respond':
            return ReviewResponseSerializer
        elif self.action == 'moderate':
            return ReviewModerationSerializer
        return ReviewSerializer
    
    def get_permissions(self):
        """Get permissions based on action."""
        if self.action in ['list', 'retrieve']:
            # Anyone can view published reviews
            permission_classes = [AllowAny]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated, CanCreateReview]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsReviewAuthorOrReadOnly]
        elif self.action == 'moderate':
            permission_classes = [IsAuthenticated, CanModerateReviews]
        elif self.action == 'respond':
            permission_classes = [IsAuthenticated, CanRespondToReview]
        elif self.action in ['vote_helpful', 'unvote_helpful']:
            permission_classes = [IsAuthenticated, CanVoteHelpful]
        elif self.action in ['my_reviews', 'pending_moderation']:
            permission_classes = [IsAuthenticated]
        elif self.action in ['property_summary', 'agent_summary']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Get filtered queryset based on user permissions."""
        user = self.request.user
        queryset = super().get_queryset()
        
        # For list action, only show published reviews or user's own reviews
        if self.action == 'list':
            if user.is_authenticated:
                if user.is_staff or user.is_superuser or user.role in ['agent', 'manager']:
                    # Staff/agents can see all reviews
                    return queryset
                else:
                    # Clients see published reviews or their own
                    return queryset.filter(Q(is_published=True) | Q(author=user))
            else:
                # Anonymous users see only published reviews
                return queryset.filter(is_published=True)
        
        # For retrieve, staff and author can see unpublished
        if self.action == 'retrieve':
            if user.is_authenticated:
                if user.is_staff or user.is_superuser:
                    return queryset
                else:
                    return queryset.filter(Q(is_published=True) | Q(author=user))
            else:
                return queryset.filter(is_published=True)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's reviews."""
        reviews = self.get_queryset().filter(author=request.user)
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanModerateReviews])
    def pending_moderation(self, request):
        """Get reviews pending moderation."""
        reviews = Review.objects.filter(
            is_published=False,
            moderated_at__isnull=True
        ).select_related('author', 'property', 'agent')
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Add agent/owner response to review."""
        review = self.get_object()
        serializer = ReviewResponseSerializer(data=request.data)
        
        if serializer.is_valid():
            review.add_response(
                response_text=serializer.validated_data['response'],
                responder=request.user
            )
            return Response(
                ReviewSerializer(review, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def moderate(self, request, pk=None):
        """Moderate a review (publish/unpublish)."""
        review = self.get_object()
        serializer = ReviewModerationSerializer(data=request.data)
        
        if serializer.is_valid():
            if serializer.validated_data['is_published']:
                review.publish(moderator=request.user)
            else:
                review.unpublish(
                    moderator=request.user,
                    reason=serializer.validated_data.get('moderation_notes', '')
                )
            return Response(
                ReviewSerializer(review, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def vote_helpful(self, request, pk=None):
        """Vote review as helpful."""
        review = self.get_object()
        
        # Check if user already voted
        if ReviewHelpful.objects.filter(review=review, user=request.user).exists():
            return Response(
                {'error': 'Vous avez déjà voté pour cet avis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create vote
        ReviewHelpful.objects.create(review=review, user=request.user)
        review.helpful_count += 1
        review.save(update_fields=['helpful_count'])
        
        return Response(
            ReviewSerializer(review, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unvote_helpful(self, request, pk=None):
        """Remove helpful vote from review."""
        review = self.get_object()
        
        vote = ReviewHelpful.objects.filter(review=review, user=request.user).first()
        if not vote:
            return Response(
                {'error': 'Vous n\'avez pas voté pour cet avis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        vote.delete()
        review.helpful_count = max(0, review.helpful_count - 1)
        review.save(update_fields=['helpful_count'])
        
        return Response(
            ReviewSerializer(review, context={'request': request}).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='property-summary/(?P<property_id>[^/.]+)')
    def property_summary(self, request, property_id=None):
        """Get review summary for a property."""
        reviews = Review.objects.filter(
            property_id=property_id,
            is_published=True
        )
        
        total_reviews = reviews.count()
        if total_reviews == 0:
            return Response({
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {},
                'verified_reviews_count': 0,
            })
        
        # Calculate statistics
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        verified_count = reviews.filter(is_verified=True).count()
        
        # Rating distribution
        rating_dist = {}
        for i in range(1, 6):
            rating_dist[str(i)] = reviews.filter(rating=i).count()
        
        # Detailed ratings averages
        avg_communication = reviews.aggregate(Avg('rating_communication'))['rating_communication__avg']
        avg_professionalism = reviews.aggregate(Avg('rating_professionalism'))['rating_professionalism__avg']
        avg_value = reviews.aggregate(Avg('rating_value'))['rating_value__avg']
        avg_cleanliness = reviews.aggregate(Avg('rating_cleanliness'))['rating_cleanliness__avg']
        avg_location = reviews.aggregate(Avg('rating_location'))['rating_location__avg']
        
        summary = {
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 2),
            'rating_distribution': rating_dist,
            'verified_reviews_count': verified_count,
            'average_communication': round(avg_communication, 2) if avg_communication else None,
            'average_professionalism': round(avg_professionalism, 2) if avg_professionalism else None,
            'average_value': round(avg_value, 2) if avg_value else None,
            'average_cleanliness': round(avg_cleanliness, 2) if avg_cleanliness else None,
            'average_location': round(avg_location, 2) if avg_location else None,
        }
        
        serializer = PropertyReviewSummarySerializer(summary)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='agent-summary/(?P<agent_id>[^/.]+)')
    def agent_summary(self, request, agent_id=None):
        """Get review summary for an agent."""
        reviews = Review.objects.filter(
            agent_id=agent_id,
            is_published=True
        )
        
        total_reviews = reviews.count()
        if total_reviews == 0:
            return Response({
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {},
                'verified_reviews_count': 0,
            })
        
        # Calculate statistics
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        verified_count = reviews.filter(is_verified=True).count()
        
        # Rating distribution
        rating_dist = {}
        for i in range(1, 6):
            rating_dist[str(i)] = reviews.filter(rating=i).count()
        
        # Detailed ratings averages
        avg_communication = reviews.aggregate(Avg('rating_communication'))['rating_communication__avg']
        avg_professionalism = reviews.aggregate(Avg('rating_professionalism'))['rating_professionalism__avg']
        
        summary = {
            'total_reviews': total_reviews,
            'average_rating': round(avg_rating, 2),
            'rating_distribution': rating_dist,
            'verified_reviews_count': verified_count,
            'average_communication': round(avg_communication, 2) if avg_communication else None,
            'average_professionalism': round(avg_professionalism, 2) if avg_professionalism else None,
        }
        
        serializer = AgentReviewSummarySerializer(summary)
        return Response(serializer.data)
