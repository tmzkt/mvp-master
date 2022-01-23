from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.authentication import JWTAuthentication
from .exceptions import EmailDontConfirm

class CustomJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        if not user.email_confirm:
            raise EmailDontConfirm(_('Email not confirmed'))
        return user
