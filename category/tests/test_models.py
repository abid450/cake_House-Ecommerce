# category/tests/test_models.py

import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from category.models import Category, DessertType


@pytest.mark.django_db
class TestCategoryModel:
    """Test Category Model"""

    def test_category_creation(self):
        """Test category creation"""
        category = Category.objects.create(
            name='Test Category',
            description='Test description'
        )
        
        assert category.name == 'Test Category'
        assert category.slug == 'test-category'
        assert category.is_active is True
        assert str(category) == 'Test Category'

    def test_category_unique_name(self):
        """Test category unique name constraint"""
        Category.objects.create(name='Unique Category')
        
        with pytest.raises(IntegrityError):
            Category.objects.create(name='Unique Category')

    def test_category_slug_auto_generate(self):
        """Test category slug auto-generation"""
        category = Category.objects.create(name='New Category')
        assert category.slug == 'new-category'

    def test_category_string_representation(self):
        """Test category string representation"""
        category = Category.objects.create(name='My Category')
        assert str(category) == 'My Category'

    def test_category_ordering(self):
        """Test category ordering by display_order"""
        cat1 = Category.objects.create(name='A Category', display_order=2)
        cat2 = Category.objects.create(name='B Category', display_order=1)
        
        categories = Category.objects.all()
        assert categories[0] == cat2
        assert categories[1] == cat1


@pytest.mark.django_db
class TestDessertTypeModel:
    """Test Dessert Type Model"""

    def test_dessert_type_creation(self):
        """Test dessert type creation"""
        dt = DessertType.objects.create(name='Cake', icon='fa-cake')
        
        assert dt.name == 'Cake'
        assert dt.slug == 'cake'
        assert dt.is_active is True
        assert str(dt) == 'Cake'

    def test_dessert_type_slug_auto_generate(self):
        """Test dessert type slug auto-generation"""
        dt = DessertType.objects.create(name='Cupcake')
        assert dt.slug == 'cupcake'

    def test_dessert_type_unique_name(self):
        """Test dessert type unique name constraint"""
        DessertType.objects.create(name='Brownie')
        
        with pytest.raises(IntegrityError):
            DessertType.objects.create(name='Brownie')