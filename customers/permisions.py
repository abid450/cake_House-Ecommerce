# ============================================
# 8. CUSTOMER PERMISSIONS
# ============================================

# apps/customers/permissions.py

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow only owners to edit"""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """Allow read-only for unauthenticated users"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow only admins to edit"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsVerified(permissions.BasePermission):
    """Allow only verified users"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_email_verified