# apps/cart/models.py

import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from products.models import Product


class Cart(models.Model):
    """
    Shopping cart. Belongs to an authenticated user when logged in,
    otherwise identified by the Django session key for guest checkout.
    Only one active cart exists per owner (user or session) at a time.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='carts'
    )
    session_key = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_active=True, user__isnull=False),
                name='unique_active_cart_per_user'
            ),
            models.UniqueConstraint(
                fields=['session_key'],
                condition=models.Q(is_active=True, session_key__isnull=False),
                name='unique_active_cart_per_session'
            ),
        ]
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        owner = self.user or self.session_key or 'guest'
        return f"Cart({owner})"

    # ============================================
    # Computed totals — always derived live from
    # line items, never stored, so they can never
    # drift out of sync with the cart contents.
    # ============================================

    @property
    def items_qs(self):
        return self.items.select_related('product', 'product__category')

    @property
    def total_items(self):
        """Total number of units across all lines."""
        return sum(item.quantity for item in self.items_qs)

    @property
    def total_lines(self):
        """Number of distinct product lines."""
        return self.items_qs.count()

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items_qs), Decimal('0.00'))

    @property
    def delivery_total(self):
        """
        Sum of delivery charges for distinct products that are not
        marked free-delivery. Charged once per product, not per unit.
        """
        total = Decimal('0.00')
        seen_products = set()
        for item in self.items_qs:
            if item.product_id in seen_products:
                continue
            seen_products.add(item.product_id)
            if not item.product.is_free_delivery:
                total += item.product.delivery_charge
        return total

    @property
    def grand_total(self):
        return self.subtotal + self.delivery_total

    @property
    def has_price_changes(self):
        """True if any item's stored price no longer matches the live product price."""
        return any(item.price_changed for item in self.items_qs)

    @property
    def has_stock_issues(self):
        """True if any item can no longer be fulfilled at its current quantity."""
        return any(item.stock_issue for item in self.items_qs)

    @property
    def is_empty(self):
        return not self.items_qs.exists()


class CartItem(models.Model):
    """
    A single product line inside a cart. The unit price is captured at
    the moment the item is added so the cart total stays stable even if
    the product's price changes later — `price_changed` flags this for
    the frontend so it can prompt the user before checkout.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')

    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="Product's final_price captured at the time this item was added"
    )
    customization = models.JSONField(
        default=dict, blank=True,
        help_text="Selected customization, e.g. {'flavor': 'Chocolate', 'size': '10 inch'}"
    )
    note = models.CharField(max_length=255, blank=True, help_text="Special instructions for this item")

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-added_at']
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def save(self, *args, **kwargs):
        if self.unit_price is None:
            self.unit_price = self.product.final_price
        super().save(*args, **kwargs)

    # ============================================
    # Computed fields
    # ============================================

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def current_unit_price(self):
        """The product's live price right now."""
        return self.product.final_price

    @property
    def price_changed(self):
        return self.unit_price != self.current_unit_price

    @property
    def stock_issue(self):
        return not self.product.is_available_for_order(self.quantity)

    @property
    def max_available_quantity(self):
        return self.product.quantity