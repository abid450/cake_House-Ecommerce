# apps/products/serializers.py

from rest_framework import serializers
from .models import Product
from category.models import Category, DessertType


class CategorySerializer(serializers.ModelSerializer):
    """Category Serializer"""
    
    product_count = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image', 'icon',
            'parent', 'subcategories', 'is_active', 'is_featured',
            'display_order', 'product_count', 'created_at', 'updated_at'
        ]
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    
    def get_subcategories(self, obj):
        return CategorySerializer(
            obj.subcategories.filter(is_active=True),
            many=True
        ).data


class DessertTypeSerializer(serializers.ModelSerializer):
    """Dessert Type Serializer"""
    
    class Meta:
        model = DessertType
        fields = ['id', 'name', 'slug', 'icon', 'is_active']


class ProductListSerializer(serializers.ModelSerializer):
    """Basic Product Serializer for Listing"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    dessert_type_name = serializers.CharField(source='dessert_type.name', read_only=True, allow_null=True)
    final_price = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    discount_percentage = serializers.FloatField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_out_of_stock = serializers.BooleanField(read_only=True)
    
    
    class Meta:
        model = Product
        fields = [
            # Basic
            'id', 'name', 'slug', 'sku', 'barcode',
            
            # Category
            'category', 'category_name', 'category_slug',
            'dessert_type', 'dessert_type_name',
            
            # Pricing
            'price', 'discount_price', 'final_price', 'discount_percentage',
            
            # Stock
            'quantity', 'min_stock_level', 'is_low_stock', 'is_out_of_stock',
            
            # Details
            'description', 'preparation_time', 'shelf_life', 'serving_size',
            
            # Images
            'main_image', 'gallery_images', 'video_url',
            
            # Status
            'is_active', 'is_featured', 'is_new', 'is_best_seller',
            'is_customizable', 'is_available', 'is_pre_order',
            
            # Shipping
            'weight', 'dimensions', 'delivery_charge', 'is_free_delivery',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
    
    

class ProductDetailSerializer(serializers.ModelSerializer):
    """Complete Product Detail Serializer"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    dessert_type_name = serializers.CharField(source='dessert_type.name', read_only=True, allow_null=True)
    final_price = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    discount_percentage = serializers.FloatField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_out_of_stock = serializers.BooleanField(read_only=True)
    has_customization = serializers.BooleanField(read_only=True)
    ingredients_list = serializers.ListField(read_only=True)
    
    
    class Meta:
        model = Product
        fields = [
            # Basic
            'id', 'name', 'slug', 'sku', 'barcode',
            
            # Category
            'category', 'category_name', 'category_slug',
            'dessert_type', 'dessert_type_name',
            
            # Pricing
            'price', 'discount_price', 'final_price', 'discount_percentage',
            
            # Stock & Ingredients
            'quantity', 'min_stock_level', 'ingredients', 'ingredients_list',
            'is_low_stock', 'is_out_of_stock',
            
            # Details
            'description', 'preparation_time', 'shelf_life', 'serving_size',
            
            # Images
            'main_image', 'gallery_images', 'video_url',
            
            # Status
            'is_active', 'is_featured', 'is_new', 'is_best_seller',
            'is_customizable', 'is_available', 'is_pre_order',
            'has_customization',
            
            # Customization
            'customization_options',
            
            # Shipping
            'weight', 'dimensions', 'delivery_charge', 'is_free_delivery',
            
            # SEO
            'meta_title', 'meta_description', 'meta_keywords',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
    


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for Creating and Updating Products"""
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'sku', 'slug', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate product data"""
        # Check if price is valid
        if data.get('price', 0) < 0:
            raise serializers.ValidationError({"price": "Price cannot be negative"})
        
        # Check if discount price is valid
        if data.get('discount_price') and data.get('discount_price') > data.get('price', 0):
            raise serializers.ValidationError(
                {"discount_price": "Discount price cannot be greater than regular price"}
            )
        
        # Check if quantity is valid
        if data.get('quantity', 0) < 0:
            raise serializers.ValidationError({"quantity": "Quantity cannot be negative"})
        
        # Check if min_stock_level is valid
        if data.get('min_stock_level', 0) < 0:
            raise serializers.ValidationError({"min_stock_level": "Minimum stock level cannot be negative"})
        
        return data