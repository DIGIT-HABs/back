"""
Serializers for favorites management.
"""

from rest_framework import serializers
from apps.properties.serializers import PropertyListSerializer
from .models import Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for Favorite model."""
    
    property_details = PropertyListSerializer(source='property', read_only=True)
    
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'property', 'property_details', 'created_at']
        read_only_fields = ['id', 'user', 'property_details', 'created_at']


class FavoriteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating favorites."""
    
    property_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Favorite
        fields = ['property_id']
    
    def validate_property_id(self, value):
        """Validate that the property exists."""
        from apps.properties.models import Property
        try:
            Property.objects.get(id=value)
        except Property.DoesNotExist:
            raise serializers.ValidationError("La propriété spécifiée n'existe pas.")
        return value
    
    def create(self, validated_data):
        """Create a favorite."""
        from apps.properties.models import Property
        property_id = validated_data.pop('property_id')
        property_instance = Property.objects.get(id=property_id)
        
        favorite, created = Favorite.objects.get_or_create(
            user=self.context['request'].user,
            property=property_instance
        )
        
        return favorite

