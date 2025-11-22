"""
Views for favorites management.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.properties.models import Property
from .models import Favorite
from .serializers import FavoriteSerializer, FavoriteCreateSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user favorites.
    """
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get favorites for the current user."""
        return Favorite.objects.filter(user=self.request.user).select_related('property', 'property__agent')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return FavoriteCreateSerializer
        return FavoriteSerializer
    
    def create(self, request, *args, **kwargs):
        """Add a property to favorites."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        favorite = serializer.save()
        
        # Return full favorite with property details
        return_serializer = FavoriteSerializer(favorite)
        return Response(return_serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """Remove a property from favorites."""
        # Support both favorite ID and property ID for deletion
        pk = kwargs.get('pk')
        
        # Try to find by favorite ID first
        try:
            favorite = Favorite.objects.get(id=pk, user=request.user)
        except Favorite.DoesNotExist:
            # Try to find by property ID
            try:
                favorite = Favorite.objects.get(property_id=pk, user=request.user)
            except Favorite.DoesNotExist:
                return Response(
                    {'error': 'Favori non trouvé.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], url_path='toggle/(?P<property_id>[^/.]+)')
    def toggle(self, request, property_id=None):
        """Toggle favorite status for a property."""
        property_instance = get_object_or_404(Property, id=property_id)
        
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            property=property_instance
        )
        
        if not created:
            # Favorite already exists, remove it
            favorite.delete()
            return Response({'status': 'removed'}, status=status.HTTP_200_OK)
        else:
            # Favorite created
            serializer = FavoriteSerializer(favorite)
            return Response({'status': 'added', 'favorite': serializer.data}, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """Check if a property is favorited by the user."""
        property_id = request.query_params.get('property_id')
        
        if not property_id:
            return Response(
                {'error': 'property_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_favorite = Favorite.objects.filter(
            user=request.user,
            property_id=property_id
        ).exists()
        
        return Response({'is_favorite': is_favorite})

