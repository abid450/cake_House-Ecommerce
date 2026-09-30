# category/tests/conftest.py

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from category.models import Category, DessertType
from products.models import Product

User = get_user_model()


@pytest.fixture
def api_client():
    """Return API client for testing"""
    return APIClient()


@pytest.fixture
def user():
    """Create a test user"""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        username='testuser'
    )


@pytest.fixture
def admin_user():
    """Create a test admin user"""
    return User.objects.create_superuser(
        email='admin@example.com',
        password='adminpass123',
        username='admin'
    )


@pytest.fixture
def category():
    """Create a test category"""
    return Category.objects.create(
        name='Test Category',
        slug='test-category',
        description='Test category description',
        is_active=True
    )


@pytest.fixture
def subcategory(category):
    """Create a test subcategory"""
    return Category.objects.create(
        name='Test Subcategory',
        slug='test-subcategory',
        description='Test subcategory description',
        parent=category,
        is_active=True
    )


@pytest.fixture
def dessert_type():
    """Create a test dessert type"""
    return DessertType.objects.create(
        name='Cake',
        slug='cake',
        icon='fa-cake',
        is_active=True
    )


@pytest.fixture
def product(category, dessert_type):
    """Create a test product"""
    return Product.objects.create(
        name='Test Product',
        slug='test-product',
        sku='TEST-001',
        category=category,
        dessert_type=dessert_type,
        price=100.00,
        discount_price=80.00,
        quantity=10,
        min_stock_level=5,
        description='Test product description',
        ingredients=['Flour', 'Sugar', 'Eggs'],
        is_active=True,
        is_featured=True
    )