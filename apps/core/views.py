"""
Views for core app.
"""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, permissions, viewsets, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import (
    Configuration, ActivityLog, Notification, 
    FileUpload, SystemStats, WebhookEvent
)
from .serializers import (
    ConfigurationSerializer, ActivityLogSerializer, 
    NotificationSerializer, FileUploadSerializer,
    SystemStatsSerializer
)
from .permissions import IsAdminOrReadOnly

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Liste des configurations",
        description="Retourne toutes les configurations système."
    ),
    retrieve=extend_schema(
        summary="Détail d'une configuration",
        description="Retourne les détails d'une configuration spécifique."
    ),
    create=extend_schema(
        summary="Création d'une configuration",
        description="Crée une nouvelle configuration système."
    ),
    update=extend_schema(
        summary="Mise à jour d'une configuration",
        description="Met à jour une configuration système."
    ),
    partial_update=extend_schema(
        summary="Mise à jour partielle d'une configuration",
        description="Met à jour partiellement une configuration."
    ),
    destroy=extend_schema(
        summary="Suppression d'une configuration",
        description="Supprime une configuration système."
    )
)
class ConfigurationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for system configurations.
    """
    
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    
    def get_queryset(self):
        """Return configurations based on permissions."""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Configuration.objects.all()
        else:
            return Configuration.objects.filter(is_public=True)
    
    def perform_create(self, serializer):
        """Create configuration with validation."""
        serializer.save()
    
    def perform_update(self, serializer):
        """Update configuration with validation."""
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """Get public configurations."""
        configs = Configuration.objects.filter(is_public=True)
        serializer = self.get_serializer(configs, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Liste des notifications",
        description="Retourne les notifications de l'utilisateur."
    ),
    retrieve=extend_schema(
        summary="Détail d'une notification",
        description="Retourne les détails d'une notification."
    ),
    create=extend_schema(
        summary="Création d'une notification",
        description="Crée une nouvelle notification (admin only)."
    )
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user notifications.
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return user's notifications."""
        user = self.request.user
        return Notification.objects.filter(
            Q(recipient_type='user', recipient_id=str(user.id)) |
            Q(recipient_type='all', is_active=True)
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response(
            {"message": "Notification marked as read."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all user notifications as read."""
        user = self.request.user
        updated = Notification.objects.filter(
            recipient_type='user', 
            recipient_id=str(user.id),
            read_at__isnull=True
        ).update(read_at=timezone.now())
        
        return Response(
            {"message": f"{updated} notifications marked as read."},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notifications count."""
        user = self.request.user
        count = Notification.objects.filter(
            recipient_type='user',
            recipient_id=str(user.id),
            read_at__isnull=True
        ).count()
        
        return Response({"unread_count": count})


@extend_schema_view(
    list=extend_schema(
        summary="Liste des logs d'activité",
        description="Retourne les logs d'activité système (admin only)."
    ),
    retrieve=extend_schema(
        summary="Détail d'un log",
        description="Retourne les détails d'un log d'activité."
    )
)
class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for activity logs (admin only).
    """
    
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return activity logs based on permissions."""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return ActivityLog.objects.all()
        else:
            return ActivityLog.objects.filter(user=user)
    
    def get_permissions(self):
        """Return appropriate permissions."""
        permission_classes = [IsAuthenticated]
        if self.action in ['list', 'retrieve']:
            permission_classes.append(IsAdminOrReadOnly)
        return [permission() for permission in permission_classes]


@extend_schema_view(
    list=extend_schema(
        summary="Liste des fichiers uploadés",
        description="Retourne les fichiers uploadés par l'utilisateur."
    ),
    retrieve=extend_schema(
        summary="Détail d'un fichier",
        description="Retourne les détails d'un fichier uploadé."
    )
)
class FileUploadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for file uploads.
    """
    
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return user's file uploads."""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return FileUpload.objects.all()
        else:
            return FileUpload.objects.filter(uploaded_by=user)


class FileUploadAPIView(APIView):
    """
    API endpoint for file uploads.
    """
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Upload de fichier",
        description="Upload un fichier vers le serveur."
    )
    def post(self, request):
        """Handle file upload."""
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_obj = request.FILES['file']
        
        # Create file upload record
        file_upload = FileUpload.objects.create(
            file=file_obj,
            original_name=file_obj.name,
            file_size=file_obj.size,
            mime_type=file_obj.content_type,
            uploaded_by=request.user,
            purpose=request.data.get('purpose', ''),
            metadata=request.data.get('metadata', {})
        )
        
        serializer = FileUploadSerializer(file_upload)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
@extend_schema(
    summary="Vérification de l'état du système",
    description="Vérifie l'état et la santé du système."
)
def health_check(request):
    """
    Health check endpoint for system monitoring.
    """
    try:
        # Basic system checks
        from django.db import connection
        
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Test Redis connection (if configured)
        redis_status = "unknown"
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            cached_value = cache.get('health_check')
            redis_status = "ok" if cached_value == "ok" else "error"
        except:
            redis_status = "error"
        
        # System status
        status_info = {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "database": "ok",
            "redis": redis_status,
            "version": "1.0.0",
            "environment": os.environ.get('DJANGO_ENV', 'development')
        }
        
        return Response(status_info, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@extend_schema(
    summary="Statistiques du système",
    description="Retourne les statistiques du système."
)
def system_stats(request):
    """
    Get system statistics.
    """
    try:
        User = get_user_model()
        
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        verified_users = User.objects.filter(is_verified=True).count()
        
        # Property statistics (if properties app is installed)
        try:
            from apps.properties.models import Property
            total_properties = Property.objects.count()
            available_properties = Property.objects.filter(status='available').count()
        except:
            total_properties = 0
            available_properties = 0
        
        # System info
        stats = {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users
            },
            "properties": {
                "total": total_properties,
                "available": available_properties
            },
            "system": {
                "uptime": "N/A",  # Could be implemented with psutil
                "database_size": "N/A",  # Could be implemented with database query
                "disk_usage": "N/A"  # Could be implemented with os.statvfs
            },
            "timestamp": timezone.now().isoformat()
        }
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
@extend_schema(
    summary="Version de l'API",
    description="Retourne les informations de version de l'API."
)
def api_version(request):
    """
    Get API version information.
    """
    version_info = {
        "api_version": "1.0.0",
        "django_version": django.get_version(),
        "framework_version": "Django REST Framework",
        "build_date": "2025-01-11",
        "environment": os.environ.get('DJANGO_ENV', 'development'),
        "documentation": "/api/docs/",
        "redoc": "/api/redoc/"
    }
    
    return Response(version_info, status=status.HTTP_200_OK)