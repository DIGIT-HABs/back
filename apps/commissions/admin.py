"""
Admin configuration for commissions app.
"""

from django.contrib import admin
from .models import Commission, Payment


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent', 'agency', 'commission_type', 'commission_amount', 'status', 'transaction_date']
    list_filter = ['status', 'commission_type', 'transaction_date']
    search_fields = ['agent__username', 'agent__email', 'property__title']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'agent', 'agency', 'amount', 'payment_method', 'status', 'payment_date']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['agent__username', 'agent__email', 'payment_reference']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['commissions']

