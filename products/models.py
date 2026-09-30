# apps/products/models.py

import uuid
import random
import string
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from category.models import Category, DessertType


class Product(models.Model):
    """Bakery Product Model - Cake House"""
    
    # ============================================
    # Basic Information
    # ============================================
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    
    # ============================================
    # Category & Type
    # ============================================
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    dessert_type = models.ForeignKey(
        DessertType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # ============================================
    # Pricing
    # ============================================
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00,
        help_text="Regular selling price"
    )
    discount_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Discounted price (if any)"
    )
    
    # ============================================
    # Stock & Ingredients
    # ============================================
    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Available quantity in stock"
    )
    min_stock_level = models.IntegerField(
        default=5,
        validators=[MinValueValidator(0)],
        help_text="Minimum stock alert level"
    )
    ingredients = models.JSONField(
        default=list, 
        blank=True, 
        help_text="List of ingredients"
    )
    
    # ============================================
    # Details
    # ============================================
    description = models.TextField(
        blank=True,
        help_text="Full product description"
    )
    preparation_time = models.IntegerField(
        default=0, 
        help_text="Preparation time in minutes"
    )
    shelf_life = models.IntegerField(
        default=0,
        help_text="Shelf life in days"
    )
    serving_size = models.CharField(
        max_length=50,
        blank=True,
        help_text="Serving size (e.g., '6-8 people')"
    )

    
    # ============================================
    # Images
    # ============================================
    main_image = models.ImageField(
        upload_to='products/', 
        blank=True, 
        null=True,
        help_text="Main product image"
    )
    gallery_images = models.JSONField(
        default=list, 
        blank=True,
        help_text="Additional product images"
    )
    video_url = models.URLField(
        blank=True, 
        null=True,
        help_text="Product video URL (YouTube/Vimeo)"
    )
    
    # ============================================
    # Availability
    # ============================================
    is_active = models.BooleanField(
        default=True,
        help_text="Product is visible in store"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Show on featured section"
    )
    is_new = models.BooleanField(
        default=False,
        help_text="Mark as new arrival"
    )
    is_best_seller = models.BooleanField(
        default=False,
        help_text="Mark as best seller"
    )
    is_customizable = models.BooleanField(
        default=False,
        help_text="Can be customized"
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Available for order"
    )
    is_pre_order = models.BooleanField(
        default=False,
        help_text="Available for pre-order"
    )
    
    # ============================================
    # Customization Options (for custom cakes)
    # ============================================
    customization_options = models.JSONField(
        default=dict, 
        blank=True,
        null= True,
        help_text="Available customization options"
    )
    
    # ============================================
    # Shipping
    # ============================================
    weight = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0.00, 
        help_text="Weight in grams"
    )
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        help_text="Dimensions (L x W x H) in cm"
    )
    delivery_charge = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        help_text="Additional delivery charge if any"
    )
    is_free_delivery = models.BooleanField(
        default=False,
        help_text="Free delivery available"
    )
    
    # ============================================
    # SEO
    # ============================================
    meta_title = models.CharField(
        max_length=200, 
        blank=True,
        help_text="SEO title"
    )
    meta_description = models.TextField(
        blank=True,
        help_text="SEO description"
    )
    meta_keywords = models.CharField(
        max_length=200, 
        blank=True,
        help_text="SEO keywords"
    )
    
    # ============================================
    # Timestamps
    # ============================================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['category']),
        ]
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            self.sku = self.generate_sku()
        super().save(*args, **kwargs)
    
    def generate_sku(self):
        """Generate unique SKU for product"""
        prefix = ''.join([w[0].upper() for w in self.name.split()[:2]])
        if not prefix:
            prefix = 'CAK'
        code = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}-{code}"
    
    # ============================================
    # Properties
    # ============================================
    
    @property
    def is_low_stock(self):
        """Check if product is low in stock"""
        return self.quantity <= self.min_stock_level
    
    @property
    def is_out_of_stock(self):
        """Check if product is out of stock"""
        return self.quantity <= 0
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.discount_price and self.price > 0:
            return round(
                ((self.price - self.discount_price) / self.price) * 100, 
                2
            )
        return 0
    
    @property
    def final_price(self):
        """Get final price (discounted if available)"""
        return self.discount_price if self.discount_price else self.price

    
    @property
    def stock_value(self):
        """Calculate total stock value"""
        return self.quantity * self.price
    
    @property
    def has_customization(self):
        """Check if product has customization options"""
        return self.is_customizable and bool(self.customization_options)
    
    @property
    def ingredients_list(self):
        """Get ingredients as list of strings"""
        if isinstance(self.ingredients, list):
            return self.ingredients
        return []
    
    @property
    def rating_average(self):
        """Calculate average rating (if reviews exist)"""
        return 0
    
    @property
    def total_reviews(self):
        """Get total number of reviews"""
        return 0
    
    @property
    def total_sold(self):
        """Get total quantity sold"""
        return 0
    
    # ============================================
    # Methods
    # ============================================
    
    def reduce_stock(self, quantity):
        """Reduce stock by given quantity"""
        if self.quantity >= quantity:
            self.quantity -= quantity
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity):
        """Increase stock by given quantity"""
        self.quantity += quantity
        self.save()
        return True
    
    def is_available_for_order(self, quantity):
        """Check if product is available for order"""
        if not self.is_available:
            return False
        if not self.is_active:
            return False
        if self.is_out_of_stock:
            return False
        if self.quantity < quantity:
            return False
        return True
    
    def get_customization_options(self):
        """Get available customization options"""
        if not self.has_customization:
            return {}
        return self.customization_options