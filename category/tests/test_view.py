# category/tests/test_views.py

import pytest
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from category.models import Category, DessertType
from products.models import Product

User = get_user_model()


@pytest.mark.django_db
class TestCategoryViews:
    """Test Category API Views"""

    # ============================================
    # 1. LIST TESTS
    # ============================================

    def test_category_list_success(self, api_client, category):
        """Test GET /api/categories/ - Success"""
        url = reverse('categories-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'results' in response.data
        assert response.data['count'] >= 1

    def test_category_list_with_filters(self, api_client, category):
        """Test GET /api/categories/ with filters"""
        url = reverse('categories-list')
        
        response = api_client.get(url, {'is_active': 'true'})
        assert response.status_code == status.HTTP_200_OK

        category.is_featured = True
        category.save()
        response = api_client.get(url, {'is_featured': 'true'})
        assert response.status_code == status.HTTP_200_OK

    def test_category_list_with_search(self, api_client, category):
        """Test GET /api/categories/ with search"""
        url = reverse('categories-list')
        
        response = api_client.get(url, {'search': 'Test'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

        response = api_client.get(url, {'search': 'NonExistent'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_category_list_pagination(self, api_client):
        """Test GET /api/categories/ with pagination"""
        for i in range(15):
            Category.objects.create(
                name=f'Category {i}',
                slug=f'category-{i}',
                is_active=True
            )
        
        url = reverse('categories-list')
        
        response = api_client.get(url, {'page': 1})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) <= 12
        assert response.data['count'] >= 15

        response = api_client.get(url, {'page': 2})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_category_list_ordering(self, api_client):
        """Test GET /api/categories/ with ordering"""
        Category.objects.create(name='A Category', display_order=2, is_active=True)
        Category.objects.create(name='B Category', display_order=1, is_active=True)
        
        url = reverse('categories-list')
        
        response = api_client.get(url, {'ordering': 'display_order'})
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        if len(results) >= 2:
            assert results[0]['display_order'] <= results[1]['display_order']

    # ============================================
    # 2. RETRIEVE TESTS
    # ============================================

    def test_category_retrieve_success(self, api_client, category):
        """Test GET /api/categories/{id}/ - Success"""
        url = reverse('categories-detail', args=[category.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(category.id)
        assert response.data['name'] == category.name
        assert response.data['slug'] == category.slug
        assert 'product_count' in response.data
        assert 'subcategories' in response.data

    def test_category_retrieve_with_subcategories(self, api_client, category, subcategory):
        """Test GET /api/categories/{id}/ with subcategories"""
        url = reverse('categories-detail', args=[category.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['subcategories']) == 1
        assert response.data['subcategories'][0]['id'] == str(subcategory.id)

    def test_category_retrieve_not_found(self, api_client):
        """Test GET /api/categories/{id}/ - Not Found"""
        url = reverse('categories-detail', args=['12345678-1234-1234-1234-123456789012'])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_category_retrieve_inactive(self, api_client):
        """Test GET /api/categories/{id}/ - Inactive category should not be found"""
        category = Category.objects.create(
            name='Inactive Category',
            slug='inactive-category',
            is_active=False
        )
        url = reverse('categories-detail', args=[category.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ============================================
    # 3. CREATE TESTS
    # ============================================

    def test_category_create_unauthorized(self, api_client):
        """Test POST /api/categories/ without authentication"""
        url = reverse('categories-list')
        data = {
            'name': 'New Category',
            'description': 'New category description'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_category_create_authorized(self, api_client, admin_user):
        """Test POST /api/categories/ with admin authentication"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-list')
        data = {
            'name': 'Admin Category',
            'description': 'Created by admin',
            'is_active': True
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Admin Category'
        assert Category.objects.filter(name='Admin Category').exists()

    def test_category_create_with_parent(self, api_client, admin_user, category):
        """Test POST /api/categories/ with parent category"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-list')
        data = {
            'name': 'Child Category',
            'parent': str(category.id),
            'is_active': True
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert str(response.data['parent']) == str(category.id)
        child = Category.objects.get(id=response.data['id'])
        assert child.parent == category

    def test_category_create_duplicate_name(self, api_client, admin_user, category):
        """Test POST /api/categories/ with duplicate name"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-list')
        data = {
            'name': category.name,
            'description': 'Duplicate category'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_category_create_invalid_data(self, api_client, admin_user):
        """Test POST /api/categories/ with invalid data"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-list')
        data = {
            'name': '',  # Empty name
            'description': 'Invalid category'
        }
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ============================================
    # 4. UPDATE TESTS
    # ============================================

    def test_category_update_unauthorized(self, api_client, category):
        """Test PUT /api/categories/{id}/ without authentication"""
        url = reverse('categories-detail', args=[category.id])
        data = {'name': 'Updated Name'}
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_category_update_authorized(self, api_client, admin_user, category):
        """Test PUT /api/categories/{id}/ with admin authentication"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-detail', args=[category.id])
        data = {
            'name': 'Updated Category Name',
            'description': 'Updated description',
            'is_active': True
        }
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.name == 'Updated Category Name'
        assert category.description == 'Updated description'

    def test_category_partial_update(self, api_client, admin_user, category):
        """Test PATCH /api/categories/{id}/ with partial update"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-detail', args=[category.id])
        
        data = {
            'name': category.name,
            'description': category.description,
            'is_active': category.is_active,
            'is_featured': True,
            'display_order': category.display_order
        }
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.is_featured is True

    def test_category_partial_update_single_field(self, api_client, admin_user, category):
        """Test PATCH /api/categories/{id}/ with single field update"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-detail', args=[category.id])
        
        # ✅ is_featured আপডেট করুন (display_order না)
        data = {'is_featured': True}
        response = api_client.patch(url, data, format='json')
        
        # ✅ এখন 200 আসবে
        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.is_featured is True

    def test_category_update_not_found(self, api_client, admin_user):
        """Test PUT /api/categories/{id}/ - Not Found"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-detail', args=['12345678-1234-1234-1234-123456789012'])
        data = {'name': 'Updated Name'}
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ============================================
    # 5. DELETE TESTS
    # ============================================

    def test_category_delete_unauthorized(self, api_client, category):
        """Test DELETE /api/categories/{id}/ without authentication"""
        url = reverse('categories-detail', args=[category.id])
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_category_delete_authorized(self, api_client, admin_user, category):
        """Test DELETE /api/categories/{id}/ with admin authentication"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-detail', args=[category.id])
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Category.objects.filter(id=category.id).exists()

    def test_category_delete_not_found(self, api_client, admin_user):
        """Test DELETE /api/categories/{id}/ - Not Found"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-detail', args=['12345678-1234-1234-1234-123456789012'])
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_category_delete_with_children(self, api_client, admin_user, category, subcategory):
        """Test DELETE /api/categories/{id}/ with children"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('categories-detail', args=[category.id])
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Category.objects.filter(id=category.id).exists()
        assert not Category.objects.filter(id=subcategory.id).exists()

    # ============================================
    # 6. CUSTOM ACTION TESTS
    # ============================================

    def test_category_tree_success(self, api_client, category, subcategory):
        """Test GET /api/categories/tree/ - Success"""
        url = reverse('categories-tree')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'results' in response.data
        assert response.data['count'] >= 1

    def test_category_tree_empty(self, api_client):
        """Test GET /api/categories/tree/ - Empty"""
        Category.objects.all().delete()
        
        url = reverse('categories-tree')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert response.data['results'] == []

    def test_category_breadcrumb_success(self, api_client, category, subcategory):
        """Test GET /api/categories/{id}/breadcrumb/ - Success"""
        url = reverse('categories-breadcrumb', args=[subcategory.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['category_id'] == str(subcategory.id)
        assert response.data['category_name'] == subcategory.name
        assert len(response.data['breadcrumb']) == 2
        assert response.data['breadcrumb'][0]['name'] == category.name
        assert response.data['breadcrumb'][1]['name'] == subcategory.name

    def test_category_breadcrumb_root(self, api_client, category):
        """Test GET /api/categories/{id}/breadcrumb/ - Root category"""
        url = reverse('categories-breadcrumb', args=[category.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['category_id'] == str(category.id)
        assert len(response.data['breadcrumb']) == 1

    def test_category_breadcrumb_not_found(self, api_client):
        """Test GET /api/categories/{id}/breadcrumb/ - Not Found"""
        url = reverse('categories-breadcrumb', args=['12345678-1234-1234-1234-123456789012'])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_category_featured_success(self, api_client, category):
        """Test GET /api/categories/featured/ - Success"""
        category.is_featured = True
        category.save()
        
        url = reverse('categories-featured')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_category_featured_empty(self, api_client):
        """Test GET /api/categories/featured/ - Empty"""
        Category.objects.all().update(is_featured=False)
        
        url = reverse('categories-featured')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_category_with_products_success(self, api_client, category, product):
        """Test GET /api/categories/with_products/ - Success"""
        url = reverse('categories-with-products')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_category_products_success(self, api_client, category, product):
        """Test GET /api/categories/{id}/products/ - Success"""
        url = reverse('categories-products', args=[category.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['products']) == 1
        assert response.data['products'][0]['id'] == str(product.id)

    def test_category_products_with_filters(self, api_client, category, product):
        """Test GET /api/categories/{id}/products/ with filters"""
        url = reverse('categories-products', args=[category.id])
        
        response = api_client.get(url, {'is_available': 'true'})
        assert response.status_code == status.HTTP_200_OK
        
        response = api_client.get(url, {'min_price': '50'})
        assert response.status_code == status.HTTP_200_OK
        
        response = api_client.get(url, {'max_price': '50'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    def test_category_products_empty(self, api_client):
        """Test GET /api/categories/{id}/products/ - No products"""
        empty_category = Category.objects.create(
            name='Empty Category',
            slug='empty-category',
            is_active=True
        )
        
        url = reverse('categories-products', args=[empty_category.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert response.data['products'] == []

    def test_category_products_not_found(self, api_client):
        """Test GET /api/categories/{id}/products/ - Not Found"""
        url = reverse('categories-products', args=['12345678-1234-1234-1234-123456789012'])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ============================================
    # 7. PERMISSION TESTS
    # ============================================

    def test_admin_permission_for_create(self, api_client, user):
        """Test that non-admin cannot create category"""
        api_client.force_authenticate(user=user)
        url = reverse('categories-list')
        data = {'name': 'Test Category'}
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_permission_for_update(self, api_client, user, category):
        """Test that non-admin cannot update category"""
        api_client.force_authenticate(user=user)
        url = reverse('categories-detail', args=[category.id])
        data = {'name': 'Updated Name'}
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_permission_for_delete(self, api_client, user, category):
        """Test that non-admin cannot delete category"""
        api_client.force_authenticate(user=user)
        url = reverse('categories-detail', args=[category.id])
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_public_access_for_list(self, api_client):
        """Test that public can access category list"""
        url = reverse('categories-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK

    def test_public_access_for_retrieve(self, api_client, category):
        """Test that public can access category detail"""
        url = reverse('categories-detail', args=[category.id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK