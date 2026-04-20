from rest_framework import permissions


class IsOwnerOrManager(permissions.BasePermission):
    """Allow access only to the owner or manager/admin users."""

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.role in ('manager', 'admin'):
            return True
        return hasattr(obj, 'created_by') and obj.created_by == request.user


# Alias for backward compatibility
IsOwnerOrAdmin = IsOwnerOrManager


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read-only access to anyone, write access to admins only."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsConsultantOrManager(permissions.BasePermission):
    """Allow access to consultants, managers, and admin users."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('consultant', 'manager', 'admin') or request.user.is_staff


class IsManager(permissions.BasePermission):
    """Allow access to managers and admin users only."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ('manager', 'admin') or request.user.is_staff
