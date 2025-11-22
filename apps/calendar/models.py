"""
Modèles pour le système de calendrier intelligent
Planification automatique des visites et gestion des disponibilités
"""

import uuid
import calendar
from datetime import datetime, date, time, timedelta
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()


class WorkingHours(models.Model):
    """Horaires de travail des agents"""
    
    DAY_CHOICES = [
        (0, 'Lundi'),
        (1, 'Mardi'),
        (2, 'Mercredi'),
        (3, 'Jeudi'),
        (4, 'Vendredi'),
        (5, 'Samedi'),
        (6, 'Dimanche'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='working_hours')
    
    # Jour de la semaine
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    
    # Horaires
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Est-ce que l'agent travaille ce jour ?
    is_working = models.BooleanField(default=True)
    
    # Pauses
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    
    # Statut
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'working_hours'
        unique_together = [
            ('user', 'day_of_week')
        ]
        ordering = ['user', 'day_of_week']

    def __str__(self):
        day_name = self.get_day_of_week_display()
        if self.is_working:
            return f"{self.user.get_full_name() or self.user.username} - {day_name}: {self.start_time}-{self.end_time}"
        return f"{self.user.get_full_name() or self.user.username} - {day_name} (Repos)"


class TimeSlot(models.Model):
    """Créneaux horaires disponibles"""
    
    STATUS_CHOICES = [
        ('available', 'Disponible'),
        ('booked', 'Réservé'),
        ('blocked', 'Bloqué'),
        ('holiday', 'Congé'),
        ('sick', 'Malade'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_slots')
    
    # Date et heure
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Réservation liée
    reservation = models.ForeignKey(
        'reservations.Reservation', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='time_slots'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'time_slot'
        unique_together = [
            ('user', 'date', 'start_time', 'end_time')
        ]
        ordering = ['date', 'start_time']
        indexes = [
            models.Index(fields=['user', 'date', 'status']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.date} {self.start_time}-{self.end_time} ({self.get_status_display()})"
    
    def is_available(self):
        """Vérifie si le créneau est disponible"""
        return self.status == 'available'
    
    def overlaps_with(self, other_slot):
        """Vérifie si ce créneau chevauche un autre"""
        return (self.date == other_slot.date and
                not (self.end_time <= other_slot.start_time or 
                     self.start_time >= other_slot.end_time))


class ClientAvailability(models.Model):
    """Disponibilités des clients"""
    
    PREFERENCE_CHOICES = [
        ('morning', 'Matin'),
        ('afternoon', 'Après-midi'),
        ('evening', 'Soirée'),
        ('any', 'Indifférent'),
    ]
    
    URGENCY_CHOICES = [
        ('low', 'Basse'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_availabilities')
    
    # Date de préférence
    preferred_date = models.DateField()
    
    # Créneau de préférence
    preferred_time_slot = models.CharField(max_length=20, choices=PREFERENCE_CHOICES)
    
    # Créneaux précis (optionnel)
    specific_start_time = models.TimeField(null=True, blank=True)
    specific_end_time = models.TimeField(null=True, blank=True)
    
    # Urgence
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='normal')
    
    # Durée préférée (en minutes)
    preferred_duration = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(15), MaxValueValidator(240)]
    )
    
    # Commentaires
    notes = models.TextField(blank=True)
    
    # Statut
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'client_availability'
        ordering = ['preferred_date', 'user']
        indexes = [
            models.Index(fields=['preferred_date', 'user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.preferred_date} ({self.get_preferred_time_slot_display()})"


class VisitSchedule(models.Model):
    """Planification de visite intelligente"""
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('scheduled', 'Planifiée'),
        ('confirmed', 'Confirmée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
        ('no_show', 'Absent'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Basse'),
        ('normal', 'Normale'),
        ('high', 'Haute'),
        ('urgent', 'Urgente'),
    ]
    
    MATCHING_ALGORITHMS = [
        ('first_available', 'Premier disponible'),
        ('best_match', 'Meilleure correspondance'),
        ('optimal_route', 'Route optimale'),
        ('load_balancing', 'Répartition de charge'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_visits')
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_agent_visits')
    property = models.ForeignKey(
        'properties.Property', 
        on_delete=models.CASCADE, 
        related_name='scheduled_visits'
    )
    reservation = models.OneToOneField(
        'reservations.Reservation',
        on_delete=models.CASCADE,
        related_name='schedule'
    )
    
    # Planification
    scheduled_date = models.DateField()
    scheduled_start_time = models.TimeField()
    scheduled_end_time = models.TimeField()
    
    # Algorithme utilisé
    matching_algorithm = models.CharField(
        max_length=20, 
        choices=MATCHING_ALGORITHMS,
        default='best_match'
    )
    
    # Statut et priorité
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Correspondance et score
    match_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    match_factors = models.JSONField(default=dict)  # Critères de correspondance
    
    # Localisation et voyage
    travel_time = models.PositiveIntegerField(null=True, blank=True, help_text="Temps de trajet en minutes")
    distance = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Distance en km")
    
    # Notes
    client_notes = models.TextField(blank=True)
    agent_notes = models.TextField(blank=True)
    system_notes = models.TextField(blank=True)
    
    # Confirmation
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='confirmed_schedules'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'visit_schedule'
        ordering = ['scheduled_date', 'scheduled_start_time']
        indexes = [
            models.Index(fields=['agent', 'scheduled_date', 'status']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['property', 'status']),
        ]

    def __str__(self):
        return f"{self.property.title} - {self.client.get_full_name() or self.client.username} - {self.scheduled_date} {self.scheduled_start_time}"
    
    def duration_minutes(self):
        """Retourne la durée en minutes"""
        start_dt = datetime.combine(date.today(), self.scheduled_start_time)
        end_dt = datetime.combine(date.today(), self.scheduled_end_time)
        return int((end_dt - start_dt).total_seconds() / 60)
    
    def is_past(self):
        """Vérifie si la visite est passée"""
        now = timezone.now()
        visit_datetime = datetime.combine(self.scheduled_date, self.scheduled_start_time)
        return visit_datetime < now
    
    def can_modify(self):
        """Vérifie si la visite peut être modifiée"""
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        now = timezone.now()
        visit_datetime = datetime.combine(self.scheduled_date, self.scheduled_start_time)
        
        # Peut modifier si c'est dans le futur et pas déjà confirmé
        return (visit_datetime > now and 
                self.status in ['pending', 'scheduled'])


class CalendarConflict(models.Model):
    """Conflits de calendrier détectés"""
    
    STATUS_CHOICES = [
        ('detected', 'Détecté'),
        ('resolved', 'Résolu'),
        ('ignored', 'Ignoré'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('critical', 'Critique'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Conflits
    schedule1 = models.ForeignKey(
        VisitSchedule,
        on_delete=models.CASCADE,
        related_name='conflicts_as_first'
    )
    schedule2 = models.ForeignKey(
        VisitSchedule,
        on_delete=models.CASCADE,
        related_name='conflicts_as_second'
    )
    
    # Détails
    conflict_type = models.CharField(max_length=50)  # 'time_overlap', 'double_booking', etc.
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField()
    
    # Résolution
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='detected')
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_conflicts'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calendar_conflict'
        unique_together = [
            ('schedule1', 'schedule2', 'conflict_type')
        ]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
        ]

    def __str__(self):
        return f"Conflit {self.get_severity_display()}: {self.schedule1} vs {self.schedule2}"


class SchedulingPreference(models.Model):
    """Préférences de planification des agents"""
    
    ROUTE_OPTIMIZATION_CHOICES = [
        ('none', 'Aucune'),
        ('distance', 'Par distance'),
        ('time', 'Par temps de trajet'),
        ('fuel', 'Économie de carburant'),
    ]
    
    CLIENT_PREFERENCE_CHOICES = [
        ('ignore', 'Ignorer'),
        ('consider', 'Considérer'),
        ('prioritize', 'Prioriser'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='scheduling_preferences')
    
    # Optimisation de route
    route_optimization = models.CharField(
        max_length=20,
        choices=ROUTE_OPTIMIZATION_CHOICES,
        default='time'
    )
    
    # Préférences client
    client_preference_handling = models.CharField(
        max_length=20,
        choices=CLIENT_PREFERENCE_CHOICES,
        default='consider'
    )
    
    # Configuration
    max_daily_visits = models.PositiveIntegerField(default=8)
    min_break_minutes = models.PositiveIntegerField(default=30)
    travel_time_buffer = models.PositiveIntegerField(default=15, help_text="Minutes de marge pour les trajets")
    
    # Zone géographique
    working_radius = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Rayon de travail en km"
    )
    preferred_areas = models.JSONField(
        default=list,
        help_text="Zones de travail préférées (codes postaux, villes)"
    )
    
    # Types de propriétés
    preferred_property_types = models.JSONField(
        default=list,
        help_text="Types de propriétés préférées"
    )
    
    # Statut
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scheduling_preference'

    def __str__(self):
        return f"Préférences de {self.user.get_full_name() or self.user.username}"


class ScheduleMetrics(models.Model):
    """Métriques de planification"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedule_metrics')
    
    # Métriques
    total_scheduled_visits = models.PositiveIntegerField(default=0)
    completed_visits = models.PositiveIntegerField(default=0)
    cancelled_visits = models.PositiveIntegerField(default=0)
    no_show_visits = models.PositiveIntegerField(default=0)
    
    # Performance
    average_match_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_travel_time = models.PositiveIntegerField(default=0, help_text="Minutes")
    total_distance = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="km")
    
    # Efficacité
    optimization_savings = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Minutes économisées")
    efficiency_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schedule_metrics'
        unique_together = [
            ('date', 'agent')
        ]
        ordering = ['-date']

    def __str__(self):
        return f"Métriques {self.agent.get_full_name() or self.agent.username} - {self.date}"