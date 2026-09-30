# apps/products/views.py

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F
from .models import Product
from .serializers import (
    ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer
)


class ProductViewSet(viewsets.ModelViewSet):
    """Product ViewSet - Complete CRUD with filtering and search"""
    
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'barcode', 'description']
    ordering_fields = ['name', 'price', 'quantity', 'created_at', 'updated_at']
    ordering = ['-created_at']
    filterset_fields = [
        'category', 'dessert_type', 'is_active', 'is_featured', 
        'is_new', 'is_best_seller', 'is_customizable', 'is_available', 'is_pre_order'
    ]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'retrieve':
            return ProductDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductListSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    
    # List with context
    def list(self, request, *args, **kwargs):
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
    
    # Retrieve with context
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, 
            context={'request': request}
        )
        
        # Get related products
        related_products = Product.objects.filter(
            Q(category=instance.category) | Q(dessert_type=instance.dessert_type),
            is_active=True
        ).exclude(id=instance.id)[:8]
        
        return Response({
            'success': True,
            'data': {
                'product': serializer.data,
                'related_products': ProductListSerializer(
                    related_products, 
                    many=True,
                    context={'request': request}
                ).data,
                'related_count': related_products.count()
            }
        })
    
    # ============================================
    # Featured Products
    # ============================================
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        products = self.get_queryset().filter(is_featured=True)[:8]
        serializer = self.get_serializer(
            products, 
            many=True,
            context={'request': request}
        )
        return Response({
            'count': products.count(),
            'results': serializer.data
        })
    
    # ============================================
    # New Arrivals
    # ============================================
    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        """Get new arrivals"""
        products = self.get_queryset().filter(is_new=True)[:8]
        serializer = self.get_serializer(
            products, 
            many=True,
            context={'request': request}
        )
        return Response({
            'count': products.count(),
            'results': serializer.data
        })
    
    # ============================================
    # Best Sellers
    # ============================================
    @action(detail=False, methods=['get'])
    def best_sellers(self, request):
        """Get best selling products"""
        products = self.get_queryset().filter(is_best_seller=True)[:8]
        serializer = self.get_serializer(
            products, 
            many=True,
            context={'request': request}
        )
        return Response({
            'count': products.count(),
            'results': serializer.data
        })
    
    # ============================================
    # Low Stock Products
    # ============================================
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock products"""
        products = Product.objects.filter(
            quantity__lte=F('min_stock_level'),
            is_active=True
        )
        serializer = self.get_serializer(
            products, 
            many=True,
            context={'request': request}
        )
        return Response({
            'count': products.count(),
            'results': serializer.data
        })
    
    # ============================================
    # Out of Stock Products
    # ============================================
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get all out of stock products"""
        products = Product.objects.filter(
            quantity=0,
            is_active=True
        )
        serializer = self.get_serializer(
            products, 
            many=True,
            context={'request': request}
        )
        return Response({
            'count': products.count(),
            'results': serializer.data
        })
    
    # ============================================
    # Available Products
    # ============================================
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get all available products"""
        products = self.get_queryset().filter(
            is_available=True,
            quantity__gt=0
        )
        serializer = self.get_serializer(
            products, 
            many=True,
            context={'request': request}
        )
        return Response({
            'count': products.count(),
            'results': serializer.data
        })
    
    # ============================================
    # Customizable Products
    # ============================================
    @action(detail=False, methods=['get'])
    def customizable(self, request):
        """Get all customizable products"""
        products = self.get_queryset().filter(is_customizable=True)
        serializer = self.get_serializer(
            products, 
            many=True,
            context={'request': request}
        )
        return Response({
            'count': products.count(),
            'results': serializer.data
        })
    
    # ============================================
    # Update Stock
    # ============================================
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update product stock"""
        product = self.get_object()
        quantity = request.data.get('quantity')
        
        if quantity is None:
            return Response(
                {'error': 'Quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quantity = int(quantity)
            if quantity < 0:
                return Response(
                    {'error': 'Quantity cannot be negative'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            product.quantity = quantity
            product.save()
            
            return Response({
                'success': True,
                'message': 'Stock updated successfully',
                'data': {
                    'product_id': str(product.id),
                    'name': product.name,
                    'quantity': product.quantity,
                    'is_low_stock': product.is_low_stock,
                    'is_out_of_stock': product.is_out_of_stock
                }
            })
            
        except ValueError:
            return Response(
                {'error': 'Invalid quantity value'},
                status=status.HTTP_400_BAD_REQUEST
            )