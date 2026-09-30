# category/tests/test_serializers.py

import pytest
from category.serializers import CategorySerializer, CategoryListSerializer
from category.models import Category


@pytest.mark.django_db
class TestCategorySerializer:
    """Test Category Serializer"""

    def test_category_serializer_fields(self, category):
        """Test category serializer fields"""
        serializer = CategorySerializer(category)
        data = serializer.data
        
        assert data['id'] == str(category.id)
        assert data['name'] == category.name
        assert data['slug'] == category.slug
        assert data['is_active'] is True
        assert 'product_count' in data
        assert 'subcategories' in data
        assert 'image_url' in data

    def test_category_serializer_with_subcategories(self, category, subcategory):
        """Test category serializer with subcategories"""
        serializer = CategorySerializer(category)
        data = serializer.data
        
        assert len(data['subcategories']) == 1
        assert data['subcategories'][0]['id'] == str(subcategory.id)
        assert data['subcategories'][0]['name'] == subcategory.name

    def test_category_list_serializer(self, category):
        """Test category list serializer"""
        serializer = CategoryListSerializer(category)
        data = serializer.data
        
        assert data['id'] == str(category.id)
        assert data['name'] == category.name
        assert 'product_count' in data
        assert 'subcategory_count' in data
        assert 'image_url' in data

    def test_category_serializer_image_url(self, category):
        """Test category image URL"""
        serializer = CategorySerializer(category)
        data = serializer.data
        
        # Without image should return None
        assert data['image_url'] is None

    def test_category_serializer_full_name(self, category, subcategory):
        """Test category full name"""
        serializer = CategorySerializer(subcategory)
        data = serializer.data
        
        assert data['full_name'] == f"{category.name} → {subcategory.name}"