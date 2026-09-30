# ============================================
# 5. CUSTOMER SERIALIZERS
# ============================================

# apps/customers/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator, RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, EmailVerificationToken
import re

User = get_user_model()


# ============================================
# JWT TOKEN SERIALIZER
# ============================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT Token Serializer"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        data['user_id'] = str(self.user.id)
        data['email'] = self.user.email
        data['username'] = self.user.username
        data['full_name'] = self.user.full_name
        data['is_staff'] = self.user.is_staff
        data['is_email_verified'] = self.user.is_email_verified
        
        return data


# ============================================
# REGISTER SERIALIZER
# ============================================

class RegisterSerializer(serializers.ModelSerializer):
    """User Registration Serializer"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        error_messages={
            'required': 'পাসওয়ার্ড প্রয়োজন।',
            'blank': 'পাসওয়ার্ড খালি রাখা যাবে না।',
        }
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label=_("Confirm Password"),
        error_messages={
            'required': 'পাসওয়ার্ড নিশ্চিত করুন।',
            'blank': 'পাসওয়ার্ড নিশ্চিতকরণ খালি রাখা যাবে না।',
        }
    )

    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[
            RegexValidator(
                regex=r'^(?:(?:\+?88)?01[3-9]\d{8})$',
                message="সঠিক মোবাইল নম্বর দিন। (যেমন: 01712345678 অথবা +8801712345678)"
            )
        ],
        error_messages={
            'invalid': 'সঠিক মোবাইল নম্বর দিন।',
        }
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'phone', 'address',
            'city', 'state', 'postal_code', 'country'
        ]
        extra_kwargs = {
            'email': {
                'required': True,
                'validators': [EmailValidator()],
                'error_messages': {
                    'required': 'ইমেইল প্রয়োজন।',
                    'blank': 'ইমেইল খালি রাখা যাবে না।',
                    'invalid': 'সঠিক ইমেইল ঠিকানা দিন।',
                }
            },
            'first_name': {
                'required': False,
                'allow_blank': True,
                'error_messages': {
                    'blank': 'নাম খালি রাখা যাবে না।',
                }
            },
            'last_name': {
                'required': False,
                'allow_blank': True,
                'error_messages': {
                    'blank': 'পদবি খালি রাখা যাবে না।',
                }
            },
            'username': {
                'error_messages': {
                    'required': 'ইউজারনেম প্রয়োজন।',
                    'blank': 'ইউজারনেম খালি রাখা যাবে না।',
                    'invalid': 'সঠিক ইউজারনেম দিন।',
                }
            },
        }
    

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password2": _("পাসওয়ার্ড দুটি মিলছে না।")}
            )
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                _("এই ইমেইল দিয়ে ইতিমধ্যে একটি অ্যাকাউন্ট আছে।")
            )
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                _("এই ইউজারনেম দিয়ে ইতিমধ্যে একটি অ্যাকাউন্ট আছে।")
            )
        return value

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


# ============================================
# LOGIN SERIALIZER
# ============================================

class LoginSerializer(serializers.Serializer):
    """User Login Serializer"""
    
    username = serializers.CharField(
        required=True,
        error_messages={
            'required': 'ইউজারনেম প্রয়োজন।',
            'blank': 'ইউজারনেম খালি রাখা যাবে না।',
        }
    )
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True,
        error_messages={
            'required': 'পাসওয়ার্ড প্রয়োজন।',
            'blank': 'পাসওয়ার্ড খালি রাখা যাবে না।',
        }
    )
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError(
                _("ইউজারনেম বা পাসওয়ার্ড ভুল।")
            )
        
        if not user.is_active:
            raise serializers.ValidationError(
                _("এই অ্যাকাউন্টটি নিষ্ক্রিয় করা হয়েছে।")
            )
        
        attrs['user'] = user
        return attrs


# ============================================
# LOGOUT SERIALIZER
# ============================================

class LogoutSerializer(serializers.Serializer):
    """User Logout Serializer"""
    
    refresh = serializers.CharField(
        required=True,
        error_messages={
            'required': 'রিফ্রেশ টোকেন প্রয়োজন।',
            'blank': 'রিফ্রেশ টোকেন খালি রাখা যাবে না।',
        }
    )
    
    def validate(self, attrs):
        try:
            token = RefreshToken(attrs['refresh'])
            token.blacklist()
        except Exception:
            raise serializers.ValidationError(
                _("টোকেনটি সঠিক নয়।")
            )
        return attrs


# ============================================
# REFRESH TOKEN SERIALIZER
# ============================================

class RefreshTokenSerializer(serializers.Serializer):
    """Refresh Token Serializer"""
    
    refresh = serializers.CharField(
        required=True,
        error_messages={
            'required': 'রিফ্রেশ টোকেন প্রয়োজন।',
            'blank': 'রিফ্রেশ টোকেন খালি রাখা যাবে না।',
        }
    )
    
    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs['refresh'])
            return {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
        except Exception:
            raise serializers.ValidationError(
                _("টোকেনটি সঠিক নয়।")
            )


# ============================================
# CHANGE PASSWORD SERIALIZER
# ============================================

class ChangePasswordSerializer(serializers.Serializer):
    """Change Password Serializer"""
    
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True,
        error_messages={
            'required': 'পুরোনো পাসওয়ার্ড প্রয়োজন।',
            'blank': 'পুরোনো পাসওয়ার্ড খালি রাখা যাবে না।',
        }
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        write_only=True,
        error_messages={
            'required': 'নতুন পাসওয়ার্ড প্রয়োজন।',
            'blank': 'নতুন পাসওয়ার্ড খালি রাখা যাবে না।',
        }
    )
    new_password2 = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True,
        error_messages={
            'required': 'নতুন পাসওয়ার্ড নিশ্চিত করুন।',
            'blank': 'নতুন পাসওয়ার্ড নিশ্চিতকরণ খালি রাখা যাবে না।',
        }
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password2": _("নতুন পাসওয়ার্ড দুটি মিলছে না।")}
            )
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _("পুরোনো পাসওয়ার্ড সঠিক নয়।")
            )
        return value


# ============================================
# PROFILE SERIALIZER
# ============================================
# apps/customers/serializers.py (ProfileSerializer fix)

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import re

User = get_user_model()


def validate_phone(value):
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


class ProfileSerializer(serializers.ModelSerializer):
    """User Profile Serializer with Update Support"""
    
    # ✅ Read-only fields
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_email_verified = serializers.BooleanField(read_only=True)
    is_profile_complete = serializers.BooleanField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # ✅ Writable fields
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validate_phone],
        max_length=17
    )
    address = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    state = serializers.CharField(required=False, allow_blank=True, max_length=100)
    postal_code = serializers.CharField(required=False, allow_blank=True, max_length=20)
    country = serializers.CharField(required=False, allow_blank=True, max_length=100)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    email_notifications = serializers.BooleanField(required=False)
    sms_notifications = serializers.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name',
            'first_name', 'last_name', 'phone',
            'address', 'city', 'state', 'postal_code', 'country',
            'profile_picture', 'date_of_birth',
            'is_email_verified', 'is_profile_complete',
            'email_notifications', 'sms_notifications',
            'date_joined', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'username', 'email', 'full_name',
            'is_email_verified', 'is_profile_complete',
            'date_joined', 'created_at', 'updated_at'
        ]
    
    def validate_phone(self, value):
        """Validate phone number"""
        if value:
            return validate_phone(value)
        return value
    
    def validate_profile_picture(self, value):
        """Validate profile picture size"""
        if value and value.size > 2 * 1024 * 1024:  # 2MB
            raise serializers.ValidationError("ছবির সাইজ ২ MB এর কম হতে হবে")
        return value
    
    def update(self, instance, validated_data):
        """Update user profile"""
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

# ============================================
# EMAIL VERIFICATION SERIALIZERS
# ============================================

class EmailVerificationRequestSerializer(serializers.Serializer):
    """Request Email Verification Serializer"""
    
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'ইমেইল প্রয়োজন।',
            'blank': 'ইমেইল খালি রাখা যাবে না।',
            'invalid': 'সঠিক ইমেইল ঠিকানা দিন।',
        }
    )
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("এই ইমেইল দিয়ে কোনো অ্যাকাউন্ট নেই।")
        return value


class EmailVerificationConfirmSerializer(serializers.Serializer):
    """Confirm Email Verification Serializer"""
    
    token = serializers.UUIDField(
        required=True,
        error_messages={
            'required': 'ভেরিফিকেশন টোকেন প্রয়োজন।',
            'invalid': 'ভেরিফিকেশন টোকেনটি সঠিক নয়।',
        }
    )
    
    def validate_token(self, value):
        try:
            token_obj = EmailVerificationToken.objects.get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("ভেরিফিকেশন টোকেনটি সঠিক নয়।")
        
        if token_obj.is_expired:
            raise serializers.ValidationError("ভেরিফিকেশন টোকেনের মেয়াদ শেষ হয়ে গেছে।")
        
        if token_obj.is_used:
            raise serializers.ValidationError("এই ভেরিফিকেশন টোকেনটি ইতিমধ্যে ব্যবহার করা হয়েছে।")
        
        self.token_obj = token_obj
        return value
    
    def save(self):
        token = self.token_obj
        token.verify()
        
        user = token.user
        user.is_email_verified = True
        user.email_verified_at = timezone.now()
        user.save()
        
        return user


class ResendVerificationSerializer(serializers.Serializer):
    """Resend Verification Email Serializer"""
    
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'ইমেইল প্রয়োজন।',
            'blank': 'ইমেইল খালি রাখা যাবে না।',
            'invalid': 'সঠিক ইমেইল ঠিকানা দিন।',
        }
    )
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("এই ইমেইল দিয়ে কোনো অ্যাকাউন্ট নেই।")
        
        if user.is_email_verified:
            raise serializers.ValidationError("এই ইমেইলটি ইতিমধ্যে ভেরিফাই করা হয়েছে।")
        
        recent_tokens = EmailVerificationToken.objects.filter(
            user=user,
            is_used=False,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
        )
        
        if recent_tokens.exists():
            raise serializers.ValidationError(
                "সম্প্রতি একটি ভেরিফিকেশন ইমেইল পাঠানো হয়েছে। অনুগ্রহ করে ৫ মিনিট অপেক্ষা করুন।"
            )
        
        self.user = user
        return value


# ============================================
# PASSWORD RESET SERIALIZERS
# ============================================

class PasswordResetSerializer(serializers.Serializer):
    """Password Reset Serializer"""
    
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'ইমেইল প্রয়োজন।',
            'blank': 'ইমেইল খালি রাখা যাবে না।',
            'invalid': 'সঠিক ইমেইল ঠিকানা দিন।',
        }
    )
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("এই ইমেইল দিয়ে কোনো অ্যাকাউন্ট নেই।")
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password Reset Confirm Serializer"""
    
    token = serializers.CharField(
        required=True,
        error_messages={
            'required': 'রিসেট টোকেন প্রয়োজন।',
            'blank': 'রিসেট টোকেন খালি রাখা যাবে না।',
        }
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        write_only=True,
        error_messages={
            'required': 'নতুন পাসওয়ার্ড প্রয়োজন।',
            'blank': 'নতুন পাসওয়ার্ড খালি রাখা যাবে না।',
        }
    )
    new_password2 = serializers.CharField(
        required=True,
        style={'input_type': 'password'},
        write_only=True,
        error_messages={
            'required': 'নতুন পাসওয়ার্ড নিশ্চিত করুন।',
            'blank': 'নতুন পাসওয়ার্ড নিশ্চিতকরণ খালি রাখা যাবে না।',
        }
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password2": _("নতুন পাসওয়ার্ড দুটি মিলছে না।")}
            )
        return attrs