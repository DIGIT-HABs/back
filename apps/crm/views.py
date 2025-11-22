"""
Views for CRM (Client Relationship Management).
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum
from django.core.cache import cache

from apps.auth.models import User
from apps.properties.models import Property
from .models import ClientProfile, PropertyInterest, ClientInteraction, Lead
from .serializers import (
    ClientProfileSerializer, PropertyInterestSerializer, ClientInteractionSerializer,
    LeadSerializer, LeadConversionSerializer, PropertyMatchSerializer,
    ClientDashboardSerializer, AgentDashboardSerializer
)
from .permissions import (
    IsClientOrOwner, IsAgentOrAdmin, CanManageClientProfile, CanManageLeads,
    CanCreateLead, CanAssignLeads, CanAccessPropertyInterests, CanManageInteractions,
    CanCreateInteraction, CanAccessMatchingResults, CanViewDashboard, CanConvertLead
)
from .matching import PropertyMatcher, LeadMatcher, auto_match_properties_for_client, auto_assign_leads_to_agents


class ClientProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing client profiles.
    """
    queryset = ClientProfile.objects.select_related('user')
    serializer_class = ClientProfileSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageClientProfile]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'priority_level': ['exact'],
        'financing_status': ['exact'],
        'conversion_score': ['gte', 'lte']
    }
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['conversion_score', 'created_at', 'updated_at', 'total_properties_viewed']
    ordering = ['-conversion_score']
    
    def get_queryset(self):
        """Filter queryset based on user role and permissions."""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'admin':
            # Admin can see all client profiles
            return queryset
        elif user.role == 'agent':
            # Agent can see profiles for their agency's clients
            return queryset.filter(user__profile__agency=user.agency)
        elif user.role == 'client':
            # Client can only see their own profile
            return queryset.filter(user=user)
        
        return queryset.none()
    
    def get_permissions(self):
        """Get permissions for different actions."""
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, IsAgentOrAdmin]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, CanManageClientProfile]
        else:
            permission_classes = [permissions.IsAuthenticated, CanViewDashboard]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def matching_properties(self, request, pk=None):
        """Get matching properties for a client profile."""
        try:
            client_profile = self.get_object()
            matcher = PropertyMatcher(client_profile)
            properties = matcher.find_matches(limit=10)
            
            # Add match scores to properties
            properties_with_scores = []
            for prop in properties:
                score = matcher.calculate_match_score(prop)
                properties_with_scores.append({
                    'property': prop,
                    'match_score': score,
                    'match_explanation': matcher.get_match_explanation(prop)
                })
            
            results = []
            for prop_data in properties_with_scores:
                prop_serializer = self.get_serializer().Meta.model.__bases__[0].__dict__['Meta'].model
                property_data = {
                    'property': prop_data['property'],
                    'match_score': prop_data['match_score'],
                    'match_explanation': prop_data['match_explanation'],
                    'recommendations': prop_data['match_explanation']['recommendations']
                }
                results.append(property_data)
            
            return Response(results)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_activity(self, request, pk=None):
        """Update client activity statistics."""
        try:
            client_profile = self.get_object()
            client_profile.update_activity()
            
            return Response({
                'total_properties_viewed': client_profile.total_properties_viewed,
                'total_inquiries_made': client_profile.total_inquiries_made,
                'conversion_score': client_profile.conversion_score
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def dashboard(self, request, pk=None):
        """Get client dashboard data."""
        try:
            client_profile = self.get_object()
            client_user = client_profile.user
            
            # Get recent interactions
            recent_interactions = ClientInteraction.objects.filter(
                client=client_user
            ).order_by('-created_at')[:5]
            
            # Get upcoming visits
            upcoming_visits = PropertyInterest.objects.filter(
                client=client_user,
                interaction_type='visit_scheduled',
                status='active'
            ).order_by('interaction_date')[:5]
            
            # Get matching properties
            matching_properties = client_profile.get_matching_properties(limit=5)
            
            # Activity summary
            activity_summary = {
                'total_interests': client_profile.total_properties_viewed,
                'total_inquiries': client_profile.total_inquiries_made,
                'conversion_score': client_profile.conversion_score,
                'last_activity': client_profile.last_property_view
            }
            
            dashboard_data = {
                'profile': ClientProfileSerializer(client_profile).data,
                'recent_interactions': ClientInteractionSerializer(recent_interactions, many=True).data,
                'upcoming_visits': PropertyInterestSerializer(upcoming_visits, many=True).data,
                'matching_properties': matching_properties,
                'activity_summary': activity_summary
            }
            
            return Response(dashboard_data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PropertyInterestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing property interests.
    """
    queryset = PropertyInterest.objects.select_related('client', 'property')
    serializer_class = PropertyInterestSerializer
    permission_classes = [permissions.IsAuthenticated, CanAccessPropertyInterests]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'client': ['exact'],
        'property': ['exact'],
        'interaction_type': ['exact'],
        'interest_level': ['exact'],
        'status': ['exact'],
        'match_score': ['gte', 'lte']
    }
    search_fields = ['client__username', 'client__email', 'property__title']
    ordering_fields = ['match_score', 'interaction_date', 'created_at']
    ordering = ['-interaction_date']
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'client':
            return queryset.filter(client=user)
        elif user.role == 'agent':
            return queryset.filter(client__profile__agency=user.agency)
        # Admin sees all
        
        return queryset
    
    def perform_create(self, serializer):
        """Create property interest with proper permissions."""
        client_id = self.request.data.get('client_id')
        property_id = self.request.data.get('property_id')
        
        # Validate client and property
        try:
            client = User.objects.get(id=client_id, role='client')
            property_obj = Property.objects.get(id=property_id)
        except (User.DoesNotExist, Property.DoesNotExist):
            raise serializers.ValidationError("Client ou propriété introuvable.")
        
        # Create interest
        interest = PropertyInterest.create_from_interaction(
            client=client,
            property_obj=property_obj,
            interaction_type=self.request.data.get('interaction_type', 'view'),
            notes=self.request.data.get('notes', '')
        )
        
        return interest
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def track_interaction(self, request):
        """Track a new client interaction with a property."""
        client_id = request.data.get('client_id')
        property_id = request.data.get('property_id')
        interaction_type = request.data.get('interaction_type', 'view')
        notes = request.data.get('notes', '')
        
        try:
            client = User.objects.get(id=client_id, role='client')
            property_obj = Property.objects.get(id=property_id)
        except (User.DoesNotExist, Property.DoesNotExist):
            return Response(
                {'error': 'Client ou propriété introuvable.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update interest
        interest = PropertyInterest.create_from_interaction(
            client=client,
            property_obj=property_obj,
            interaction_type=interaction_type,
            notes=notes
        )
        
        serializer = self.get_serializer(interest)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def client_interests(self, request, pk=None):
        """Get all interests for a specific client."""
        try:
            client = User.objects.get(id=pk, role='client')
            
            # Check permissions
            if not CanAccessPropertyInterests().has_object_permission(request, self, client):
                return Response(
                    {'error': 'Accès non autorisé.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            interests = PropertyInterest.objects.filter(client=client).order_by('-interaction_date')
            serializer = self.get_serializer(interests, many=True)
            
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Client introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )


class ClientInteractionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing client interactions.
    """
    queryset = ClientInteraction.objects.select_related('client', 'agent', 'content_type')
    serializer_class = ClientInteractionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageInteractions]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'client': ['exact'],
        'agent': ['exact'],
        'interaction_type': ['exact'],
        'channel': ['exact'],
        'priority': ['exact'],
        'status': ['exact'],
        'scheduled_date': ['gte', 'lte'],
        'requires_follow_up': ['exact']
    }
    search_fields = ['client__username', 'client__email', 'agent__username', 'subject', 'content']
    ordering_fields = ['scheduled_date', 'created_at', 'priority']
    ordering = ['-scheduled_date']
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'client':
            return queryset.filter(client=user)
        elif user.role == 'agent':
            return queryset.filter(Q(agent=user) | Q(client__profile__agency=user.agency))
        # Admin sees all
        
        return queryset
    
    def perform_create(self, serializer):
        """Create interaction with proper agent assignment."""
        client_id = self.request.data.get('client_id')
        agent_id = self.request.data.get('agent_id')
        
        # Validate client and agent
        try:
            client = User.objects.get(id=client_id, role='client')
            agent = User.objects.get(id=agent_id, role='agent')
        except User.DoesNotExist:
            raise serializers.ValidationError("Client ou agent introuvable.")
        
        # Ensure agent is from same agency
        if client.agency != agent.agency:
            raise serializers.ValidationError("L'agent doit appartenir à la même agence que le client.")
        
        return ClientInteraction.objects.create(
            client=client, agent=agent, **serializer.validated_data
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def complete(self, request, pk=None):
        """Mark interaction as completed with outcome."""
        try:
            interaction = self.get_object()
            outcome = request.data.get('outcome')
            notes = request.data.get('notes', '')
            
            if not outcome:
                return Response(
                    {'error': 'Le résultat est requis.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            interaction.complete_interaction(outcome, notes)
            
            serializer = self.get_serializer(interaction)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def schedule_follow_up(self, request, pk=None):
        """Schedule a follow-up interaction."""
        try:
            interaction = self.get_object()
            follow_up_date = request.data.get('follow_up_date')
            notes = request.data.get('notes', '')
            
            if not follow_up_date:
                return Response(
                    {'error': 'La date de suivi est requise.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            interaction.schedule_follow_up(follow_up_date, notes)
            
            serializer = self.get_serializer(interaction)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leads.
    """
    queryset = Lead.objects.select_related('assigned_agent', 'agency')
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageLeads]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'source': ['exact'],
        'status': ['exact'],
        'qualification': ['exact'],
        'agency': ['exact'],
        'assigned_agent': ['exact'],
        'score': ['gte', 'lte'],
        'created_at': ['gte', 'lte']
    }
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'company']
    ordering_fields = ['score', 'urgency_score', 'created_at', 'next_action_date']
    ordering = ['-score', '-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user role and permissions."""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'admin':
            # Admin can see all leads
            return queryset
        elif user.role == 'agent':
            # Agent can see leads for their agency
            return queryset.filter(agency=user.agency)
        
        return queryset.none()
    
    def get_permissions(self):
        """Get permissions for different actions."""
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, CanCreateLead]
        elif self.action == 'assign':
            permission_classes = [permissions.IsAuthenticated, CanAssignLeads]
        elif self.action == 'convert':
            permission_classes = [permissions.IsAuthenticated, CanConvertLead]
        else:
            permission_classes = [permissions.IsAuthenticated, CanManageLeads]
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """Create lead and calculate initial score."""
        agency_id = self.request.data.get('agency_id')
        agency = Agency.objects.get(id=agency_id)
        
        lead = serializer.save(agency=agency)
        lead.calculate_score()
        lead.save()
        
        return lead
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, CanAssignLeads])
    def assign(self, request, pk=None):
        """Assign lead to an agent."""
        try:
            lead = self.get_object()
            agent_id = request.data.get('agent_id')
            
            if not agent_id:
                return Response(
                    {'error': 'ID agent requis.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                agent = User.objects.get(id=agent_id, role='agent')
            except User.DoesNotExist:
                return Response(
                    {'error': 'Agent introuvable.'},
                    status=status.HTTP_400_BAD_REQUEST
            )
            
            lead.assign_to_agent(agent)
            
            serializer = self.get_serializer(lead)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, CanConvertLead])
    def convert(self, request, pk=None):
        """Convert lead to client."""
        try:
            lead = self.get_object()
            serializer = LeadConversionSerializer(lead, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, CanManageLeads])
    def auto_assign(self, request):
        """Automatically assign unassigned leads to agents."""
        try:
            agency_id = request.data.get('agency_id')
            if not agency_id:
                return Response(
                    {'error': 'ID agence requis.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            agency = Agency.objects.get(id=agency_id)
            assigned_count = auto_assign_leads_to_agents(agency)
            
            return Response({
                'message': f'{assigned_count} leads assignés automatiquement.',
                'assigned_count': assigned_count
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, CanViewDashboard])
    def statistics(self, request):
        """Get lead statistics."""
        queryset = self.get_queryset()
        
        stats = {
            'total_leads': queryset.count(),
            'by_status': dict(queryset.values_list('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_source': dict(queryset.values_list('source').annotate(count=Count('id')).values_list('source', 'count')),
            'by_qualification': dict(queryset.values_list('qualification').annotate(count=Count('id')).values_list('qualification', 'count')),
            'avg_score': queryset.aggregate(avg_score=Avg('score'))['avg_score'] or 0,
            'conversion_rate': 0  # Calculate based on won leads
        }
        
        # Calculate conversion rate
        won_leads = queryset.filter(status='won').count()
        if queryset.count() > 0:
            stats['conversion_rate'] = (won_leads / queryset.count()) * 100
        
        return Response(stats)


class PropertyMatchingViewSet(viewsets.ViewSet):
    """
    ViewSet for property matching operations.
    """
    permission_classes = [permissions.IsAuthenticated, CanAccessMatchingResults]
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def find_matches(self, request):
        """Find matching properties for a client."""
        client_id = request.data.get('client_id')
        limit = request.data.get('limit', 10)
        min_score = request.data.get('min_score', 30)
        
        try:
            client = User.objects.get(id=client_id, role='client')
            if not hasattr(client, 'client_profile'):
                return Response(
                    {'error': 'Profil client non trouvé.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            matcher = PropertyMatcher(client.client_profile)
            properties = matcher.find_matches(limit=limit, min_score=min_score)
            
            # Create response with detailed information
            results = []
            for property_obj in properties:
                score = matcher.calculate_match_score(property_obj)
                explanation = matcher.get_match_explanation(property_obj)
                
                results.append({
                    'property': property_obj,
                    'match_score': score,
                    'match_explanation': explanation,
                    'recommendations': explanation.get('recommendations', [])
                })
            
            # Serialize results
            serialized_results = []
            from .serializers import PropertyListSerializer
            for result in results:
                property_data = PropertyListSerializer(result['property']).data
                property_data.update({
                    'match_score': result['match_score'],
                    'match_explanation': result['match_explanation'],
                    'recommendations': result['recommendations']
                })
                serialized_results.append(property_data)
            
            return Response(serialized_results)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'Client introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def get_match_score(self, request):
        """Get match score for a specific client-property pair."""
        client_id = request.data.get('client_id')
        property_id = request.data.get('property_id')
        
        try:
            client = User.objects.get(id=client_id, role='client')
            property_obj = Property.objects.get(id=property_id)
            
            if not hasattr(client, 'client_profile'):
                return Response(
                    {'error': 'Profil client non trouvé.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            matcher = PropertyMatcher(client.client_profile)
            score = matcher.calculate_match_score(property_obj)
            explanation = matcher.get_match_explanation(property_obj)
            
            return Response({
                'match_score': score,
                'match_explanation': explanation
            })
            
        except (User.DoesNotExist, Property.DoesNotExist):
            return Response(
                {'error': 'Client ou propriété introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard data.
    """
    permission_classes = [permissions.IsAuthenticated, CanViewDashboard]
    
    @action(detail=False, methods=['get'])
    def client_dashboard(self, request):
        """Get client dashboard data."""
        if request.user.role != 'client':
            return Response(
                {'error': 'Seuls les clients peuvent accéder à ce tableau de bord.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            client_profile = request.user.client_profile
            
            # Get recent interactions
            recent_interactions = ClientInteraction.objects.filter(
                client=request.user
            ).order_by('-created_at')[:5]
            
            # Get upcoming visits
            upcoming_visits = PropertyInterest.objects.filter(
                client=request.user,
                interaction_type='visit_scheduled'
            ).order_by('interaction_date')[:5]
            
            # Get matching properties
            matching_properties = client_profile.get_matching_properties(limit=5)
            
            dashboard_data = {
                'profile': ClientProfileSerializer(client_profile).data,
                'recent_interactions': ClientInteractionSerializer(recent_interactions, many=True).data,
                'upcoming_visits': PropertyInterestSerializer(upcoming_visits, many=True).data,
                'matching_properties': matching_properties,
                'activity_summary': {
                    'total_interests': client_profile.total_properties_viewed,
                    'total_inquiries': client_profile.total_inquiries_made,
                    'conversion_score': client_profile.conversion_score
                }
            }
            
            return Response(dashboard_data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def agent_dashboard(self, request):
        """Get agent dashboard data."""
        if request.user.role not in ['agent', 'admin']:
            return Response(
                {'error': 'Seuls les agents et administrateurs peuvent accéder à ce tableau de bord.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get clients for this agent/agency
            if request.user.role == 'admin':
                clients = User.objects.filter(role='client')
            else:
                clients = User.objects.filter(role='client', profile__agency=request.user.agency)
            
            # Get leads
            if request.user.role == 'admin':
                leads = Lead.objects.all()
            else:
                leads = Lead.objects.filter(agency=request.user.agency)
            
            # Get recent interactions
            recent_interactions = ClientInteraction.objects.filter(
                agent=request.user
            ).order_by('-created_at')[:5]
            
            # Get upcoming visits
            upcoming_visits = PropertyInterest.objects.filter(
                agent=request.user,
                interaction_type='visit_scheduled'
            ).order_by('interaction_date')[:5]
            
            # Performance statistics
            performance_stats = {
                'total_clients': clients.count(),
                'pending_leads': leads.filter(status__in=['new', 'contacted']).count(),
                'completed_interactions': ClientInteraction.objects.filter(
                    agent=request.user, status='completed'
                ).count(),
                'avg_client_satisfaction': 0  # Placeholder for future implementation
            }
            
            dashboard_data = {
                'profile': {
                    'agent_name': request.user.get_full_name(),
                    'agency': request.user.agency.name,
                    'role': request.user.role
                },
                'recent_interactions': ClientInteractionSerializer(recent_interactions, many=True).data,
                'upcoming_visits': PropertyInterestSerializer(upcoming_visits, many=True).data,
                'performance_stats': performance_stats
            }
            
            return Response(dashboard_data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)