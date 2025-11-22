"""
Models for properties management.
"""

import uuid
from django.db import models
# from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.auth.models import User, Agency


class Property(models.Model):
    """Property model for real estate listings."""
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Property Type & Status
    property_type = models.CharField(
        max_length=20,
        choices=[
            ('apartment', 'Appartement'),
            ('house', 'Maison'),
            ('villa', 'Villa'),
            ('penthouse', 'Penthouse'),
            ('loft', 'Loft'),
            ('duplex', 'Duplex'),
            ('triplex', 'Triplex'),
            ('studio', 'Studio'),
            ('commercial', 'Commercial'),
            ('office', 'Bureau'),
            ('land', 'Terrain'),
            ('parking', 'Parking'),
            ('cellar', 'Cave'),
            ('garage', 'Garage'),
        ],
        default='apartment'
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Brouillon'),
            ('available', 'Disponible'),
            ('under_offer', 'Sous offre'),
            ('reserved', 'Réservé'),
            ('sold', 'Vendu'),
            ('rented', 'Loué'),
            ('withdrawn', 'Retiré'),
            ('archived', 'Archivé'),
        ],
        default='draft'
    )
    
    # Location
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Sénégal')
    
    # Coordinates (PostGIS)
    # location = gis_models.PointField(null=True, blank=True, srid=4326)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=8, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True
    )
    
    # Financial Information
    price = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    price_per_sqm = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(0)], null=True, blank=True
    )
    
    # Property Details
    surface_area = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    usable_area = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0)], null=True, blank=True
    )
    garden_area = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(0)], null=True, blank=True
    )
    
    # Rooms
    rooms = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    bedrooms = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    bathrooms = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    toilets = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], default=1
    )
    
    # Additional Features
    floor = models.CharField(max_length=50, blank=True)
    total_floors = models.PositiveIntegerField(null=True, blank=True)
    year_built = models.PositiveIntegerField(
        validators=[MinValueValidator(1800), MaxValueValidator(2025)],
        null=True, blank=True
    )
    
    # Energy & Environment
    energy_class = models.CharField(
        max_length=5,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
            ('E', 'E'),
            ('F', 'F'),
            ('G', 'G'),
        ],
        null=True, blank=True
    )
    ges_class = models.CharField(
        max_length=5,
        choices=[
            ('A', 'A'),
            ('B', 'B'),
            ('C', 'C'),
            ('D', 'D'),
            ('E', 'E'),
            ('F', 'F'),
            ('G', 'G'),
        ],
        null=True, blank=True
    )
    
    heating_type = models.CharField(
        max_length=50,
        choices=[
            ('gas', 'Gaz'),
            ('electric', 'Électrique'),
            ('oil', 'Fioul'),
            ('wood', 'Bois'),
            ('heat_pump', 'Pompe à chaleur'),
            ('district', 'Chauffage urbain'),
            ('solar', 'Solaire'),
        ],
        blank=True
    )
    
    # Features
    has_balcony = models.BooleanField(default=False)
    has_terrace = models.BooleanField(default=False)
    has_garden = models.BooleanField(default=False)
    has_garage = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    has_elevator = models.BooleanField(default=False)
    has_fireplace = models.BooleanField(default=False)
    has_pool = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=False)
    has_security_system = models.BooleanField(default=False)
    
    # Furnishing
    furnished = models.BooleanField(default=False)
    furnished_level = models.CharField(
        max_length=20,
        choices=[
            ('none', 'Non meublé'),
            ('partially', 'Partiellement meublé'),
            ('fully', 'Entièrement meublé'),
        ],
        default='none'
    )
    
    # Available From
    available_from = models.DateField(null=True, blank=True)
    
    # Owner Information
    owner_name = models.CharField(max_length=200, blank=True)
    owner_phone = models.CharField(max_length=20, blank=True)
    owner_email = models.EmailField(blank=True)
    
    # Agency & Agent
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='properties')
    agent = models.ForeignKey(
        User, on_delete=models.SET_NULL, 
        related_name='assigned_properties',
        null=True, blank=True
    )
    
    # Features & Amenities
    amenities = models.JSONField(default=dict, blank=True)
    additional_features = models.JSONField(default=dict, blank=True)
    
    # SEO & Marketing
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=500, blank=True)
    featured_image = models.ImageField(upload_to='properties/featured/', null=True, blank=True)
    
    # Settings
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    show_price = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    inquiry_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'properties'
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property_type', 'status']),
            models.Index(fields=['city', 'postal_code']),
            models.Index(fields=['price']),
            models.Index(fields=['surface_area']),
            models.Index(fields=['is_featured', 'status']),
            models.Index(fields=['published_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.city}"
    
    def save(self, *args, **kwargs):
        """Override save to calculate price per sqm and coordinates."""
        # Calculate price per square meter
        if self.surface_area and self.surface_area > 0:
            self.price_per_sqm = self.price / self.surface_area
        
        # Set coordinates from latitude/longitude
        # if self.latitude and self.longitude:
        #     from django.contrib.gis.geos import Point
        #     self.location = Point(self.longitude, self.latitude)
        
        # Set published date if status changes to available
        if self.status == 'available' and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_full_address(self):
        """Get full address as string."""
        address = f"{self.address_line1}"
        if self.address_line2:
            address += f", {self.address_line2}"
        address += f", {self.postal_code} {self.city}"
        if self.country != 'Sénégal':
            address += f", {self.country}"
        return address
    
    def get_absolute_url(self):
        """Get absolute URL for the property."""
        from django.urls import reverse
        return reverse('property_detail', kwargs={'pk': self.id})
    
    def can_be_edited_by(self, user):
        """Check if property can be edited by user."""
        if user.is_staff or user.is_superuser:
            return True
        return self.agent == user or self.agency == getattr(user.profile, 'agency', None)
    
    def can_be_viewed_by(self, user):
        """Check if property can be viewed by user."""
        if self.is_public:
            return True
        return self.can_be_edited_by(user)
    
    def increment_view_count(self):
        """Increment view count."""
        Property.objects.filter(pk=self.pk).update(view_count=models.F('view_count') + 1)
    
    def increment_inquiry_count(self):
        """Increment inquiry count."""
        Property.objects.filter(pk=self.pk).update(inquiry_count=models.F('inquiry_count') + 1)


class PropertyImage(models.Model):
    """Property images model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='properties/images/')
    thumbnail = models.ImageField(upload_to='properties/thumbnails/', null=True, blank=True)
    
    # Image Details
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(max_length=500, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    
    # Ordering
    order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    
    # Metadata
    file_size = models.PositiveIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_images'
        verbose_name = 'Property Image'
        verbose_name_plural = 'Property Images'
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['property', 'order']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.property.title} - Image {self.order + 1}"


class PropertyDocument(models.Model):
    """Property documents model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='documents')
    
    # Document Details
    title = models.CharField(max_length=200)
    document_type = models.CharField(
        max_length=20,
        choices=[
            ('floor_plan', 'Plan de l\'étage'),
            ('certificate', 'Certificat'),
            ('deed', 'Acte de propriété'),
            ('diagnosis', 'Diagnostic'),
            ('insurance', 'Assurance'),
            ('contract', 'Contrat'),
            ('photo', 'Photo'),
            ('other', 'Autre'),
        ]
    )
    
    document_file = models.FileField(upload_to='properties/documents/')
    
    # Permissions
    is_public = models.BooleanField(
        default=False, 
        help_text="Disponible publiquement"
    )
    requires_auth = models.BooleanField(
        default=True,
        help_text="Nécessite une authentification pour accéder"
    )
    
    # Metadata
    file_size = models.PositiveIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_documents'
        verbose_name = 'Property Document'
        verbose_name_plural = 'Property Documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', 'document_type']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.property.title} - {self.title}"


class PropertyVisit(models.Model):
    """Property visits model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='visits')
    
    # Client who requested the visit
    client = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='client_visits',
        help_text='Client who requested the visit'
    )
    
    # Visit Details
    visit_type = models.CharField(
        max_length=20,
        choices=[
            ('individual', 'Individuelle'),
            ('group', 'Groupe'),
            ('virtual', 'Virtuelle'),
            ('self_visit', 'Visite libre'),
        ],
        default='individual'
    )
    
    scheduled_date = models.DateTimeField(help_text='Date et heure de la visite')
    duration_minutes = models.PositiveIntegerField(default=60)
    
    # Visitor Information (legacy fields for backward compatibility)
    visitor_name = models.CharField(max_length=200, blank=True)
    visitor_email = models.EmailField(blank=True)
    visitor_phone = models.CharField(max_length=20, blank=True)
    visitor_count = models.PositiveIntegerField(default=1)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', 'Programmée'),
            ('confirmed', 'Confirmée'),
            ('completed', 'Terminée'),
            ('cancelled', 'Annulée'),
            ('no_show', 'Absent'),
        ],
        default='scheduled'
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text='Notes du client')
    visitor_notes = models.TextField(blank=True)
    agent_notes = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )
    
    # Agent
    agent = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        related_name='agent_visits',
        null=True, blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'property_visits'
        verbose_name = 'Property Visit'
        verbose_name_plural = 'Property Visits'
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['property', 'scheduled_date']),
            models.Index(fields=['client']),
            models.Index(fields=['status']),
            models.Index(fields=['agent']),
        ]
    
    def __str__(self):
        return f"{self.property.title} - {self.scheduled_date}"
    
    def confirm_visit(self):
        """Confirm the visit."""
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()
    
    def complete_visit(self):
        """Mark visit as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()


class PropertyHistory(models.Model):
    """Property history/audit model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='history')
    
    # Change Details
    action = models.CharField(
        max_length=20,
        choices=[
            ('created', 'Créé'),
            ('updated', 'Modifié'),
            ('status_changed', 'Statut modifié'),
            ('price_changed', 'Prix modifié'),
            ('published', 'Publié'),
            ('archived', 'Archivé'),
            ('deleted', 'Supprimé'),
        ]
    )
    
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    
    # Change Metadata
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_reason = models.CharField(max_length=500, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'property_history'
        verbose_name = 'Property History'
        verbose_name_plural = 'Property History'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', 'created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['changed_by']),
        ]
    
    def __str__(self):
        return f"{self.property.title} - {self.action} - {self.created_at}"


class PropertySearch(models.Model):
    """Saved property searches model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_searches')
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='property_searches')
    
    # Search Details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Search Criteria
    search_criteria = models.JSONField(default=dict)
    
    # Settings
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immédiat'),
            ('daily', 'Quotidien'),
            ('weekly', 'Hebdomadaire'),
        ],
        default='daily'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'property_searches'
        verbose_name = 'Property Search'
        verbose_name_plural = 'Property Searches'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['agency']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.name}"