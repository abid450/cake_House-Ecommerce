# order/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id):
    """Send order confirmation email"""
    try:
        from .models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'✅ Order Confirmed - {order.order_number}'
        
        # Build items HTML
        items_html = ""
        for item in order.items.all():
            items_html += f"""
            <tr>
                <td style="padding:10px;">{item.product_name}</td>
                <td style="padding:10px;text-align:center;">{item.quantity}</td>
                <td style="padding:10px;text-align:right;">৳{item.total_price}</td>
            </tr>
            """
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family:Arial,sans-serif;background:#faf0e6;padding:20px;">
            <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;">
                <div style="background:linear-gradient(135deg,#a0324a,#7a2436);padding:30px;text-align:center;">
                    <h1 style="color:#fff;margin:0;">🎂 Cake House</h1>
                    <p style="color:rgba(255,255,255,0.8);margin:8px 0 0;">Order Confirmed!</p>
                </div>
                <div style="padding:30px;">
                    <h2 style="color:#333;">ধন্যবাদ, {order.shipping_name}!</h2>
                    <p style="color:#666;">আপনার অর্ডার সফলভাবে গ্রহণ করা হয়েছে।</p>
                    
                    <div style="background:#f8fafc;padding:16px;border-radius:8px;margin:20px 0;">
                        <p style="margin:0;color:#333;"><strong>Order Number:</strong> {order.order_number}</p>
                        <p style="margin:8px 0 0;color:#333;"><strong>Status:</strong> {order.get_status_display()}</p>
                        <p style="margin:8px 0 0;color:#333;"><strong>Total:</strong> ৳{order.total_amount}</p>
                    </div>
                    
                    <table style="width:100%;border-collapse:collapse;">
                        <thead>
                            <tr style="background:#1a0f14;color:#faf0e6;">
                                <th style="padding:10px;text-align:left;">Product</th>
                                <th style="padding:10px;text-align:center;">Qty</th>
                                <th style="padding:10px;text-align:right;">Price</th>
                            </tr>
                        </thead>
                        <tbody>{items_html}</tbody>
                    </table>
                    
                    <div style="text-align:center;margin-top:30px;">
                        <a href="{settings.FRONTEND_URL}/orders/{order.id}/" 
                           style="display:inline-block;padding:14px 36px;background:#d4a857;color:#1a0f14;text-decoration:none;border-radius:999px;font-weight:700;">
                            📦 View Order
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        recipient = order.shipping_email or (order.user.email if order.user else None)
        if recipient:
            send_mail(
                subject=subject,
                message=f"Order {order.order_number} confirmed.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Order confirmation email sent to {recipient}")
        
        return {'success': True, 'order_id': str(order.id)}
        
    except Exception as e:
        logger.error(f"Order confirmation email failed: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)


@shared_task
def send_order_status_update_email(order_id, old_status, new_status):
    """Send order status update email"""
    try:
        from .models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'📦 Order Status Updated - {order.order_number}'
        
        status_messages = {
            'confirmed': 'আপনার অর্ডার নিশ্চিত করা হয়েছে।',
            'processing': 'আপনার অর্ডার প্রস্তুত করা হচ্ছে।',
            'shipped': 'আপনার অর্ডার পাঠানো হয়েছে।',
            'delivered': 'আপনার অর্ডার সফলভাবে ডেলিভারি হয়েছে।',
            'cancelled': 'আপনার অর্ডার বাতিল করা হয়েছে।',
        }
        
        message = status_messages.get(new_status, f'Order status changed to {new_status}')
        
        recipient = order.shipping_email or (order.user.email if order.user else None)
        if recipient:
            send_mail(
                subject=subject,
                message=f"{message}\n\nOrder: {order.order_number}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        
        return {'success': True, 'order_id': str(order_id)}
        
    except Exception as e:
        logger.error(f"Status update email failed: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def process_order_payment(order_id, transaction_id):
    """Process order payment"""
    try:
        from .models import Order
        order = Order.objects.get(id=order_id)
        order.mark_as_paid(transaction_id)
        
        # Send confirmation
        send_order_confirmation_email.delay(order_id)
        
        return {'success': True, 'order_id': str(order_id)}
        
    except Exception as e:
        logger.error(f"Payment processing failed: {str(e)}")
        return {'success': False, 'error': str(e)}