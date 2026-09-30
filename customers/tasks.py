# Task/tasks.py — ADD THIS TASK
# (alongside your other email tasks; needs no new imports beyond
# what's already at the top of this file, since User is imported there)


from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from customers.models import User
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_login_alert_email(self, user_id, login_meta):
    """
    Sends a security notification email right after a successful login —
    device, browser, approximate location, IP, and time — same idea as
    LinkedIn/Google's "new sign-in" alerts.

    login_meta is a plain dict (not a model instance) so this task stays
    fully serializable for Celery: {
        'ip_address': str, 'device': str, 'os': str, 'browser': str,
        'city': str, 'country': str, 'login_at': str (ISO datetime),
    }
    """
    try:
        user = User.objects.get(id=user_id)

        location = ', '.join(filter(None, [login_meta.get('city'), login_meta.get('country')])) or 'অজানা লোকেশন'

        subject = "নতুন লগইন সনাক্ত হয়েছে — Cake House"

        html_message = f"""
        <html>
        <body style="margin:0;padding:0;font-family:'Segoe UI',Arial,sans-serif;background:#faf1e2;">
            <div style="max-width:600px;margin:0 auto;padding:20px;">
                <div style="background:#fffdf9;border-radius:20px;overflow:hidden;box-shadow:0 18px 40px -20px rgba(42,22,32,0.35);">

                    <div style="background:linear-gradient(135deg,#8E2E3B 0%,#6E1F2A 100%);padding:30px 32px;text-align:center;">
                        <h1 style="color:#fff;margin:0;font-size:24px;">🔐 নতুন লগইন সনাক্ত হয়েছে</h1>
                        <p style="color:rgba(255,255,255,0.85);margin:8px 0 0;font-size:13.5px;">Cake House অ্যাকাউন্ট সুরক্ষা</p>
                    </div>

                    <div style="padding:32px;">
                        <p style="color:#2A1620;font-size:15px;line-height:1.6;">
                            হ্যালো {user.first_name or user.username},<br>
                            আপনার অ্যাকাউন্টে এইমাত্র একটি সফল লগইন হয়েছে। বিস্তারিত নিচে দেওয়া হলো:
                        </p>

                        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-top:20px;">
                            <tr style="border-bottom:1px solid #f0e4d0;">
                                <td style="padding:10px 4px;color:#8E2E3B;font-weight:600;width:40%;">🕒 সময়</td>
                                <td style="padding:10px 4px;color:#2A1620;">{login_meta.get('login_at', '—')}</td>
                            </tr>
                            <tr style="border-bottom:1px solid #f0e4d0;">
                                <td style="padding:10px 4px;color:#8E2E3B;font-weight:600;">📍 লোকেশন</td>
                                <td style="padding:10px 4px;color:#2A1620;">{location}</td>
                            </tr>
                            <tr style="border-bottom:1px solid #f0e4d0;">
                                <td style="padding:10px 4px;color:#8E2E3B;font-weight:600;">🌐 IP ঠিকানা</td>
                                <td style="padding:10px 4px;color:#2A1620;font-family:monospace;">{login_meta.get('ip_address', '—')}</td>
                            </tr>
                            <tr style="border-bottom:1px solid #f0e4d0;">
                                <td style="padding:10px 4px;color:#8E2E3B;font-weight:600;">💻 ডিভাইস</td>
                                <td style="padding:10px 4px;color:#2A1620;">{login_meta.get('device', '—')}</td>
                            </tr>
                            <tr style="border-bottom:1px solid #f0e4d0;">
                                <td style="padding:10px 4px;color:#8E2E3B;font-weight:600;">🖥️ অপারেটিং সিস্টেম</td>
                                <td style="padding:10px 4px;color:#2A1620;">{login_meta.get('os', '—')}</td>
                            </tr>
                            <tr>
                                <td style="padding:10px 4px;color:#8E2E3B;font-weight:600;">🧭 ব্রাউজার</td>
                                <td style="padding:10px 4px;color:#2A1620;">{login_meta.get('browser', '—')}</td>
                            </tr>
                        </table>

                        <div style="background:#fef2f2;border-left:4px solid #dc2626;padding:16px 20px;border-radius:8px;margin-top:26px;">
                            <p style="margin:0;color:#991b1b;font-weight:600;font-size:14px;">
                                এই লগইনটি যদি আপনি না করে থাকেন...
                            </p>
                            <p style="margin:6px 0 0;color:#b91c1c;font-size:13px;">
                                তাহলে এখনই আপনার পাসওয়ার্ড পরিবর্তন করুন এবং আমাদের সাথে যোগাযোগ করুন।
                            </p>
                        </div>

                        <div style="text-align:center;margin-top:26px;">
                            <a href="{settings.FRONTEND_URL}/profile/"
                               style="display:inline-block;padding:13px 34px;background:linear-gradient(135deg,#C79A4B 0%,#A9812F 100%);color:#2A1620;text-decoration:none;border-radius:999px;font-weight:700;font-size:14.5px;">
                                🔑 পাসওয়ার্ড পরিবর্তন করুন
                            </a>
                        </div>
                    </div>

                    <div style="background:#2A1620;padding:18px;text-align:center;">
                        <p style="color:rgba(248,238,223,0.5);font-size:11.5px;margin:0;">
                            এই ইমেইলটি স্বয়ংক্রিয়ভাবে পাঠানো হয়েছে Cake House থেকে।
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        send_mail(
            subject=subject,
            message=(
                f"নতুন লগইন সনাক্ত হয়েছে।\n"
                f"সময়: {login_meta.get('login_at', '—')}\n"
                f"লোকেশন: {location}\n"
                f"IP: {login_meta.get('ip_address', '—')}\n"
                f"ডিভাইস: {login_meta.get('device', '—')} ({login_meta.get('os', '—')}, {login_meta.get('browser', '—')})\n"
                f"আপনি না হলে অবিলম্বে পাসওয়ার্ড পরিবর্তন করুন।"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Login alert email sent to {user.email}")
        return {'success': True, 'user_id': str(user.id)}

    except Exception as e:
        logger.error(f"Login alert email failed: {str(e)}")
        self.retry(exc=e, countdown=30)
        raise