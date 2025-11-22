"""
Services for reservations management.
"""

import stripe
from decimal import Decimal
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.properties.models import Property
from apps.crm.models import ClientProfile

User = get_user_model()


class PaymentService:
    """
    Service for handling Stripe payment processing.
    """
    
    def __init__(self):
        """Initialize Stripe with secret key."""
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY must be configured in settings")
    
    def create_payment_intent(self, amount, currency, reservation_id, description='', billing_info=None):
        """
        Create a Stripe payment intent for a reservation.
        
        Args:
            amount: Amount in cents
            currency: Currency code (eur, usd, etc.)
            reservation_id: UUID of the reservation
            description: Payment description
            billing_info: Billing information dictionary
            
        Returns:
            Stripe PaymentIntent object
        """
        try:
            # Prepare metadata
            metadata = {
                'reservation_id': str(reservation_id),
                'type': 'reservation_payment'
            }
            
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                description=description,
                metadata=metadata,
                automatic_payment_methods={'enabled': True},
                **({'receipt_email': billing_info.get('email')} if billing_info and billing_info.get('email') else {})
            )
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            raise Exception(f"Payment intent creation failed: {str(e)}")
    
    def confirm_payment_intent(self, payment_intent_id):
        """
        Confirm a Stripe payment intent.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            Payment intent object
        """
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            raise Exception(f"Payment confirmation failed: {str(e)}")
    
    def create_refund(self, charge_id, amount, reason=''):
        """
        Create a refund for a charge.
        
        Args:
            charge_id: Stripe charge ID
            amount: Refund amount in cents
            reason: Refund reason
            
        Returns:
            Stripe Refund object
        """
        try:
            refund = stripe.Refund.create(
                charge=charge_id,
                amount=amount,
                reason='requested_by_customer' if reason else None,
                metadata={'type': 'reservation_refund'} if reason else None
            )
            return refund
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            raise Exception(f"Refund creation failed: {str(e)}")
    
    def get_payment_method(self, payment_method_id):
        """
        Retrieve payment method details.
        
        Args:
            payment_method_id: Stripe payment method ID
            
        Returns:
            Payment method object
        """
        try:
            return stripe.PaymentMethod.retrieve(payment_method_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    def create_customer(self, email, name, phone=None):
        """
        Create a Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            phone: Customer phone
            
        Returns:
            Stripe Customer object
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                phone=phone,
                metadata={'type': 'reservation_customer'}
            )
            return customer
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            raise Exception(f"Customer creation failed: {str(e)}")
    
    def attach_payment_method(self, payment_method_id, customer_id):
        """
        Attach payment method to customer.
        
        Args:
            payment_method_id: Stripe payment method ID
            customer_id: Stripe customer ID
            
        Returns:
            Updated payment method object
        """
        try:
            return stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    def calculate_application_fee(self, amount, fee_percentage=2.9):
        """
        Calculate Stripe application fee.
        
        Args:
            amount: Transaction amount in cents
            fee_percentage: Application fee percentage
            
        Returns:
            Application fee amount in cents
        """
        return int(amount * (fee_percentage / 100))


class NotificationService:
    """
    Service for handling notifications related to reservations.
    """
    
    @staticmethod
    def send_visit_confirmation(reservation):
        """
        Send confirmation email for visit reservations.
        
        Args:
            reservation: Reservation object
        """
        try:
            # Get email recipients
            recipients = []
            
            # Client email
            if reservation.client_email:
                recipients.append(reservation.client_email)
            elif reservation.client_profile and reservation.client_profile.user:
                recipients.append(reservation.client_profile.user.email)
            
            # Agent email
            if reservation.assigned_agent and reservation.assigned_agent.email:
                recipients.append(reservation.assigned_agent.email)
            
            if not recipients:
                return
            
            # Prepare context
            context = {
                'reservation': reservation,
                'property': reservation.property,
                'client_name': reservation.get_client_name(),
                'client_email': reservation.get_client_email(),
                'scheduled_date': reservation.scheduled_date,
                'duration': reservation.duration_minutes,
                'agent': reservation.assigned_agent,
                'base_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            }
            
            # Render email templates
            subject = f"Confirmation de visite - {reservation.property.title}"
            html_message = render_to_string('emails/visit_confirmation.html', context)
            plain_message = strip_tags(html_message)
            
            # Send email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@digit-hab.com'),
                recipient_list=recipients,
                html_message=html_message
            )
            
        except Exception as e:
            # Log error but don't fail the reservation creation
            print(f"Failed to send visit confirmation email: {str(e)}")
    
    @staticmethod
    def send_confirmation_notification(reservation):
        """
        Send confirmation notification for reservation.
        
        Args:
            reservation: Reservation object
        """
        try:
            recipients = []
            
            # Client notification
            if reservation.client_email:
                recipients.append(reservation.client_email)
            elif reservation.client_profile and reservation.client_profile.user:
                recipients.append(reservation.client_profile.user.email)
            
            # Agent notification
            if reservation.assigned_agent and reservation.assigned_agent.email:
                recipients.append(reservation.assigned_agent.email)
            
            if not recipients:
                return
            
            # Prepare context
            context = {
                'reservation': reservation,
                'property': reservation.property,
                'client_name': reservation.get_client_name(),
                'confirmation_date': reservation.confirmed_at,
                'agent': reservation.assigned_agent,
                'base_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            }
            
            # Determine email type based on reservation type
            if reservation.reservation_type == 'visit':
                template = 'emails/visit_confirmed.html'
                subject = f"Visite confirmée - {reservation.property.title}"
            elif reservation.reservation_type == 'purchase':
                template = 'emails/purchase_confirmed.html'
                subject = f"Offre confirmée - {reservation.property.title}"
            else:
                template = 'emails/reservation_confirmed.html'
                subject = f"Réservation confirmée - {reservation.property.title}"
            
            # Render and send email
            html_message = render_to_string(template, context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@digit-hab.com'),
                recipient_list=recipients,
                html_message=html_message
            )
            
        except Exception as e:
            print(f"Failed to send confirmation notification: {str(e)}")
    
    @staticmethod
    def send_cancellation_notification(reservation, reason=''):
        """
        Send cancellation notification.
        
        Args:
            reservation: Reservation object
            reason: Cancellation reason
        """
        try:
            recipients = []
            
            # Client notification
            if reservation.client_email:
                recipients.append(reservation.client_email)
            elif reservation.client_profile and reservation.client_profile.user:
                recipients.append(reservation.client_profile.user.email)
            
            # Agent notification
            if reservation.assigned_agent and reservation.assigned_agent.email:
                recipients.append(reservation.assigned_agent.email)
            
            if not recipients:
                return
            
            # Prepare context
            context = {
                'reservation': reservation,
                'property': reservation.property,
                'client_name': reservation.get_client_name(),
                'cancellation_reason': reason,
                'cancelled_at': reservation.cancelled_at,
                'base_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            }
            
            # Render and send email
            html_message = render_to_string('emails/reservation_cancelled.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"Réservation annulée - {reservation.property.title}"
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@digit-hab.com'),
                recipient_list=recipients,
                html_message=html_message
            )
            
        except Exception as e:
            print(f"Failed to send cancellation notification: {str(e)}")
    
    @staticmethod
    def send_payment_confirmation(payment):
        """
        Send payment confirmation notification.
        
        Args:
            payment: Payment object
        """
        try:
            reservation = payment.reservation
            recipients = []
            
            # Client notification
            if payment.billing_email:
                recipients.append(payment.billing_email)
            elif reservation.client_email:
                recipients.append(reservation.client_email)
            elif reservation.client_profile and reservation.client_profile.user:
                recipients.append(reservation.client_profile.user.email)
            
            # Agent notification
            if reservation.assigned_agent and reservation.assigned_agent.email:
                recipients.append(reservation.assigned_agent.email)
            
            if not recipients:
                return
            
            # Prepare context
            context = {
                'payment': payment,
                'reservation': reservation,
                'property': reservation.property,
                'client_name': reservation.get_client_name(),
                'amount': payment.amount,
                'currency': payment.currency,
                'payment_date': payment.completed_at,
                'payment_method': payment.get_payment_method_display(),
                'base_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            }
            
            # Render and send email
            html_message = render_to_string('emails/payment_confirmation.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"Confirmation de paiement - {reservation.property.title}"
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@digit-hab.com'),
                recipient_list=recipients,
                html_message=html_message
            )
            
        except Exception as e:
            print(f"Failed to send payment confirmation: {str(e)}")
    
    @staticmethod
    def send_payment_failure_notification(payment):
        """
        Send payment failure notification.
        
        Args:
            payment: Payment object
        """
        try:
            reservation = payment.reservation
            recipients = []
            
            # Client notification
            if payment.billing_email:
                recipients.append(payment.billing_email)
            elif reservation.client_email:
                recipients.append(reservation.client_email)
            elif reservation.client_profile and reservation.client_profile.user:
                recipients.append(reservation.client_profile.user.email)
            
            if not recipients:
                return
            
            # Prepare context
            context = {
                'payment': payment,
                'reservation': reservation,
                'property': reservation.property,
                'client_name': reservation.get_client_name(),
                'amount': payment.amount,
                'currency': payment.currency,
                'error_message': payment.error_message,
                'failure_reason': payment.failure_reason,
                'base_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            }
            
            # Render and send email
            html_message = render_to_string('emails/payment_failed.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"Échec du paiement - {reservation.property.title}"
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@digit-hab.com'),
                recipient_list=recipients,
                html_message=html_message
            )
            
        except Exception as e:
            print(f"Failed to send payment failure notification: {str(e)}")
    
    @staticmethod
    def send_reminder_notification(reservation):
        """
        Send reminder notification before scheduled visit.
        
        Args:
            reservation: Reservation object
        """
        try:
            recipients = []
            
            # Client notification
            if reservation.client_email:
                recipients.append(reservation.client_email)
            elif reservation.client_profile and reservation.client_profile.user:
                recipients.append(reservation.client_profile.user.email)
            
            if not recipients:
                return
            
            # Calculate reminder time
            reminder_time = reservation.scheduled_date - timezone.timedelta(hours=24)
            if timezone.now() < reminder_time:
                return  # Don't send if too early
            
            # Prepare context
            context = {
                'reservation': reservation,
                'property': reservation.property,
                'client_name': reservation.get_client_name(),
                'scheduled_date': reservation.scheduled_date,
                'duration': reservation.duration_minutes,
                'agent': reservation.assigned_agent,
                'base_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            }
            
            # Render and send email
            html_message = render_to_string('emails/visit_reminder.html', context)
            plain_message = strip_tags(html_message)
            
            subject = f"Rappel de visite - {reservation.property.title}"
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@digit-hab.com'),
                recipient_list=recipients,
                html_message=html_message
            )
            
        except Exception as e:
            print(f"Failed to send reminder notification: {str(e)}")


class AvailabilityService:
    """
    Service for checking property availability and managing scheduling.
    """
    
    @staticmethod
    def check_availability(property_id, start_date, end_date, duration_minutes=60):
        """
        Check if a property is available for a time slot.
        
        Args:
            property_id: Property UUID
            start_date: Start datetime
            end_date: End datetime
            duration_minutes: Duration in minutes
            
        Returns:
            dict with availability status and conflicts
        """
        try:
            property_obj = Property.objects.get(id=property_id)
            
            # Check if property is available
            if property_obj.status not in ['available', 'under_offer']:
                return {
                    'available': False,
                    'reason': f'Property not available (status: {property_obj.status})',
                    'conflicts': []
                }
            
            # Check for conflicting reservations
            conflicts = Reservation.objects.filter(
                property=property_obj,
                status__in=['pending', 'confirmed'],
                scheduled_date__lt=end_date,
                scheduled_end_date__gt=start_date
            ).exclude(
                scheduled_date__gte=end_date
            ).select_related('client_profile__user')
            
            # Check for conflicting visits
            visit_conflicts = Property.objects.filter(
                id=property_id,
                visits__scheduled_date__lt=end_date,
                visits__scheduled_time__gte=start_date.time(),
                visits__status__in=['scheduled', 'confirmed']
            )
            
            conflict_list = list(conflicts) + list(visit_conflicts)
            
            return {
                'available': len(conflict_list) == 0,
                'conflicts': [str(c) for c in conflict_list],
                'property_status': property_obj.status
            }
            
        except Property.DoesNotExist:
            return {
                'available': False,
                'reason': 'Property not found',
                'conflicts': []
            }
        except Exception as e:
            return {
                'available': False,
                'reason': f'Error checking availability: {str(e)}',
                'conflicts': []
            }
    
    @staticmethod
    def find_available_slots(property_id, date, duration_minutes=60, slot_duration=30):
        """
        Find available time slots for a specific date.
        
        Args:
            property_id: Property UUID
            date: Date to check
            duration_minutes: Required duration in minutes
            slot_duration: Slot granularity in minutes
            
        Returns:
            list of available time slots
        """
        try:
            from datetime import datetime, timedelta
            
            property_obj = Property.objects.get(id=property_id)
            
            # Define working hours (9 AM to 6 PM)
            work_start = datetime.combine(date, datetime.min.time().replace(hour=9))
            work_end = datetime.combine(date, datetime.min.time().replace(hour=18))
            
            # Get existing reservations for the day
            existing_reservations = Reservation.objects.filter(
                property=property_obj,
                scheduled_date__date=date,
                status__in=['pending', 'confirmed']
            ).order_by('scheduled_date')
            
            # Generate available slots
            available_slots = []
            current_time = work_start
            
            while current_time + timedelta(minutes=duration_minutes) <= work_end:
                end_time = current_time + timedelta(minutes=duration_minutes)
                
                # Check if slot conflicts with existing reservations
                has_conflict = any(
                    res.scheduled_date < end_time and res.scheduled_end_date > current_time
                    for res in existing_reservations
                )
                
                if not has_conflict:
                    available_slots.append({
                        'start': current_time.time(),
                        'end': end_time.time(),
                        'start_datetime': current_time,
                        'end_datetime': end_time
                    })
                
                current_time += timedelta(minutes=slot_duration)
            
            return available_slots
            
        except Property.DoesNotExist:
            return []
        except Exception as e:
            print(f"Error finding available slots: {str(e)}")
            return []