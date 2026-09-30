# apps/category/serializers.py

from rest_framework import serializers
from .models import Category, DessertType


class DessertTypeSerializer(serializers.ModelSerializer):
    """Dessert Type Serializer"""
    
    class Meta:
        model = DessertType
        fields = [
            'id', 
            'name', 
            'slug', 
            'icon', 
            'is_active'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    """Category Serializer with Subcategories and Product Count"""
    
    # Nested subcategories
    #subcategories = serializers.SerializerMethodField()
    
    # Product count
    product_count = serializers.SerializerMethodField()
    
    # Full name (with parent)
    full_name = serializers.SerializerMethodField()
    
    # Parent category details
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    parent_id = serializers.UUIDField(source='parent.id', read_only=True, allow_null=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            # Basic
            'id', 
            'name', 
            'slug', 
            'description',
            
            # Image & Icon
            'image_url', 
            'icon',
            
            # Parent
            'parent', 
            'parent_name',
            'parent_id',
            #'subcategories',
            
            # Status
            'is_active', 
            'is_featured',
            
            # Order
            'display_order',
            
            # Computed
            'product_count',
            'full_name',
            
            # SEO
            'meta_title', 
            'meta_description', 
            'meta_keywords',
            
            # Timestamps
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
        depth = 1 


    def get_image_url(self, obj):
        """Get full URL of category image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    
    def get_product_count(self, obj):
        """Get count of active products in this category"""
        return obj.products.filter(is_active=True).count()
    
    
    def get_full_name(self, obj):
        """Get full name with parent"""
        if obj.parent:
            return f"{obj.parent.name} → {obj.name}"
        return obj.name



class CategoryListSerializer(serializers.ModelSerializer):
    """Simplified Category Serializer for List View"""
    
    product_count = serializers.SerializerMethodField()
    subcategory_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    
    class Meta:
        model = Category
        fields = [
            'id', 
            'name', 
            'slug', 
            'icon', 
            'image_url',
            'is_active',
            'is_featured',
            'display_order',
            'product_count',
            'subcategory_count'
        ]

        depth = 1 



    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

    def get_subcategory_count(self, obj):
        """Get count of active subcategories"""
        return obj.subcategories.filter(is_active=True).count()


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Detailed Category Serializer with Full Subcategories"""
    
    subcategories = CategorySerializer(many=True, read_only=True)
    parent_details = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            # Basic
            'id', 
            'name', 
            'slug', 
            'description',
            
            # Image & Icon
            'image', 
            'icon',
            
            # Parent
            'parent',
            'parent_details',
            'subcategories',
            
            # Status
            'is_active', 
            'is_featured',
            
            # Order
            'display_order',
            
            # Computed
            'product_count',
            'full_name',
            
            # SEO
            'meta_title', 
            'meta_description', 
            'meta_keywords',
            
            # Timestamps
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
        depth = 1 


    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    
    def get_full_name(self, obj):
        if obj.parent:
            return f"{obj.parent.name} → {obj.name}"
        return obj.name
    
    def get_subcategories(self, obj):
        subcategories = obj.subcategories.filter(is_active=True)
        return CategorySerializer(subcategories, many=True, context=self.context).data
    
    def get_parent_details(self, obj):
        """Get parent category details"""
        if obj.parent:
            return {
                'id': str(obj.parent.id),
                'name': obj.parent.name,
                'slug': obj.parent.slug
            }
        return None


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for Creating and Updating Categories"""
    
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate category data"""
        # Check if name is provided
        if not data.get('name'):
            raise serializers.ValidationError({"name": "Category name is required"})
        
        # Check if parent is valid (cannot be self)
        if data.get('parent') and data.get('parent') == self.instance:
            raise serializers.ValidationError(
                {"parent": "A category cannot be its own parent"}
            )
        
        # Check for duplicate names (excluding current instance)
        name = data.get('name')
        if name:
            queryset = Category.objects.filter(name__iexact=name)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"name": f"Category with name '{name}' already exists"}
                )
        
        return data


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Category Tree Serializer for Hierarchical Display"""
    
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    
    class Meta:
        model = Category
        fields = [
            'id', 
            'name', 
            'slug', 
            'icon',
            'is_active',
            'display_order',
            'product_count',
            'children'
        ]
    
    def get_children(self, obj):
        """Get children categories recursively"""
        children = obj.subcategories.filter(is_active=True)
        return CategoryTreeSerializer(children, many=True).data

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

    
class CategoryBreadcrumbSerializer(serializers.Serializer):
    """Category Breadcrumb Serializer"""
    
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    url = serializers.CharField()