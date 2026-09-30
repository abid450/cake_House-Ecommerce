# ============================================
# 4. TASKS APP (New app for common tasks)
# ============================================

# apps/tasks/__init__.py
# Empty file


# apps/tasks/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import connection
from products.models import Product
from django.db.models import F, Q
import subprocess
import os
import logging

logger = logging.getLogger(__name__)


# ============================================
# ✅ CLEANUP EXPIRED VERIFICATION TOKENS
# ============================================
@shared_task
def cleanup_expired_verification_tokens():
    """Delete expired email verification tokens"""
    from customers.models import EmailVerificationToken
    
    deleted_count = 0
    expired_tokens = EmailVerificationToken.objects.filter(
        is_used=False,
        expires_at__lt=timezone.now()
    )
    
    for token in expired_tokens:
        token.delete()
        deleted_count += 1
    
    logger.info(f"Cleaned up {deleted_count} expired verification tokens")
    return {
        'success': True,
        'deleted_count': deleted_count
    }


# ============================================
# ✅ DATABASE BACKUP
# ============================================
@shared_task
def backup_database():
    """Backup database using pg_dump"""
    db_name = settings.DATABASES['default']['NAME']
    db_user = settings.DATABASES['default']['USER']
    db_host = settings.DATABASES['default']['HOST']
    db_port = settings.DATABASES['default']['PORT']
    
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'backup_{db_name}_{timestamp}.sql')
    
    try:
        # PostgreSQL backup
        cmd = f'pg_dump -h {db_host} -p {db_port} -U {db_user} -F c -b -v -f "{backup_file}" {db_name}'
        subprocess.run(cmd, shell=True, check=True, env={**os.environ, 'PGPASSWORD': settings.DATABASES['default']['PASSWORD']})
        
        logger.info(f"Database backup created: {backup_file}")
        return {
            'success': True,
            'backup_file': backup_file,
            'timestamp': timestamp
        }
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================
# ✅ SEND TEST EMAIL
# ============================================
@shared_task
def send_test_email(recipient_email):
    """Send test email to verify email configuration"""
    try:
        send_mail(
            subject='Celery Test Email',
            message='This is a test email from Celery with RabbitMQ!',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Test email sent to {recipient_email}")
        return {
            'success': True,
            'recipient': recipient_email
        }
    except Exception as e:
        logger.error(f"Test email failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================
# ✅ SEND BULK EMAIL
# ============================================
@shared_task
def send_bulk_email(subject, message, recipient_list):
    """Send bulk email to multiple recipients"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f"Bulk email sent to {len(recipient_list)} recipients")
        return {
            'success': True,
            'recipient_count': len(recipient_list)
        }
    except Exception as e:
        logger.error(f"Bulk email failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================
# ✅ GENERATE SITEMAP
# ============================================
@shared_task
def generate_sitemap():
    """Generate sitemap for SEO"""
    from django.core.management import call_command
    
    try:
        sitemap_dir = os.path.join(settings.BASE_DIR, 'sitemaps')
        os.makedirs(sitemap_dir, exist_ok=True)
        
        # Call Django management command
        call_command('sitemap', output_dir=sitemap_dir)
        
        logger.info("Sitemap generated successfully")
        return {
            'success': True,
            'sitemap_dir': sitemap_dir
        }
    except Exception as e:
        logger.error(f"Sitemap generation failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================
# ✅ CLEANUP LOGS
# ============================================
@shared_task
def cleanup_logs():
    """Delete old log files"""
    import glob
    from datetime import datetime, timedelta
    
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    deleted_count = 0
    retention_days = 30
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    for log_file in glob.glob(os.path.join(log_dir, '*.log')):
        file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
        if file_mtime < cutoff_date:
            os.remove(log_file)
            deleted_count += 1
    
    logger.info(f"Cleaned up {deleted_count} old log files")
    return {
        'success': True,
        'deleted_count': deleted_count
    }




# ============================================
# 5. PRODUCTS TASKS
# ============================================

# apps/products/tasks.py

@shared_task(bind=True, max_retries=3)
def send_low_stock_alerts(self):
    """Send HTML email alerts for low stock products"""
    try:
        low_stock_products = Product.objects.filter(
            Q(quantity__lte=F('min_stock_level')) & Q(is_active=True)
        )
        
        if not low_stock_products.exists():
            return {
                'success': True,
                'message': 'No low stock products found'
            }
        
        # ✅ HTML Email Template
        product_rows = ""
        for product in low_stock_products:
            # Stock Status Badge
            if product.quantity <= 0:
                status_badge = '<span style="background:#dc2626;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">স্টক শেষ</span>'
            elif product.quantity <= product.min_stock_level:
                status_badge = '<span style="background:#f59e0b;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">সীমিত</span>'
            else:
                status_badge = '<span style="background:#10b981;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;">OK</span>'
            
            product_rows += f"""
            <tr style="border-bottom:1px solid #f0f0f0;">
                <td style="padding:12px 8px;font-weight:600;color:#1a0f14;">{product.name}</td>
                <td style="padding:12px 8px;font-family:monospace;font-size:12px;color:#666;">{product.sku}</td>
                <td style="padding:12px 8px;text-align:center;font-weight:700;color:#dc2626;">{product.quantity}</td>
                <td style="padding:12px 8px;text-align:center;color:#666;">{product.min_stock_level}</td>
                <td style="padding:12px 8px;text-align:center;">{status_badge}</td>
            </tr>
            """
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;background:#faf0e6;">
            <div style="max-width:680px;margin:0 auto;padding:20px;">
                <!-- Main Card -->
                <div style="background:#fffcf9;border-radius:20px;overflow:hidden;box-shadow:0 18px 40px -20px rgba(26,15,20,0.35);">
                    
                    <!-- Header -->
                    <div style="background:linear-gradient(135deg,#a0324a 0%,#7a2436 100%);padding:30px 32px;text-align:center;">
                        <h1 style="color:#fff;margin:0;font-size:26px;font-weight:700;">🔔 Low Stock Alert</h1>
                        <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:14px;">Cake House Inventory System</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding:32px;">
                        <!-- Alert Summary -->
                        <div style="background:#fef2f2;border-left:4px solid #dc2626;padding:16px 20px;border-radius:8px;margin-bottom:24px;">
                            <p style="margin:0;color:#991b1b;font-weight:600;font-size:15px;">
                                ⚠️ {low_stock_products.count()}টি পণ্যের স্টক কমে গেছে!
                            </p>
                            <p style="margin:6px 0 0;color:#b91c1c;font-size:13px;">
                                অনুগ্রহ করে দ্রুত স্টক পুনরায় পূরণ করুন।
                            </p>
                        </div>
                        
                        <!-- Product Table -->
                        <table style="width:100%;border-collapse:collapse;font-size:14px;">
                            <thead>
                                <tr style="background:#1a0f14;color:#faf0e6;">
                                    <th style="padding:12px 8px;text-align:left;border-radius:8px 0 0 0;">পণ্যের নাম</th>
                                    <th style="padding:12px 8px;text-align:left;">SKU</th>
                                    <th style="padding:12px 8px;text-align:center;">স্টক</th>
                                    <th style="padding:12px 8px;text-align:center;">সর্বনিম্ন</th>
                                    <th style="padding:12px 8px;text-align:center;border-radius:0 8px 0 0;">অবস্থা</th>
                                </tr>
                            </thead>
                            <tbody>
                                {product_rows}
                            </tbody>
                        </table>
                        
                        <!-- Action Button -->
                        <div style="text-align:center;margin-top:30px;">
                            <a href="{settings.FRONTEND_URL}/admin/products/" 
                               style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#d4a857 0%,#b8913a 100%);color:#1a0f14;text-decoration:none;border-radius:999px;font-weight:700;font-size:15px;">
                                📦 স্টক ম্যানেজ করুন
                            </a>
                        </div>
                        
                        <!-- Footer Note -->
                        <p style="text-align:center;color:#999;font-size:12px;margin-top:24px;">
                            এই ইমেইলটি স্বয়ংক্রিয়ভাবে পাঠানো হয়েছে Cake House ইনভেন্টরি সিস্টেম থেকে।
                        </p>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background:#1a0f14;padding:20px;text-align:center;">
                        <p style="color:rgba(250,240,230,0.5);font-size:12px;margin:0;">
                            © 2026 Cake House. All rights reserved.
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # ✅ Send HTML Email
        send_mail(
            subject=f'🔔 Low Stock Alert - {low_stock_products.count()} Products Need Restocking',
            message=f"Low stock alert for {low_stock_products.count()} products.",  # Plain text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=settings.ADMIN_EMAILS,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Low stock alert sent for {low_stock_products.count()} products")
        return {
            'success': True,
            'product_count': low_stock_products.count()
        }
        
    except Exception as e:
        logger.error(f"Low stock alert failed: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)
        raise

@shared_task
def send_product_update_notification(product_id):
    """Send notification when product is updated"""
    from .models import Product
    
    try:
        product = Product.objects.get(id=product_id)
        send_mail(
            subject=f'Product Updated: {product.name}',
            message=f"""
            Product: {product.name}
            SKU: {product.sku}
            Price: ৳{product.selling_price}
            Stock: {product.quantity}
            
            View product: {settings.FRONTEND_URL}/product-details/?id={product.id}
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            fail_silently=False,
        )
        return {'success': True, 'product_id': str(product_id)}
    except Exception as e:
        logger.error(f"Product update notification failed: {str(e)}")
        return {'success': False, 'error': str(e)}




# ============================================
# 6. CUSTOMERS TASKS (Email Verification)
# ============================================

# apps/customers/tasks.py
from customers.models import User, EmailVerificationToken


@shared_task(bind=True, max_retries=3)
def send_verification_email(self, user_id, token_id):
    """Send email verification email asynchronously"""
    try:
        user = User.objects.get(id=user_id)
        token = EmailVerificationToken.objects.get(id=token_id)
        
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
        
        subject = "Verify Your Email - Cake House"
        
        # HTML Email Template
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #f0f0f0;">
                    <h1 style="color: #333; font-size: 28px;">🎂 Cake House</h1>
                    <p style="color: #666; font-size: 16px;">Premium Bakery & Dessert Shop</p>
                </div>
                <div style="padding: 20px 0;">
                    <h2 style="color: #333; font-size: 22px;">Hello {user.first_name or user.username}!</h2>
                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        Thank you for registering at <strong>Cake House</strong>.
                        Please click the button below to verify your email address:
                    </p>
                    <div style="text-align: center; padding: 20px 0;">
                        <a href="{verification_link}" 
                           style="display: inline-block; padding: 14px 40px; background: linear-gradient(135deg, #8E2E3B 0%, #6E1F2A 100%); 
                                  color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                            ✅ Verify Email Address
                        </a>
                    </div>
                    <p style="color: #888; font-size: 14px; text-align: center;">
                        This link will expire in <strong>24 hours</strong>.
                    </p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        If you didn't create an account with us, please ignore this email.
                    </p>
                </div>
                <div style="text-align: center; padding-top: 20px; border-top: 2px solid #f0f0f0; color: #999; font-size: 12px;">
                    <p>© 2024 Cake House. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_mail(
            subject=subject,
            message="Please verify your email address.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return {
            'success': True,
            'user_id': str(user.id),
            'email': user.email
        }
        
    except Exception as e:
        logger.error(f"Verification email failed: {str(e)}")
        self.retry(exc=e, countdown=60 * 5)
        raise


@shared_task
def send_welcome_email(user_id):
    """Send welcome email after successful verification"""
    try:
        user = User.objects.get(id=user_id)
        
        subject = "Welcome to Cake House! 🎂"
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #f0f0f0;">
                    <h1 style="color: #333; font-size: 28px;">🎂 Cake House</h1>
                </div>
                <div style="padding: 20px 0;">
                    <h2 style="color: #333; font-size: 22px;">Welcome, {user.first_name or user.username}! 🎉</h2>
                    <p style="color: #555; font-size: 16px; line-height: 1.6;">
                        Your email has been verified successfully. You're now part of the Cake House family!
                    </p>
                    <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <h3 style="color: #333; margin-top: 0;">What you can do now:</h3>
                        <ul style="color: #555; font-size: 15px; line-height: 1.8; padding-left: 20px;">
                            <li>🍰 Browse our delicious cakes and desserts</li>
                            <li>🛒 Place orders online</li>
                            <li>🎁 Get exclusive offers and discounts</li>
                            <li>📦 Track your orders</li>
                        </ul>
                    </div>
                    <div style="text-align: center; padding: 20px 0;">
                        <a href="{settings.FRONTEND_URL}/products" 
                           style="display: inline-block; padding: 14px 40px; background: linear-gradient(135deg, #8E2E3B 0%, #6E1F2A 100%); 
                                  color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                            🛍️ Start Shopping
                        </a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        send_mail(
            subject=subject,
            message="Welcome to Cake House!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return {
            'success': True,
            'user_id': str(user.id),
            'email': user.email
        }
        
    except Exception as e:
        logger.error(f"Welcome email failed: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def send_weekly_newsletter():
    """Send weekly newsletter to all subscribed customers"""
    users = User.objects.filter(email_notifications=True, is_email_verified=True)
    
    if not users.exists():
        return {'success': True, 'message': 'No users to send newsletter'}
    
    subject = "Weekly Newsletter - Cake House 🎂"
    message = """
    Weekly Newsletter
    
    Dear Valued Customer,
    
    Welcome to this week's newsletter from Cake House!
    
    Featured Products:
    • New arrivals this week
    • Special discounts
    • Exclusive offers
    
    Visit our website to see the full collection:
    {settings.FRONTEND_URL}/products
    
    Best regards,
    Cake House Team
    """
    
    email_list = [user.email for user in users]
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=email_list,
            fail_silently=False,
        )
        logger.info(f"Weekly newsletter sent to {len(email_list)} subscribers")
        return {
            'success': True,
            'subscriber_count': len(email_list)
        }
    except Exception as e:
        logger.error(f"Weekly newsletter failed: {str(e)}")
        return {'success': False, 'error': str(e)}



# ============================================
# 8. CART TASKS
# ============================================
from cart.models import Cart


@shared_task
def cleanup_expired_carts():
    """Delete expired carts (older than 30 days)"""
    cutoff_date = timezone.now() - timezone.timedelta(days=30)
    
    expired_carts = Cart.objects.filter(
        updated_at__lt=cutoff_date,
        user__isnull=True
    )
    
    deleted_count = expired_carts.count()
    expired_carts.delete()
    
    logger.info(f"Cleaned up {deleted_count} expired carts")
    return {
        'success': True,
        'deleted_count': deleted_count
    }


@shared_task
def send_abandoned_cart_reminder():
    """Send reminder emails for abandoned carts"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    cutoff_date = timezone.now() - timezone.timedelta(hours=24)
    
    carts = Cart.objects.filter(
        updated_at__lt=cutoff_date,
        updated_at__gt=timezone.now() - timezone.timedelta(days=3),
        user__isnull=False
    )
    
    reminder_count = 0
    
    for cart in carts:
        if cart.items.exists():
            user = cart.user
            if user.email and user.email_notifications:
                # Send reminder email
                send_mail(
                    subject='Don\'t forget your items at Cake House! 🎂',
                    message=f"""
                    Hello {user.full_name},
                    
                    You have items waiting in your cart at Cake House!
                    
                    Visit your cart to complete your order:
                    {settings.FRONTEND_URL}/cart
                    
                    Best regards,
                    Cake House Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                reminder_count += 1
    
    logger.info(f"Sent {reminder_count} abandoned cart reminders")
    return {
        'success': True,
        'reminder_count': reminder_count
    }



