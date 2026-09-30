# payment/serializers.py

from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Payment Serializer"""
    
    order_number = serializers.CharField(source='orders.order_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'transaction_id', 'order', 'order_number',
            'gateway', 'amount', 'currency',
            'session_key', 'gateway_page_url', 'validation_id',
            'bank_transaction_id', 'card_type', 'card_no', 'store_amount',
            'status', 'risk_level', 'risk_title',
            'created_at', 'updated_at', 'paid_at', 'failed_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'session_key', 'gateway_page_url',
            'validation_id', 'bank_transaction_id', 'card_type', 'card_no',
            'store_amount', 'status', 'risk_level', 'risk_title',
            'created_at', 'updated_at', 'paid_at', 'failed_at'
        ]


class PaymentInitiateSerializer(serializers.Serializer):
    """Payment Initiate Serializer"""
    
    order_id = serializers.UUIDField(required=True)
    
    def validate_order_id(self, value):
        from orders.models import Order
        try:
            order = Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("অর্ডার পাওয়া যায়নি।")
        
        if order.payment_status == 'paid':
            raise serializers.ValidationError("এই অর্ডারটি ইতিমধ্যে পরিশোধিত।")
        
        if order.status == 'cancelled':
            raise serializers.ValidationError("বাতিল করা অর্ডারের জন্য পেমেন্ট করা যাবে না।")
        
        self.order = order
        return value