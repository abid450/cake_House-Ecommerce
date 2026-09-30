from django.db import models

# Create your models here.
# payment/models.py

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Payment(models.Model):
    """Payment Transaction Model for SSLCommerz"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    GATEWAY_CHOICES = [
        ('sslcommerz', 'SSLCommerz'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('cod', 'Cash on Delivery'),
    ]
    
    # ============================================
    # Basic Information
    # ============================================
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # ============================================
    # Gateway Info
    # ============================================
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES, default='sslcommerz')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='BDT')
    
    # ============================================
    # SSLCommerz Response
    # ============================================
    session_key = models.CharField(max_length=200, blank=True)
    gateway_page_url = models.URLField(blank=True)
    validation_id = models.CharField(max_length=100, blank=True)
    bank_transaction_id = models.CharField(max_length=100, blank=True)
    card_type = models.CharField(max_length=50, blank=True)
    card_no = models.CharField(max_length=50, blank=True)
    store_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # ============================================
    # Status
    # ============================================
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    risk_level = models.CharField(max_length=20, blank=True)
    risk_title = models.CharField(max_length=100, blank=True)
    
    # ============================================
    # Raw Response
    # ============================================
    raw_response = models.JSONField(default=dict, blank=True)
    ipn_response = models.JSONField(default=dict, blank=True)
    
    # ============================================
    # Timestamps
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.get_status_display()}"
    
    # ============================================
    # Methods
    # ============================================
    def mark_success(self, response_data=None):
        """Mark payment as successful"""
        self.status = 'success'
        self.paid_at = timezone.now()
        if response_data:
            self.raw_response = response_data
            self.validation_id = response_data.get('val_id', '')
            self.bank_transaction_id = response_data.get('bank_tran_id', '')
            self.card_type = response_data.get('card_type', '')
            self.card_no = response_data.get('card_no', '')
            self.store_amount = response_data.get('store_amount', self.amount)
            self.risk_level = response_data.get('risk_level', '')
            self.risk_title = response_data.get('risk_title', '')
        self.save()
        
        # Update order
        self.order.mark_as_paid(self.transaction_id)
    
    def mark_failed(self, response_data=None):
        """Mark payment as failed"""
        self.status = 'failed'
        self.failed_at = timezone.now()
        if response_data:
            self.raw_response = response_data
        self.save()
        
        # Update order
        self.order.payment_status = 'failed'
        self.order.save()
    
    def mark_cancelled(self):
        """Mark payment as cancelled"""
        self.status = 'cancelled'
        self.save()
        
        # Update order
        self.order.payment_status = 'failed'
        self.order.save()
    
    def mark_refunded(self, amount=None):
        """Mark payment as refunded"""
        self.status = 'refunded'
        self.save()
        
        # Update order
        self.order.payment_status = 'refunded'
        self.order.save()