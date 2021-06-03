from rest_framework import permissions


class IsVerify(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_verify
