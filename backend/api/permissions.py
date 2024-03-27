from rest_framework import permissions


class IsAuthorOrAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
        Позволяет доступ только авторам и администраторам
        или только чтение для всех остальных.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.is_admin
            or request.user.is_superuser
        )


class IsAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
        Позволяет доступ только администраторам
        или только чтение для всех остальных.
    """
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            and (request.user.is_staff
                 or request.user.is_admin
                 or request.user.is_superuser)
        )


class IsAdmin(permissions.BasePermission):
    """ Позволяет доступ только администраторам."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_admin
            or request.user.is_superuser
            or request.user.is_staff
        )
