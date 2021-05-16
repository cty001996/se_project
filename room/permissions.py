from rest_framework import permissions


class IsAdminOrManager(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return True
