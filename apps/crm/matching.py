"""
Automatic property matching system for CRM.
"""

import math
from decimal import Decimal
# from django.contrib.gis.measure import D
# from django.contrib.gis.geos import Point
from django.db.models import Q, Avg
from apps.properties.models import Property
from .models import ClientProfile, PropertyInterest


class PropertyMatcher:
    """
    Intelligent property matching system that calculates compatibility scores
    between client preferences and available properties.
    """
    
    def __init__(self, client_profile):
        self.client_profile = client_profile
        self.user = client_profile.user
    
    def find_matches(self, limit=10, min_score=30):
        """
        Find properties that match client preferences.
        
        Args:
            limit: Maximum number of results to return
            min_score: Minimum match score (0-100) to include
            
        Returns:
            QuerySet of Properties with match scores
        """
        # Start with available properties only
        queryset = Property.objects.filter(status='available')
        
        # Apply basic filters
        queryset = self._apply_basic_filters(queryset)
        
        # Calculate match scores and order by score
        properties_with_scores = []
        
        for property_obj in queryset:
            score = self.calculate_match_score(property_obj)
            if score >= min_score:
                properties_with_scores.append((property_obj, score))
        
        # Sort by score (descending) and limit results
        properties_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return only property objects, but we'll annotate with score
        matched_properties = [prop for prop, score in properties_with_scores[:limit]]
        
        # Add match scores as annotations
        if matched_properties:
            from django.db.models import Value, IntegerField
            from django.db.models.functions import Coalesce
            
            # Create a mapping of property_id to score
            score_map = {str(prop.id): score for prop, score in properties_with_scores[:limit]}
            
            # Annotate with match scores
            queryset = Property.objects.filter(id__in=[p.id for p in matched_properties])
            queryset = queryset.annotate(
                match_score=Coalesce(
                    Value(score_map.get(str(obj.id), 0), output_field=IntegerField()),
                    Value(0, output_field=IntegerField())
                )
            )
            
            return queryset.order_by('-match_score')
        
        return Property.objects.none()
    
    def calculate_match_score(self, property_obj):
        """
        Calculate match score between client preferences and a property.
        
        Score calculation breakdown:
        - Budget compatibility: 25 points
        - Property type match: 20 points  
        - Location proximity: 20 points
        - Size requirements: 15 points
        - Features match: 10 points
        - Financing readiness: 10 points
        
        Returns score from 0-100
        """
        score = 0
        max_score = 100
        
        # 1. Budget Compatibility (25 points)
        budget_score = self._calculate_budget_score(property_obj)
        score += budget_score
        
        # 2. Property Type Match (20 points)
        type_score = self._calculate_property_type_score(property_obj)
        score += type_score
        
        # 3. Location Compatibility (20 points)
        location_score = self._calculate_location_score(property_obj)
        score += location_score
        
        # 4. Size Requirements (15 points)
        size_score = self._calculate_size_score(property_obj)
        score += size_score
        
        # 5. Features Match (10 points)
        features_score = self._calculate_features_score(property_obj)
        score += features_score
        
        # 6. Financing Readiness (10 points)
        finance_score = self._calculate_financing_score(property_obj)
        score += finance_score
        
        # Clamp score to 0-100
        return min(score, max_score)
    
    def _calculate_budget_score(self, property_obj):
        """Calculate budget compatibility score (0-25)."""
        if not self.client_profile.max_budget:
            return 15  # Neutral score if no budget specified
        
        property_price = property_obj.price
        
        # If property is within budget
        if property_price <= self.client_profile.max_budget:
            budget_range = self.client_profile.max_budget - (self.client_profile.min_budget or 0)
            if budget_range > 0:
                # Check if property is in preferred budget range
                min_budget = self.client_profile.min_budget or (self.client_profile.max_budget * 0.7)
                if min_budget <= property_price <= self.client_profile.max_budget:
                    return 25  # Perfect budget match
                elif property_price >= min_budget:
                    return 20  # Good budget match
                else:
                    return 15  # Acceptable but below preferred range
            else:
                return 25 if property_price <= self.client_profile.max_budget else 0
        
        # Property exceeds budget
        excess_ratio = (property_price - self.client_profile.max_budget) / self.client_profile.max_budget
        if excess_ratio <= 0.1:  # Within 10% over budget
            return 5  # Slight over budget
        else:
            return 0  # Significantly over budget
    
    def _calculate_property_type_score(self, property_obj):
        """Calculate property type compatibility score (0-20)."""
        preferred_types = self.client_profile.preferred_property_types
        
        if not preferred_types:
            return 15  # Neutral score if no preference specified
        
        if property_obj.property_type in preferred_types:
            return 20  # Perfect type match
        
        # Partial matches for similar property types
        type_groups = {
            'apartment': ['duplex', 'triplex', 'penthouse', 'loft'],
            'house': ['villa'],
            'villa': ['house'],
            'commercial': ['office'],
            'office': ['commercial']
        }
        
        for preferred_type in preferred_types:
            if property_obj.property_type in type_groups.get(preferred_type, []):
                return 15  # Good partial match
        
        return 5  # No match but property exists
    
    def _calculate_location_score(self, property_obj):
        """Calculate location compatibility score (0-20)."""
        score = 0
        
        # City preferences
        preferred_cities = self.client_profile.preferred_cities
        if preferred_cities:
            if property_obj.city in preferred_cities:
                score += 15
            else:
                # Check for partial matches
                for preferred_city in preferred_cities:
                    if preferred_city.lower() in property_obj.city.lower():
                        score += 10
                        break
                else:
                    score += 5  # Other city but in preferred locations
        else:
            score += 10  # No city preference
        
        # Distance from center (if coordinates available)
        # if property_obj.latitude and property_obj.longitude and hasattr(self.client_profile, 'preferred_locations'):
        #     try:
        #         # Check if city is in preferred locations
        #         location_prefs = self.client_profile.preferred_locations
        #         if any(pref.get('city', '').lower() == property_obj.city.lower() for pref in location_prefs):
        #             score += 5
        #     except:
        #         pass
        
        return min(score, 20)
    
    def _calculate_size_score(self, property_obj):
        """Calculate size requirements score (0-15)."""
        score = 0
        
        # Bedrooms
        if self.client_profile.min_bedrooms and property_obj.bedrooms:
            if property_obj.bedrooms >= self.client_profile.min_bedrooms:
                score += 8
                # Bonus for exceeding minimum
                if self.client_profile.max_bedrooms and property_obj.bedrooms <= self.client_profile.max_bedrooms:
                    score += 2
            else:
                # Penalty for below minimum
                score -= 3
        
        # Area
        if self.client_profile.min_area and property_obj.surface_area:
            if property_obj.surface_area >= self.client_profile.min_area:
                score += 5
                # Bonus if within max area
                if self.client_profile.max_area and property_obj.surface_area <= self.client_profile.max_area:
                    score += 2
            else:
                # Penalty for below minimum
                score -= 2
        
        return max(score, 0)
    
    def _calculate_features_score(self, property_obj):
        """Calculate features compatibility score (0-10)."""
        if not self.client_profile.must_have_features:
            return 7  # Neutral score if no specific requirements
        
        must_have = self.client_profile.must_have_features
        property_features = property_obj.features or {}
        
        matches = 0
        total_required = len(must_have)
        
        for required_feature in must_have:
            if required_feature in property_features:
                matches += 1
            elif hasattr(property_obj, required_feature):
                # Check if property has the feature as an attribute
                if getattr(property_obj, required_feature, False):
                    matches += 1
        
        if total_required > 0:
            return int((matches / total_required) * 10)
        else:
            return 7
    
    def _calculate_financing_score(self, property_obj):
        """Calculate financing readiness score (0-10)."""
        financing_status = self.client_profile.financing_status
        
        if financing_status == 'pre_approved':
            return 10  # Best case - pre-approved financing
        elif financing_status == 'cash':
            return 9   # Cash purchase - very attractive
        elif financing_status == 'mortgage':
            return 7   # Needs mortgage but prepared
        else:  # not_sure
            return 4   # Uncertain financing situation
    
    def _apply_basic_filters(self, queryset):
        """Apply basic filters before detailed scoring."""
        # Only available properties
        queryset = queryset.filter(status='available')
        
        # Filter by agency if client is from a specific agency
        if hasattr(self.user, 'agency') and self.user.agency:
            queryset = queryset.filter(agency=self.user.agency)
        
        return queryset
    
    def get_match_explanation(self, property_obj):
        """
        Get detailed explanation of why a property matches or doesn't match.
        
        Returns a dictionary with scoring breakdown and recommendations.
        """
        score = self.calculate_match_score(property_obj)
        
        explanation = {
            'overall_score': score,
            'breakdown': {
                'budget': self._calculate_budget_score(property_obj),
                'property_type': self._calculate_property_type_score(property_obj),
                'location': self._calculate_location_score(property_obj),
                'size': self._calculate_size_score(property_obj),
                'features': self._calculate_features_score(property_obj),
                'financing': self._calculate_financing_score(property_obj)
            },
            'recommendations': []
        }
        
        # Generate recommendations based on low scores
        if explanation['breakdown']['budget'] < 15:
            explanation['recommendations'].append(
                "Considérez ajuster votre budget ou regarder des propriétés dans une zone différente."
            )
        
        if explanation['breakdown']['property_type'] < 10:
            explanation['recommendations'].append(
                "Vous pourriez être intéressé par des types de propriétés similaires."
            )
        
        if explanation['breakdown']['location'] < 10:
            explanation['recommendations'].append(
                "Découvrez cette zone - elle pourrait répondre à vos besoins."
            )
        
        if explanation['breakdown']['size'] < 8:
            explanation['recommendations'].append(
                "La superficie pourrait être adaptée selon vos besoins."
            )
        
        return explanation


class LeadMatcher:
    """
    Matching system for leads to identify hot prospects and opportunities.
    """
    
    def __init__(self, lead):
        self.lead = lead
    
    def calculate_urgency_score(self):
        """Calculate how urgent this lead is (0-100)."""
        score = 0
        
        # Timeframe impact
        timeframe_scores = {
            'immediate': 30, 'within_month': 25, 'within_3_months': 20,
            'within_6_months': 15, 'within_year': 10, 'exploring': 5
        }
        score += timeframe_scores.get(self.lead.timeframe.lower() if self.lead.timeframe else '', 0)
        
        # Budget specificity
        if self.lead.budget_range:
            score += 20
        
        # Contact information completeness
        if self.lead.email and self.lead.phone:
            score += 20
        elif self.lead.email or self.lead.phone:
            score += 10
        
        # Property interest detail
        interest_details = [self.lead.property_type_interest, self.lead.budget_range, 
                          self.lead.location_interest, self.lead.timeframe]
        score += sum(15 for detail in interest_details if detail)
        
        # Source quality
        source_scores = {'referral': 15, 'website': 10, 'walk_in': 12, 'open_house': 12, 
                        'phone_call': 8, 'social_media': 5, 'advertisement': 8}
        score += source_scores.get(self.lead.source, 5)
        
        return min(score, 100)
    
    def recommend_action(self):
        """Recommend next action based on lead analysis."""
        actions = []
        
        if not self.lead.assigned_agent:
            actions.append("Assigner un agent dès que possible")
        
        if self.lead.status == 'new':
            actions.append("Contacter dans les 24h")
        elif self.lead.status == 'contacted':
            actions.append("Planifier un rendez-vous")
        
        if self.lead.qualification == 'hot':
            actions.append("Priorité élevée - suivi personnalisé")
        elif self.lead.qualification == 'warm':
            actions.append("Suivi régulier recommandé")
        
        if not self.lead.property_type_interest or not self.lead.budget_range:
            actions.append("Collecter plus d'informations sur les préférences")
        
        return actions


def auto_match_properties_for_client(client_user, limit=5):
    """
    Utility function to automatically find matching properties for a client.
    
    Args:
        client_user: User instance with role='client'
        limit: Maximum number of properties to return
        
    Returns:
        List of Property instances with match scores
    """
    if not hasattr(client_user, 'client_profile'):
        return []
    
    matcher = PropertyMatcher(client_user.client_profile)
    return matcher.find_matches(limit=limit)


def auto_assign_leads_to_agents(agency):
    """
    Automatically assign new leads to available agents based on workload.
    
    Args:
        agency: Agency instance
        
    Returns:
        Number of leads assigned
    """
    from django.db.models import Count
    from apps.auth.models import User
    
    # Get available agents in the agency
    agents = User.objects.filter(role='agent', profile__agency=agency, is_active=True)
    
    if not agents:
        return 0
    
    # Get lead distribution among agents
    agent_workload = {}
    for agent in agents:
        assigned_leads = Lead.objects.filter(assigned_agent=agent, status__in=['new', 'contacted', 'qualified']).count()
        agent_workload[agent.id] = assigned_leads
    
    # Get unassigned leads
    unassigned_leads = Lead.objects.filter(
        agency=agency,
        assigned_agent__isnull=True,
        status__in=['new', 'contacted']
    ).order_by('-score', '-created_at')
    
    assigned_count = 0
    for lead in unassigned_leads:
        # Find agent with lowest workload
        best_agent_id = min(agent_workload.keys(), key=lambda k: agent_workload[k])
        best_agent = agents.get(id=best_agent_id)
        
        # Assign lead
        lead.assigned_agent = best_agent
        lead.status = 'contacted'
        lead.save()
        
        # Update workload
        agent_workload[best_agent_id] += 1
        assigned_count += 1
    
    return assigned_count