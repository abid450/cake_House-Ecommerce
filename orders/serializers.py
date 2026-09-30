# order/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from products.models import Product
from decimal import Decimal
from customers.models import User
import re
from orders.models import Order

def validate_bd_phone(value):
    """Validate Bangladesh phone number"""
    if not value:
        return value
    
    phone = re.sub(r'[\s\-\(\)]', '', str(value))
    pattern = r'^(?:(?:\+?88)?01[3-9]\d{8})$'
    
    if not re.match(pattern, phone):
        raise serializers.ValidationError(
            "সঠিক মোবাইল নম্বর দিন। (যেমন: 01712345678)"
        )
    return phone



class OrderItemSerializer(serializers.ModelSerializer):
    """Order Item Serializer"""
    
    product_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_detail', 'product_name', 'product_sku',
            'product_image', 'unit_price', 'quantity', 'total_price',
            'customization', 'special_instructions', 'created_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at']
    
    def get_product_detail(self, obj):
        if obj.product:
            return {
                'id': str(obj.product.id),
                'name': obj.product.name,
                'slug': obj.product.slug,
                'main_image': obj.product.main_image.url if obj.product.main_image else None,
                'price': str(obj.product.price),
                'final_price': str(obj.product.final_price),
            }
        return None


class OrderListSerializer(serializers.ModelSerializer):
    """Order List Serializer (Summary)"""
    
    total_items = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'payment_status',
            'total_amount', 'total_items', 'created_at', 'delivery_date'
        ]
        read_only_fields = ['id', 'order_number', 'created_at']


class OrderDetailSerializer(serializers.ModelSerializer):
    """Order Detail Serializer"""
    
    items = OrderItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    status_history = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user',
            'shipping_name', 'shipping_phone', 'shipping_email',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_postal_code', 'shipping_country',
            'billing_same_as_shipping', 'billing_name', 'billing_phone',
            'billing_address', 'billing_city', 'billing_postal_code',
            'subtotal', 'delivery_charge', 'discount_amount',
            'tax_amount', 'total_amount',
            'payment_method', 'payment_status', 'payment_transaction_id',
            'status', 'customer_note', 'admin_note',
            'delivery_date', 'delivery_time', 'delivered_at',
            'tracking_number', 'tracking_url',
            'items', 'total_items', 'status_history',
            'created_at', 'updated_at', 'confirmed_at', 'cancelled_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'user', 'subtotal', 'total_amount',
            'payment_status', 'payment_transaction_id', 'status',
            'created_at', 'updated_at', 'confirmed_at', 'cancelled_at'
        ]
    
    def get_status_history(self, obj):
        return [
            {
                'status': h.status,
                'note': h.note,
                'created_at': h.created_at,
            }
            for h in obj.status_history.all()[:10]
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Order Create Serializer"""
    
    # ✅ Explicitly define required fields
    shipping_name = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=200,
        error_messages={
            'required': 'নাম প্রয়োজন।',
            'blank': 'নাম খালি রাখা যাবে না।',
            'max_length': 'নাম ২০০ অক্ষরের বেশি হতে পারবে না।',
        }
    )
    shipping_phone = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=20,
        error_messages={
            'required': 'মোবাইল নম্বর প্রয়োজন।',
            'blank': 'মোবাইল নম্বর খালি রাখা যাবে না।',
        }
    )
    shipping_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        default='',
        error_messages={
            'invalid': 'সঠিক ইমেইল ঠিকানা দিন।',
        }
    )
    shipping_address = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'ঠিকানা প্রয়োজন।',
            'blank': 'ঠিকানা খালি রাখা যাবে না।',
        }
    )
    shipping_city = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=100,
        error_messages={
            'required': 'শহর প্রয়োজন।',
            'blank': 'শহর খালি রাখা যাবে না।',
        }
    )
    shipping_state = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )
    shipping_postal_code = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )
    shipping_country = serializers.CharField(
        required=False,
        allow_blank=True,
        default='Bangladesh'
    )
    customer_note = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )
    
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=True,
        error_messages={
            'required': 'অন্তত একটি পণ্য প্রয়োজন।',
            'empty': 'অন্তত একটি পণ্য প্রয়োজন।',
        }
    )
    
    class Meta:
        model = Order
        fields = [
            'shipping_name', 'shipping_phone', 'shipping_email',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_postal_code', 'shipping_country',
            'payment_method', 'customer_note',
            'delivery_date', 'delivery_time',
            'items'
        ]
    
    def validate_shipping_name(self, value):
        """Validate shipping name"""
        if not value or not value.strip():
            raise serializers.ValidationError("নাম প্রয়োজন।")
        if len(value.strip()) < 4:
            raise serializers.ValidationError("নাম কমপক্ষে ৩ অক্ষর হতে হবে।")
        return value.strip()

    
    def validate_shipping_phone(self, value):
            """Validate phone number"""
            if value:
                return validate_bd_phone(value)
            return value
    
    def validate_shipping_address(self, value):
        """Validate shipping address"""
        if not value or not value.strip():
            raise serializers.ValidationError("ঠিকানা প্রয়োজন।")
        return value.strip()

    def validate_shipping_email(self, value):
           if Order.objects.filter(shipping_email__iexact=value).exists():
               raise serializers.ValidationError(
                   ("এই ইমেইল দিয়ে ইতিমধ্যে একটি অ্যাকাউন্ট আছে।")
               )
           return value
    
    def validate_shipping_city(self, value):
        """Validate shipping city"""
        if not value or not value.strip():
            raise serializers.ValidationError("শহর প্রয়োজন।")
        return value.strip()
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("অন্তত একটি পণ্য প্রয়োজন।")
        
        for item in value:
            if 'product_id' not in item:
                raise serializers.ValidationError("প্রতিটি আইটেমে product_id থাকতে হবে।")
            if 'quantity' not in item or int(item['quantity']) < 1:
                raise serializers.ValidationError("পরিমাণ কমপক্ষে ১ হতে হবে।")
            
            try:
                product = Product.objects.get(id=item['product_id'])
                if product.is_out_of_stock:
                    raise serializers.ValidationError(f"{product.name} স্টকে নেই।")
                if product.quantity < int(item['quantity']):
                    raise serializers.ValidationError(
                        f"{product.name}-এর পর্যাপ্ত স্টক নেই। "
                        f"বর্তমান স্টক: {product.quantity}"
                    )
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"পণ্য পাওয়া যায়নি: {item['product_id']}")
        
        return value
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user if self.context['request'].user.is_authenticated else None
        
        # ✅ Decimal দিয়ে শুরু
        subtotal = Decimal('0.00')
        
        # Create order
        order = Order.objects.create(
            user=user,
            **validated_data
        )
        
        # Create order items
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'])
            quantity = int(item_data['quantity'])
            
            # ✅ Decimal দিয়ে unit_price
            unit_price = Decimal(str(product.final_price))
            total_price = unit_price * quantity
            
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                product_image=product.main_image.url if product.main_image else '',
                unit_price=unit_price,
                quantity=quantity,
                total_price=total_price,
                customization=item_data.get('customization', {}),
                special_instructions=item_data.get('special_instructions', '')
            )
            
            subtotal += total_price
            
            # Reduce stock
            product.reduce_stock(quantity)
        
        # Calculate totals
        order.subtotal = subtotal
        order.delivery_charge = Decimal('100.00')
        order.total_amount = subtotal + order.delivery_charge
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            note='Order created'
        )
        
        # ✅ COD হলে Email পাঠান
        if order.payment_method == 'cod':
            from .tasks import send_order_confirmation_email
            send_order_confirmation_email.delay(str(order.id))
        
        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Order Status Update Serializer"""
    
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True)
    tracking_number = serializers.CharField(required=False, allow_blank=True)
    tracking_url = serializers.URLField(required=False, allow_blank=True)