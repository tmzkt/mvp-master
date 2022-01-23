from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.exceptions import DetailDictMixin


class EmailDontConfirm(DetailDictMixin, APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('Incorrect authentication credentials.')
    default_code = 'authentication_failed'


class DeviceNotRegister(DetailDictMixin, APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Device not registered")
    default_code = 'device registration_failed'
