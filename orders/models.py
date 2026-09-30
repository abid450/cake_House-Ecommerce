from django.db import models

# Create your models here.
# order/models.py

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from products.models import Product


class Order(models.Model):
    """Order Model for Cake House"""
    
    # ============================================
    # Order Status Choices
    # ============================================
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('sslcommerz', 'SSLCommerz'),
        ('bkash', 'bKash'),
        ('nagad', 'Nagad'),
        ('card', 'Card'),
    ]
    
    # ============================================
    # Basic Information
    # ============================================
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True, db_index=True, blank=True)
    
    # ============================================
    # User
    # ============================================
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # ============================================
    # Guest Info (if not logged in)
    # ============================================
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    guest_name = models.CharField(max_length=200, blank=True)
    
    # ============================================
    # Shipping Address
    # ============================================
    shipping_name = models.CharField(max_length=200)
    shipping_phone = models.CharField(max_length=20)
    shipping_email = models.EmailField(blank=True)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, default='Bangladesh')
    
    # ============================================
    # Billing Address (Optional)
    # ============================================
    billing_same_as_shipping = models.BooleanField(default=True)
    billing_name = models.CharField(max_length=200, blank=True)
    billing_phone = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField(blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    
    # ============================================
    # Order Details
    # ============================================
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    delivery_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # ============================================
    # Payment
    # ============================================
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        default='cod'
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending'
    )
    payment_transaction_id = models.CharField(max_length=200, blank=True)
    payment_details = models.JSONField(default=dict, blank=True)
    
    # ============================================
    # Status
    # ============================================
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        db_index=True
    )
    
    # ============================================
    # Notes
    # ============================================
    customer_note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    
    # ============================================
    # Delivery
    # ============================================
    delivery_date = models.DateField(null=True, blank=True)
    delivery_time = models.CharField(max_length=50, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # ============================================
    # Tracking
    # ============================================
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)
    
    # ============================================
    # Timestamps
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.shipping_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        import random
        import string
        prefix = 'CAK'
        date_str = timezone.now().strftime('%Y%m%d')
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}-{date_str}-{random_str}"
    
    # ============================================
    # Properties
    # ============================================
    @property
    def total_items(self):
        """Get total items in order"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def is_paid(self):
        return self.payment_status == 'paid'
    
    @property
    def is_cancellable(self):
        return self.status in ['pending', 'confirmed']
    
    @property
    def is_deliverable(self):
        return self.status in ['confirmed', 'processing', 'shipped']
    
    # ============================================
    # Methods
    # ============================================
    def calculate_totals(self):
        """Calculate order totals"""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.total_amount = (
            self.subtotal + 
            self.delivery_charge + 
            self.tax_amount - 
            self.discount_amount
        )
        self.save()
        return self.total_amount
    
    def mark_as_paid(self, transaction_id=''):
        """Mark order as paid"""
        self.payment_status = 'paid'
        self.payment_transaction_id = transaction_id
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()
    
    def cancel(self, reason=''):
        """Cancel order"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.admin_note = f"{self.admin_note}\nCancelled: {reason}"
        self.save()
        # Restore stock
        for item in self.items.all():
            item.product.increase_stock(item.quantity)


class OrderItem(models.Model):
    """Order Item Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    
    # ============================================
    # Product Snapshot (in case product changes)
    # ============================================
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50)
    product_image = models.URLField(blank=True)
    
    # ============================================
    # Pricing
    # ============================================
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # ============================================
    # Customization
    # ============================================
    customization = models.JSONField(default=dict, blank=True)
    special_instructions = models.TextField(blank=True)
    
    # ============================================
    # Timestamps
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """Track order status changes"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.CharField(max_length=20)
    note = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order Status History'
        verbose_name_plural = 'Order Status Histories'
    
    def __str__(self):
        return f"{self.order.order_number} - {self.status}"