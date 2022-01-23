from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework import exceptions

from cms.models import Device
from .serializers import DeviceSerializer


class DeviceRegisterMixin(object):

    def device_register(self, data, user):
        flag = False
        try:
            pk=data['device']['device_uuid']
        except:
            raise exceptions.ParseError(detail=_("device data or device_uuid incorrect!"))
        if Device.objects.filter(pk=pk).exists():
            device = Device.objects.get(pk=pk)
            token = OutstandingToken.objects.get(token=device.token)
            if hasattr(token, 'blacklistedtoken'):
                # Token already blacklisted. Skip
                pass
            else:
                BlacklistedToken.objects.create(token=token)

        else:
            # register a new device
            device_serializer = DeviceSerializer(data=data)
            device_serializer.is_valid(raise_exception=True)
            device = device_serializer.save(user=user)
            flag = True
        return device, flag
