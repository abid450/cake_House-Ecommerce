# payment/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import redirect
from django.conf import settings
import logging

from .models import Payment
from .serializers import PaymentSerializer, PaymentInitiateSerializer
from .sslcommerz import sslcommerz
from orders.models import Order

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Payment ViewSet"""
    
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]
    
    # ✅ Permission Override (সব Action-এর জন্য)
    def get_permissions(self):
        """Set permissions based on action"""
        # ✅ AllowAny for all payment actions
        if self.action in ['initiate', 'success', 'fail', 'cancel', 'ipn']:
            self.permission_classes = [AllowAny]
        elif self.action in ['refund']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [AllowAny]
        return super().get_permissions()
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return Payment.objects.all()
        if user.is_authenticated:
            return Payment.objects.filter(order__user=user)
        return Payment.objects.none()
    
    # ============================================
    # Initiate Payment
    # ============================================
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def initiate(self, request):
        """Initiate SSLCommerz payment"""
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order = serializer.order
        
        # Create Payment record
        payment = Payment.objects.create(
            transaction_id=str(order.id),
            order=order,
            gateway='sslcommerz',
            amount=order.total_amount,
            status='pending',
        )
        
        # Initiate SSLCommerz
        result = sslcommerz.initiate_payment(order, request)
        
        if result['success']:
            payment.session_key = result.get('session_key', '')
            payment.gateway_page_url = result.get('gateway_url', '')
            payment.save()
            
            return Response({
                'success': True,
                'message': 'পেমেন্ট সেশন তৈরি হয়েছে।',
                'data': {
                    'payment_id': str(payment.id),
                    'transaction_id': payment.transaction_id,
                    'gateway_url': result['gateway_url'],
                    'session_key': result.get('session_key', ''),
                }
            })
        else:
            payment.status = 'failed'
            payment.raw_response = result
            payment.save()
            
            return Response({
                'success': False,
                'message': result.get('error', 'পেমেন্ট শুরু করা যায়নি।'),
                'data': {'payment_id': str(payment.id)}
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # ============================================
    # Payment Success Callback
    # ============================================
    @action(detail=False, methods=['post', 'get'], permission_classes=[AllowAny])
    def success(self, request):
        """SSLCommerz success callback"""
        data = request.data if request.method == 'POST' else request.query_params
        
        tran_id = data.get('tran_id')
        val_id = data.get('val_id')
        
        logger.info(f"🔔 Payment success callback: tran_id={tran_id}, val_id={val_id}")
        
        try:
            order = Order.objects.get(id=tran_id)
            payment = Payment.objects.filter(order=order).first()
            
            if not payment:
                payment = Payment.objects.create(
                    transaction_id=tran_id,
                    order=order,
                    gateway='sslcommerz',
                    amount=order.total_amount,
                )
            
            # Validate payment
            validation = sslcommerz.validate_payment(val_id)
            
            if validation.get('status') in ['VALID', 'VALIDATED']:
                payment.mark_success(validation)
                
                # ✅ Cart Clear করুন
                if order.user:
                    from cart.models import Cart
                    try:
                        cart = Cart.objects.get(user=order.user)
                        cart.items.all().delete()
                        cart.save()
                        logger.info(f"✅ Cart cleared for {order.user.username}")
                    except Cart.DoesNotExist:
                        pass
                
                # Send confirmation email
                from orders.tasks import send_order_confirmation_email
                send_order_confirmation_email.delay(str(order.id))
                
                logger.info(f"✅ Payment SUCCESS: {order.order_number}")
                
                # ✅ Redirect to Frontend Success Page
                return redirect(f"{settings.FRONTEND_URL}/checkout/success/?order={order.order_number}")
            else:
                payment.mark_failed(validation)
                logger.warning(f"❌ Payment FAILED: {order.order_number}")
                return redirect(f"{settings.FRONTEND_URL}/checkout/failed/?order={order.order_number}")
                
        except Order.DoesNotExist:
            logger.error(f"❌ Order not found: {tran_id}")
            return redirect(f"{settings.FRONTEND_URL}/checkout/failed/")
        except Exception as e:
            logger.error(f"❌ Payment success callback error: {str(e)}")
            return redirect(f"{settings.FRONTEND_URL}/checkout/failed/")
    
    # ============================================
    # Payment Fail Callback
    # ============================================
    @action(detail=False, methods=['post', 'get'], permission_classes=[AllowAny])
    def fail(self, request):
        """SSLCommerz fail callback"""
        data = request.data if request.method == 'POST' else request.query_params
        tran_id = data.get('tran_id')
        
        logger.info(f"❌ Payment fail callback: {tran_id}")
        
        try:
            order = Order.objects.get(id=tran_id)
            payment = Payment.objects.filter(order=order).first()
            
            if payment:
                payment.mark_failed(data)
            
            return redirect(f"{settings.FRONTEND_URL}/checkout/failed/?order={order.order_number}")
            
        except Order.DoesNotExist:
            return redirect(f"{settings.FRONTEND_URL}/checkout/failed/")
    
    # ============================================
    # Payment Cancel Callback
    # ============================================
    @action(detail=False, methods=['post', 'get'], permission_classes=[AllowAny])
    def cancel(self, request):
        """SSLCommerz cancel callback"""
        data = request.data if request.method == 'POST' else request.query_params
        tran_id = data.get('tran_id')
        
        logger.info(f"⏸️ Payment cancel callback: {tran_id}")
        
        try:
            order = Order.objects.get(id=tran_id)
            payment = Payment.objects.filter(order=order).first()
            
            if payment:
                payment.mark_cancelled()
            
            return redirect(f"{settings.FRONTEND_URL}/checkout/cancelled/?order={order.order_number}")
            
        except Order.DoesNotExist:
            return redirect(f"{settings.FRONTEND_URL}/checkout/cancelled/")
    
    # ============================================
    # IPN Callback
    # ============================================
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def ipn(self, request):
        """SSLCommerz IPN (Instant Payment Notification)"""
        data = request.data
        
        logger.info(f"🔔 IPN received: {data}")
        
        tran_id = data.get('tran_id')
        val_id = data.get('val_id')
        ipn_status = data.get('status')
        
        try:
            order = Order.objects.get(id=tran_id)
            payment = Payment.objects.filter(order=order).first()
            
            if payment:
                payment.ipn_response = data
                
                if ipn_status in ['VALID', 'VALIDATED']:
                    validation = sslcommerz.validate_payment(val_id)
                    if validation.get('status') in ['VALID', 'VALIDATED']:
                        payment.mark_success(validation)
                        
                        # ✅ Cart Clear করুন
                        if order.user:
                            from cart.models import Cart
                            try:
                                cart = Cart.objects.get(user=order.user)
                                cart.items.all().delete()
                                cart.save()
                            except Cart.DoesNotExist:
                                pass
                        
                        # Send confirmation email
                        from orders.tasks import send_order_confirmation_email
                        send_order_confirmation_email.delay(str(order.id))
                        
                        logger.info(f"✅ IPN Payment SUCCESS: {order.order_number}")
                        
                elif ipn_status == 'FAILED':
                    payment.mark_failed(data)
                    logger.warning(f"❌ IPN Payment FAILED: {order.order_number}")
                elif ipn_status == 'CANCELLED':
                    payment.mark_cancelled()
                    logger.warning(f"⏸️ IPN Payment CANCELLED: {order.order_number}")
                
                payment.save()
            
            return Response({'status': 'OK'})
            
        except Order.DoesNotExist:
            logger.error(f"❌ IPN Order not found: {tran_id}")
            return Response({'status': 'ERROR', 'message': 'Order not found'}, status=404)
        except Exception as e:
            logger.error(f"❌ IPN error: {str(e)}")
            return Response({'status': 'ERROR', 'message': str(e)}, status=500)
    
    # ============================================
    # Payment Status Check
    # ============================================
    @action(detail=True, methods=['get'])
    def status_check(self, request, pk=None):
        """Check payment status"""
        payment = self.get_object()
        return Response({
            'success': True,
            'data': {
                'transaction_id': payment.transaction_id,
                'status': payment.status,
                'amount': str(payment.amount),
                'paid_at': payment.paid_at,
                'order_number': payment.order.order_number,
            }
        })
    
    # ============================================
    # Refund (Admin)
    # ============================================
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def refund(self, request, pk=None):
        """Initiate refund (Admin only)"""
        if not request.user.is_staff:
            return Response({
                'success': False,
                'message': 'শুধুমাত্র এডমিন রিফান্ড করতে পারবেন।'
            }, status=status.HTTP_403_FORBIDDEN)
        
        payment = self.get_object()
        
        if payment.status != 'success':
            return Response({
                'success': False,
                'message': 'শুধুমাত্র সফল পেমেন্ট রিফান্ড করা যাবে।'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refund_amount = request.data.get('amount', payment.amount)
        refund_remarks = request.data.get('remarks', 'Customer request')
        
        result = sslcommerz.initiate_refund(
            payment.bank_transaction_id,
            refund_amount,
            refund_remarks
        )
        
        if result.get('status') == 'SUCCESS':
            payment.mark_refunded(refund_amount)
            return Response({
                'success': True,
                'message': 'রিফান্ড সফল হয়েছে।',
                'data': result
            })
        else:
            return Response({
                'success': False,
                'message': 'রিফান্ড ব্যর্থ হয়েছে।',
                'data': result
            }, status=status.HTTP_400_BAD_REQUEST)