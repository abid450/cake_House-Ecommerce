"""
URL configuration for cooking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from category.views import CategoryViewSet, DessertTypeViewSet
from products.views import ProductViewSet
from cart.views import CartViewSet
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from customers.views import *
from orders.views import *
from dashboard.views import *
from payment.views import *


router =DefaultRouter()
router.register(r'products', ProductViewSet, basename='products')
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'dessert_types', DessertTypeViewSet, basename='dessert_type')
router.register(r'cart', CartViewSet, basename='cart')
router.register('orders', OrderViewSet, basename='order')
router.register('payments', PaymentViewSet, basename='payment')






urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  

    path('api/auth/login/', LoginView.as_view(), name='auth_login'),
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', ProfileView.as_view(), name='profile'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('api/auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('api/auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/auth/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('api/auth/resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    path('api/auth/profile/', ProfileView.as_view(), name='profile'),
    path('api/auth/profile/picture/', DeleteProfilePictureView.as_view(), name='delete_profile_picture'),

    path('api/dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('api/dashboard/revenue-chart/', RevenueChartView.as_view(), name='revenue-chart'),
    path('api/dashboard/top-products/', TopProductsView.as_view(), name='top-products'),
    path('api/dashboard/recent-orders/', RecentOrdersView.as_view(), name='recent-orders'),
    path('api/dashboard/order-status-chart/', OrderStatusChartView.as_view(), name='order-status-chart'),
    path('api/dashboard/category-sales/', CategorySalesView.as_view(), name='category-sales'),
    path('api/dashboard/low-stock/', LowStockProductsView.as_view(), name='low-stock'),
    path('api/dashboard/payment-stats/', PaymentStatsView.as_view(), name='payment-stats'),


    path('home/', TemplateView.as_view(template_name='index.html'), name='home'),  
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),  
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),  
    path('verify-email/', TemplateView.as_view(template_name='verify-email.html'), name='verify_email_page'),
    path('redirect_email/', TemplateView.as_view(template_name='redirect_verify.html'), name='redirect_verify'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile_page'),
    path('checkout/', TemplateView.as_view(template_name='checkout.html'), name='checkout'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('checkout/success/', TemplateView.as_view(template_name='checkout_success.html'), name='checkout_success'),









]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)