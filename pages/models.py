from django import forms
from django.db import models
from django.core.validators import RegexValidator

# добавляем перевод
from django.utils.translation import gettext_lazy as _

class AppForm(models.Model):
    name = models.CharField(_('Name'), max_length=30)
    message = models.TextField(_('Message'), blank=True, default='')
    email = models.EmailField(_('Email'), max_length=30)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Inquiry')
        verbose_name_plural = _('Inquiries')


class Contact(models.Model):
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."))

    name = models.CharField(_('Name'), max_length=30)
    message = models.TextField(_('Message'), blank=True, default='')
    email = models.EmailField(_('Email'), max_length=30, blank=True, default='')
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True) # validators should be a list

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Contact')
        verbose_name_plural = _('Contacts')
