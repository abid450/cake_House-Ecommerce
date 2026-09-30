# apps/category/tests/test_urls.py
import pytest
from django.urls import reverse, resolve


class TestCategoryURLs:
    """Test Category URLs"""

    def test_category_list_url(self):
        url = reverse('categories-list')
        assert url == '/api/categories/'

    def test_category_tree_url(self):
        url = reverse('categories-tree')
        assert url == '/api/categories/tree/'

    def test_category_products_url(self):
        url = reverse('categories-products', args=['123e4567-e89b-12d3-a456-426614174000'])
        assert url == '/api/categories/123e4567-e89b-12d3-a456-426614174000/products/'