# apps/category/views.py

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import Category, DessertType
from .serializers import (
    CategorySerializer, CategoryListSerializer, CategoryDetailSerializer,
    CategoryCreateUpdateSerializer, CategoryTreeSerializer,
    CategoryBreadcrumbSerializer, DessertTypeSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """Category ViewSet - Complete CRUD with filtering"""
    
    queryset = Category.objects.select_related('parent').prefetch_related('subcategories').filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'display_order', 'created_at']
    ordering = ['display_order', 'name']
    filterset_fields = ['is_active', 'is_featured', 'parent']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CategoryListSerializer
        elif self.action == 'retrieve':
            return CategoryDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateUpdateSerializer
        elif self.action == 'tree':
            return CategoryTreeSerializer
        elif self.action == 'breadcrumb':
            return CategoryBreadcrumbSerializer
        return CategorySerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    
    # ============================================
    # LIST - Context সহ Serializer
    # ============================================
    def list(self, request, *args, **kwargs):
        """Get list of categories with image URLs"""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, 
                many=True, 
                context={'request': request}  
            )
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(
            queryset, 
            many=True, 
            context={'request': request}  
        )
        return Response(serializer.data)
    
    # ============================================
    # RETRIEVE - Context সহ Serializer
    # ============================================
    def retrieve(self, request, *args, **kwargs):
        """Get category detail with image URL"""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            context={'request': request}  
        )
        return Response(serializer.data)
    
    # ============================================
    # Get Category Tree
    # ============================================
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree (hierarchical)"""
        root_categories = Category.objects.filter(
            parent__isnull=True,
            is_active=True
        )
        
        serializer = CategoryTreeSerializer(
            root_categories, 
            many=True,
            context={'request': request}  
        )
        return Response({
            'count': root_categories.count(),
            'results': serializer.data
        })
    
    # ============================================
    # Get Category Breadcrumb
    # ============================================
    @action(detail=True, methods=['get'])
    def breadcrumb(self, request, pk=None):
        """Get breadcrumb path for a category"""
        category = self.get_object()
        
        breadcrumb = []
        current = category
        
        while current:
            breadcrumb.insert(0, {
                'id': str(current.id),
                'name': current.name,
                'slug': current.slug,
                'url': f'/category/{current.slug}/'
            })
            current = current.parent
        
        return Response({
            'category_id': str(category.id),
            'category_name': category.name,
            'breadcrumb': breadcrumb
        })
    
    # ============================================
    # Get Featured Categories
    # ============================================
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured categories"""
        categories = self.get_queryset().filter(
            is_featured=True,
            is_active=True
        )[:8]
        
        serializer = self.get_serializer(
            categories, 
            many=True,
            context={'request': request}  
        )
        return Response({
            'count': categories.count(),
            'results': serializer.data
        })
    
    # ============================================
    # Get Categories with Products
    # ============================================
    @action(detail=False, methods=['get'])
    def with_products(self, request):
        """Get categories that have at least one product"""
        categories = Category.objects.filter(
            is_active=True,
            products__is_active=True
        ).distinct()
        
        # Annotate with product count
        categories = categories.annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('-product_count')
        
        serializer = self.get_serializer(
            categories, 
            many=True,
            context={'request': request}  
        )
        return Response({
            'count': categories.count(),
            'results': serializer.data
        })
    
    # ============================================
    # Get Category Products
    # ============================================
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products in a category"""
        category = self.get_object()
        
        # Import Product serializer here to avoid circular import
        from products.serializers import ProductListSerializer
        from products.models import Product
        
        products = Product.objects.filter(
            category=category,
            is_active=True
        )
        
        # Filters
        is_available = request.query_params.get('is_available')
        if is_available is not None:
            is_available = is_available.lower() == 'true'
            products = products.filter(is_available=is_available)
        
        is_customizable = request.query_params.get('is_customizable')
        if is_customizable is not None:
            is_customizable = is_customizable.lower() == 'true'
            products = products.filter(is_customizable=is_customizable)
        
        # Price range
        min_price = request.query_params.get('min_price')
        if min_price:
            products = products.filter(price__gte=min_price)
        
        max_price = request.query_params.get('max_price')
        if max_price:
            products = products.filter(price__lte=max_price)
        
        # Order by
        order_by = request.query_params.get('order_by', '-created_at')
        products = products.order_by(order_by)
        
        serializer = ProductListSerializer(
            products, 
            many=True,
            context={'request': request}  # 
        )
        
        return Response({
            'category': {
                'id': str(category.id),
                'name': category.name,
                'slug': category.slug
            },
            'products': serializer.data,
            'count': products.count()
        })


class DessertTypeViewSet(viewsets.ModelViewSet):
    """Dessert Type ViewSet"""
    
    queryset = DessertType.objects.filter(is_active=True)
    serializer_class = DessertTypeSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()