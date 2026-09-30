# apps/category/filters.py

import django_filters
from django.db.models import Q
from .models import Category


class CategoryFilter(django_filters.FilterSet):
    """Advanced Category Filter"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.UUIDFilter(field_name='parent')
    is_active = django_filters.BooleanFilter(field_name='is_active')
    is_featured = django_filters.BooleanFilter(field_name='is_featured')
    
    has_products = django_filters.BooleanFilter(method='filter_has_products')
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Category
        fields = ['name', 'parent', 'is_active', 'is_featured']
    
    def filter_has_products(self, queryset, name, value):
        """Filter categories that have products"""
        if value:
            return queryset.filter(products__is_active=True).distinct()
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(slug__icontains=value)
        )