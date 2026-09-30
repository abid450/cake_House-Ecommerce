from django.shortcuts import render

# Create your views here.
# ============================================
# 7. CUSTOMER VIEWS
# ============================================

# apps/customers/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    ChangePasswordSerializer,
    ProfileSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationConfirmSerializer,
    ResendVerificationSerializer,
)
from .models import  EmailVerificationToken
from Task.tasks import send_verification_email, send_welcome_email
from .permisions import IsOwnerOrReadOnly
from django.utils import timezone
from .models import LoginHistory
from .utils import get_client_ip, parse_user_agent, get_location_from_ip
from .tasks import send_login_alert_email

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """User Registration with Email Verification"""
    
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # ✅ Create verification token
        token = EmailVerificationToken.objects.create(
            user=user,
            email=user.email
        )
        
        # ✅ Send verification email (Celery task)
        result = send_verification_email.delay(str(user.id), str(token.id))
    
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'User registered successfully. Please check your email to verify your account.',
            'data': {
                'user_id': str(user.id),
                'email': user.email,
                'username': user.username,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'task_id': result.id,  # ✅ Task ID for tracking
            }
        }, status=status.HTTP_201_CREATED)


# ============================================================
# customers/views.py — REPLACE your existing LoginView with this
# ============================================================


class LoginView(APIView):
    """User Login View — now also records login history and sends a
    security alert email with device/location details."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            # ---- gather login context ----
            ip_address = get_client_ip(request)
            ua_string = request.META.get('HTTP_USER_AGENT', '')
            ua_info = parse_user_agent(ua_string)
            location = get_location_from_ip(ip_address)
            login_time = timezone.now()

            # ---- persist for a future "recent activity" page ----
            LoginHistory.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=ua_string,
                device=ua_info['device'],
                os=ua_info['os'],
                browser=ua_info['browser'],
                city=location['city'],
                country=location['country'],
            )

            # ---- fire the alert email asynchronously ----
            send_login_alert_email.delay(str(user.id), {
                'ip_address': ip_address,
                'device': ua_info['device'],
                'os': ua_info['os'],
                'browser': ua_info['browser'],
                'city': location['city'],
                'country': location['country'],
                'login_at': login_time.strftime('%d %B %Y, %I:%M %p'),
            })

            return Response({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'user_id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'is_email_verified': user.is_email_verified,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)

        return Response({
            'success': False,
            'message': 'Invalid credentials',
            'errors': serializer.errors
        }, status=status.HTTP_401_UNAUTHORIZED)


# ============================================================
# cooking/celery.py — ADD to app.conf.task_routes
# ============================================================
#
# 'Task.tasks.send_login_alert_email': {'queue': 'email'},


class LogoutView(APIView):
    """User Logout View"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'success': True,
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)


class RefreshTokenView(TokenRefreshView):
    """Refresh JWT Token"""
    
    def post(self, request, *args, **kwargs):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'success': True,
            'data': serializer.validated_data
        }, status=status.HTTP_200_OK)

        

class ProfileView(APIView):
    """
    User Profile View - Get and Update
    GET  /api/auth/profile/ → Get profile
    PUT  /api/auth/profile/ → Update profile (all fields)
    PATCH /api/auth/profile/ → Partial update
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get user profile"""
        serializer = ProfileSerializer(
            request.user,
            context={'request': request}
        )
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request):
        """Update full profile"""
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        """Partial update profile"""
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# apps/customers/views.py — ADD THIS NEW VIEW
# (paste it right after your existing ProfileView class)

class DeleteProfilePictureView(APIView):
    """
    DELETE /api/auth/profile/picture/
    Removes the user's profile picture — deletes the actual file from
    storage (not just clearing the DB field), so it doesn't leave
    orphaned files behind in media/profiles/.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user

        if not user.profile_picture:
            return Response({
                'success': False,
                'message': 'কোনো প্রোফাইল ছবি পাওয়া যায়নি।'
            }, status=status.HTTP_400_BAD_REQUEST)

        # save=False here because we call user.save() ourselves right after —
        # avoids writing to the DB twice
        user.profile_picture.delete(save=False)
        user.profile_picture = None
        user.save(update_fields=['profile_picture'])

        return Response({
            'success': True,
            'message': 'প্রোফাইল ছবি মুছে ফেলা হয়েছে।'
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """Change Password View"""
    
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    """Verify Email with Token"""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = EmailVerificationConfirmSerializer
    
    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        send_welcome_email.delay(str(user.id))
        
        return Response({
            'success': True,
            'message': 'Email verified successfully! Welcome to Cake House.',
            'data': {
                'user_id': str(user.id),
                'email': user.email,
                'username': user.username,
                'is_email_verified': user.is_email_verified,
                'email_verified_at': user.email_verified_at,
            }
        }, status=status.HTTP_200_OK)


class ResendVerificationEmailView(APIView):
    """Resend Verification Email"""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendVerificationSerializer
    
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.user
        
        token = EmailVerificationToken.objects.create(
            user=user,
            email=user.email
        )
        
        send_verification_email.delay(str(user.id), str(token.id))
        
        return Response({
            'success': True,
            'message': 'Verification email sent successfully. Please check your inbox.',
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """Password Reset Request View"""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        from django_rest_passwordreset.models import ResetPasswordToken
        token = ResetPasswordToken.objects.create(user=user)
        
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token.key}"
        
        send_mail(
            subject='Password Reset - Cake House',
            message=f"""
            Hello {user.username},
            
            You requested to reset your password.
            Click the link below to reset your password:
            
            {reset_link}
            
            This link will expire in 24 hours.
            
            If you didn't request this, please ignore this email.
            
            Best regards,
            Cake House Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        return Response({
            'success': True,
            'message': 'Password reset link sent to your email'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Password Reset Confirm View"""
    
    permission_classes = [permissions.AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            from django_rest_passwordreset.models import ResetPasswordToken
            reset_token = ResetPasswordToken.objects.get(key=token)
            user = reset_token.user
            
            if reset_token.created_at < timezone.now() - timezone.timedelta(hours=24):
                reset_token.delete()
                return Response({
                    'success': False,
                    'message': 'Reset token has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            reset_token.delete()
            
            return Response({
                'success': True,
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
            
        except ResetPasswordToken.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Invalid reset token'
            }, status=status.HTTP_400_BAD_REQUEST)