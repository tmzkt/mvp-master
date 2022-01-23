import os

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import ValidationError

from .models import AppForm, Contact


# def validate_file_extension(value):
#     ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
#     valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.png', '.xlsx', '.xls']
#     if not ext.lower() in valid_extensions:
#         raise ValidationError(u'Unsupported file extension.')


class ApplicationForm(forms.ModelForm):
    use_required_attribute = False

    name = forms.CharField(label=False,
                           widget=forms.TextInput(
                               attrs={'placeholder': _("Enter your name"), 'required': False}))
    message = forms.CharField(label=False, required=False,
                              widget=forms.Textarea(
                                  attrs={'placeholder': _("Message"), 'rows': 2, 'cols': 40, 'required': False}))

    email = forms.EmailField(label=False,
                             widget=forms.TextInput(
                                 attrs={'placeholder': _("Enter your email"), 'required': False}))

    class Meta:
        model = AppForm
        fields = ('name', 'message', 'email')


class ContactForm(forms.ModelForm):
    use_required_attribute = False

    name = forms.CharField(label=False,
                           widget=forms.TextInput(
                               attrs={'placeholder': _("Enter your name"), 'required': False}))
    message = forms.CharField(label=False, required=False,
                              widget=forms.Textarea(
                                  attrs={'placeholder': _("Message"), 'rows': 2, 'cols': 40, 'required': False}))

    email = forms.EmailField(label=False,
                             widget=forms.TextInput(
                                 attrs={'placeholder': _("Enter your email"), 'required': False}))

    phone_number = forms.RegexField(label=False,
                            regex=r'^\+?1?\d{9,15}$',
                            widget=forms.TextInput(
                                 attrs={'placeholder': _("Enter your phone number"), 'required': False})
                            )

    class Meta:
        model = Contact
        fields = ('name', 'message', 'email', 'phone_number')


class SendingPresentationForm(forms.Form):
    title = forms.CharField(required=True, label=_('Title'),
                            widget=forms.TextInput(
                                attrs={'readonly': 'readonly', 'placeholder': _('Title'), 'required': False}))
    name = forms.CharField(label=False, required=True,
                           widget=forms.TextInput(
                               attrs={'placeholder': _("Enter your name"), 'required': False}))
    email = forms.EmailField(label=False, required=True,
                             widget=forms.TextInput(
                                 attrs={'placeholder': _("Enter your email"), 'required': False}))
    message = forms.CharField(label=False, required=True,
                              widget=forms.Textarea(
                                  attrs={'placeholder': _("Message"), 'rows': 2, 'cols': 40, 'required': False}))
    file = forms.FileField(label=False, required=False,
                           widget=forms.FileInput(
                              attrs={'placeholder': _("Choose File"), 'required': False}))

