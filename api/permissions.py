from rest_framework import permissions
from . import app_settings

class IsBase(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.META['HTTP_KEY'] == app_settings.INCOME_MAIN_BASE_TOKEN
