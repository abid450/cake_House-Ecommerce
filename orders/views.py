from django.shortcuts import render

# Create your views here.
# order/views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Order, OrderItem, OrderStatusHistory
from .serializers import (
    OrderListSerializer, OrderDetailSerializer,
    OrderCreateSerializer, OrderStatusUpdateSerializer,
    OrderItemSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """Order ViewSet - Complete Order Management"""
    
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'shipping_name', 'shipping_phone']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    filterset_fields = ['status', 'payment_status', 'payment_method']
    
    def get_queryset(self):
        """Admin sees all orders, users see their own"""
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderListSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            self.permission_classes = [AllowAny]
        elif self.action in ['update_status', 'destroy']:
            self.permission_classes = [IsAdminUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    # ============================================
    # Create Order
    # ============================================

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        if order.payment_method == 'cod':
            from .tasks import send_order_confirmation_email
            send_order_confirmation_email.delay(str(order.id))

        return Response({
            'success': True,
            'message': 'অর্ডার সফলভাবে তৈরি হয়েছে।',
            'data': OrderDetailSerializer(order, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

    # ============================================
    # List Orders
    # ============================================
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    # ============================================
    # Retrieve Order
    # ============================================
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    # ============================================
    # Update Order Status
    # ============================================
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        old_status = order.status
        new_status = serializer.validated_data['status']
        
        order.status = new_status
        if serializer.validated_data.get('tracking_number'):
            order.tracking_number = serializer.validated_data['tracking_number']
        if serializer.validated_data.get('tracking_url'):
            order.tracking_url = serializer.validated_data['tracking_url']
        
        if new_status == 'delivered':
            from django.utils import timezone
            order.delivered_at = timezone.now()
        
        order.save()
        
        # Log status change
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            note=serializer.validated_data.get('note', ''),
            changed_by=request.user
        )
        
        # Send status update email
        from .tasks import send_order_status_update_email
        send_order_status_update_email.delay(str(order.id), old_status, new_status)
        
        return Response({
            'success': True,
            'message': f'অর্ডার স্ট্যাটাস আপডেট হয়েছে: {new_status}',
            'data': OrderDetailSerializer(order, context={'request': request}).data
        })
    
    # ============================================
    # Cancel Order
    # ============================================
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel order"""
        order = self.get_object()
        
        if not order.is_cancellable:
            return Response({
                'success': False,
                'message': 'এই অর্ডারটি আর বাতিল করা যাবে না।'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', '')
        order.cancel(reason=reason)
        
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            note=f'Cancelled: {reason}',
            changed_by=request.user
        )
        
        return Response({
            'success': True,
            'message': 'অর্ডার বাতিল করা হয়েছে।',
            'data': OrderDetailSerializer(order, context={'request': request}).data
        })
    
    # ============================================
    # Order Stats (Admin)
    # ============================================
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def stats(self, request):
        """Get order statistics"""
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats = {
            'total_orders': Order.objects.count(),
            'pending_orders': Order.objects.filter(status='pending').count(),
            'processing_orders': Order.objects.filter(status='processing').count(),
            'delivered_orders': Order.objects.filter(status='delivered').count(),
            'cancelled_orders': Order.objects.filter(status='cancelled').count(),
            'today_orders': Order.objects.filter(created_at__date=today).count(),
            'week_orders': Order.objects.filter(created_at__date__gte=week_ago).count(),
            'month_orders': Order.objects.filter(created_at__date__gte=month_ago).count(),
            'total_revenue': Order.objects.filter(payment_status='paid').aggregate(
                total=Sum('total_amount')
            )['total'] or 0,
        }
        
        return Response({
            'success': True,
            'data': stats
        })