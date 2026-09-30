from django.shortcuts import render

# Create your views here.
# dashboard/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from orders.models import Order, OrderItem
from products.models import Product
from category.models import Category
from customers.models import User
from payment.models import Payment


class DashboardStatsView(APIView):
    """Dashboard Statistics API"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        year_ago = today - timedelta(days=365)
        
        # ============================================
        # Revenue Stats
        # ============================================
        total_revenue = Order.objects.filter(
            payment_status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        today_revenue = Order.objects.filter(
            payment_status='paid',
            created_at__date=today
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        week_revenue = Order.objects.filter(
            payment_status='paid',
            created_at__date__gte=week_ago
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        month_revenue = Order.objects.filter(
            payment_status='paid',
            created_at__date__gte=month_ago
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        # ============================================
        # Order Stats
        # ============================================
        total_orders = Order.objects.count()
        today_orders = Order.objects.filter(created_at__date=today).count()
        week_orders = Order.objects.filter(created_at__date__gte=week_ago).count()
        month_orders = Order.objects.filter(created_at__date__gte=month_ago).count()
        
        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status='processing').count()
        shipped_orders = Order.objects.filter(status='shipped').count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        cancelled_orders = Order.objects.filter(status='cancelled').count()
        
        # ============================================
        # Product Stats
        # ============================================
        total_products = Product.objects.filter(is_active=True).count()
        low_stock_products = Product.objects.filter(
            quantity__lte=F('min_stock_level'),
            is_active=True
        ).count()
        out_of_stock_products = Product.objects.filter(
            quantity=0,
            is_active=True
        ).count()
        
        # ============================================
        # Customer Stats
        # ============================================
        total_customers = User.objects.filter(is_staff=False).count()
        new_customers_today = User.objects.filter(
            date_joined__date=today,
            is_staff=False
        ).count()
        new_customers_month = User.objects.filter(
            date_joined__date__gte=month_ago,
            is_staff=False
        ).count()
        
        # ============================================
        # Category Stats
        # ============================================
        total_categories = Category.objects.filter(is_active=True).count()
        
        return Response({
            'success': True,
            'data': {
                'revenue': {
                    'total': float(total_revenue),
                    'today': float(today_revenue),
                    'week': float(week_revenue),
                    'month': float(month_revenue),
                },
                'orders': {
                    'total': total_orders,
                    'today': today_orders,
                    'week': week_orders,
                    'month': month_orders,
                    'pending': pending_orders,
                    'processing': processing_orders,
                    'shipped': shipped_orders,
                    'delivered': delivered_orders,
                    'cancelled': cancelled_orders,
                },
                'products': {
                    'total': total_products,
                    'low_stock': low_stock_products,
                    'out_of_stock': out_of_stock_products,
                },
                'customers': {
                    'total': total_customers,
                    'new_today': new_customers_today,
                    'new_month': new_customers_month,
                },
                'categories': {
                    'total': total_categories,
                }
            }
        })


class RevenueChartView(APIView):
    """Revenue Chart Data (Last 30 days)"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)
        
        # Build date range
        date_range = []
        current = start_date
        while current <= end_date:
            date_range.append(current)
            current += timedelta(days=1)
        
        # Get orders grouped by date
        orders_by_date = Order.objects.filter(
            payment_status='paid',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values('created_at__date').annotate(
            revenue=Sum('total_amount'),
            count=Count('id')
        ).order_by('created_at__date')
        
        # Build lookup dict
        data_lookup = {
            item['created_at__date']: {
                'revenue': float(item['revenue']),
                'orders': item['count']
            }
            for item in orders_by_date
        }
        
        # Build chart data
        chart_data = []
        for date in date_range:
            data = data_lookup.get(date, {'revenue': 0, 'orders': 0})
            chart_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'label': date.strftime('%d %b'),
                'revenue': data['revenue'],
                'orders': data['orders'],
            })
        
        return Response({
            'success': True,
            'data': chart_data
        })


class TopProductsView(APIView):
    """Top Selling Products"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        
        top_products = OrderItem.objects.values(
            'product__id',
            'product__name',
            'product__sku',
            'product__main_image',
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum('total_price'),
            order_count=Count('order', distinct=True)
        ).order_by('-total_sold')[:limit]
        
        data = []
        for item in top_products:
            image_url = None
            if item['product__main_image']:
                image_url = f"/media/{item['product__main_image']}"
            
            data.append({
                'product_id': str(item['product__id']) if item['product__id'] else None,
                'name': item['product__name'],
                'sku': item['product__sku'],
                'image': image_url,
                'total_sold': item['total_sold'],
                'total_revenue': float(item['total_revenue']),
                'order_count': item['order_count'],
            })
        
        return Response({
            'success': True,
            'data': data
        })


class RecentOrdersView(APIView):
    """Recent Orders"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        
        orders = Order.objects.all().order_by('-created_at')[:limit]
        
        data = []
        for order in orders:
            data.append({
                'id': str(order.id),
                'order_number': order.order_number,
                'customer_name': order.shipping_name,
                'customer_phone': order.shipping_phone,
                'total_amount': float(order.total_amount),
                'status': order.status,
                'payment_status': order.payment_status,
                'created_at': order.created_at.isoformat(),
            })
        
        return Response({
            'success': True,
            'data': data
        })


class OrderStatusChartView(APIView):
    """Order Status Distribution"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        status_counts = Order.objects.values('status').annotate(
            count=Count('id')
        )
        
        data = {
            'pending': 0,
            'confirmed': 0,
            'processing': 0,
            'shipped': 0,
            'delivered': 0,
            'cancelled': 0,
            'refunded': 0,
        }
        
        for item in status_counts:
            data[item['status']] = item['count']
        
        return Response({
            'success': True,
            'data': data
        })


class CategorySalesView(APIView):
    """Sales by Category"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        categories = Category.objects.filter(is_active=True).annotate(
            total_sales=Sum('products__order_items__total_price'),
            total_orders=Count('products__order_items__order', distinct=True),
            product_count=Count('products', distinct=True)
        ).order_by('-total_sales')
        
        data = []
        for cat in categories:
            data.append({
                'id': str(cat.id),
                'name': cat.name,
                'total_sales': float(cat.total_sales or 0),
                'total_orders': cat.total_orders or 0,
                'product_count': cat.product_count or 0,
            })
        
        return Response({
            'success': True,
            'data': data
        })


class LowStockProductsView(APIView):
    """Low Stock Products List"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        products = Product.objects.filter(
            quantity__lte=F('min_stock_level'),
            is_active=True
        ).order_by('quantity')[:20]
        
        data = []
        for p in products:
            data.append({
                'id': str(p.id),
                'name': p.name,
                'sku': p.sku,
                'quantity': p.quantity,
                'min_stock_level': p.min_stock_level,
                'image': p.main_image.url if p.main_image else None,
                'is_out_of_stock': p.quantity <= 0,
            })
        
        return Response({
            'success': True,
            'data': data
        })


class PaymentStatsView(APIView):
    """Payment Statistics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        today = timezone.now().date()
        month_ago = today - timedelta(days=30)
        
        # Payment method distribution
        payment_methods = Order.objects.filter(
            payment_status='paid',
            created_at__date__gte=month_ago
        ).values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        method_data = {}
        for item in payment_methods:
            method_data[item['payment_method']] = {
                'count': item['count'],
                'total': float(item['total']),
            }
        
        # Payment status distribution
        payment_statuses = Order.objects.values('payment_status').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        status_data = {}
        for item in payment_statuses:
            status_data[item['payment_status']] = {
                'count': item['count'],
                'total': float(item['total'] or 0),
            }
        
        return Response({
            'success': True,
            'data': {
                'by_status': status_data,
            }
        })