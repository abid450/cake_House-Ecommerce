from django.db import models

# Create your models here.
# ============================================
# 4. CUSTOMER MODEL
# ============================================

# apps/customers/models.py

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom User Model for Cake House"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ✅ ফোন নম্বর ভ্যালিডেশন ঠিক করুন
    phone_regex = RegexValidator(
        regex=r'^(?:(?:\+?88)?01[3-9]\d{8})$',
        message="সঠিক মোবাইল নম্বর দিন। (যেমন: 01712345678 অথবা +8801712345678)"
    )
    
    phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='Bangladesh')
    
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_vendor = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers_customer'
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email or self.username
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def is_profile_complete(self):
        return all([self.phone, self.address, self.city])


class EmailVerificationToken(models.Model):
    """Email Verification Token Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'customers_email_verification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
        ]
    
    def __str__(self):
        return f"Verification for {self.email} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    def verify(self):
        if self.is_valid:
            self.is_used = True
            self.is_verified = True
            self.save()
            return True
        return False


# apps/customers/models.py — ADD THIS at the bottom of the file
# (keeps a record of every login, useful for a future
# "recent login activity" page à la LinkedIn/Facebook,
# and for the login-alert email itself)

class LoginHistory(models.Model):
    """One row per successful login — powers login-alert emails and,
    later if you want it, a 'where you're logged in' page."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_history'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Parsed from user_agent, filled in at login time so we don't
    # need to re-parse the raw string every time we display history
    device = models.CharField(max_length=100, blank=True)   # e.g. "Mobile", "PC", "Tablet"
    os = models.CharField(max_length=100, blank=True)        # e.g. "Windows 11", "Android 14"
    browser = models.CharField(max_length=100, blank=True)   # e.g. "Chrome 128"

    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customers_login_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = 'Login History'
        verbose_name_plural = 'Login History'

    def __str__(self):
        return f"{self.user.email} @ {self.created_at:%Y-%m-%d %H:%M} from {self.ip_address}"