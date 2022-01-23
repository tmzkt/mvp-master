import copy
from pydoc import locate

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from social_core.backends.google import GoogleOAuth2

from cms.models import HealthData
from cms.converting import cm_to_feet


class CustomUserCreationForm(UserCreationForm):

    password1 = forms.CharField(
        label=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': _('Enter your password')}),
        strip=False,
        min_length=8,
        max_length=18,
    )
    password2 = forms.CharField(
        label=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': _('Repeat your password')}),
        strip=False,
    )

    use_required_attribute=False

    class Meta(UserCreationForm):
        model = get_user_model()
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):

    class Meta(UserChangeForm):
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'image')


class CustomAuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = UsernameField(required=False, widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(
        required=False,
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )

    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }

    def __init__(self, request=None, *args, **kwargs):
        """
        The 'request' parameter is set for custom auth use by subclasses.
        The form data comes in via the standard 'data' kwarg.
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

        # Set the max length and label for the "username" field.
        self.username_field = get_user_model()._meta.get_field(get_user_model().USERNAME_FIELD)
        username_max_length = self.username_field.max_length or 254
        self.fields['username'].max_length = username_max_length
        self.fields['username'].widget.attrs['maxlength'] = username_max_length
        if self.fields['username'].label is None:
            self.fields['username'].label = capfirst(self.username_field.verbose_name)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        # https://stackoverflow.com/questions/547829/how-to-dynamically-load-a-python-class
        # Check if GoogleOAuth2 is added as Authentication Backend.
        if GoogleOAuth2 in [locate(BackEnd) for BackEnd in settings.AUTHENTICATION_BACKENDS]:

            # If previously signed up using google raise validation error.
            if username and get_user_model().objects.filter(
                    email=username,
                    social_auth__provider=GoogleOAuth2.name,
            ).exists():
                raise forms.ValidationError(
                    _("Please log in using your Google account."),
                    code='invalid'
                )

        if not username or not password:
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login or password',
            )

        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        """
        Controls whether the given User may log in. This is a policy setting,
        independent of end-user authentication. This default behavior is to
        allow login by active users, and reject login by inactive users.
        If the given user cannot log in, this method should raise a
        ``forms.ValidationError``.
        If the given user may log in, this method should return None.
        """
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

    def get_user(self):
        return self.user_cache

    def get_invalid_login_error(self):
        msg = _('Invalid login or password')
        self.add_error('username', msg)
        self.add_error('password', msg)
        return forms.ValidationError(
            self.error_messages['invalid_login'],
            code='invalid_login',
            params={'username': self.username_field.verbose_name},
        )


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(min_length=2, max_length=30, validators=[RegexValidator(r'^[-a-zA-ZА-Яа-я]+\Z', message=_('Enter your name'))],
                                 help_text=None, error_messages={'required': _('Enter your name')})
    last_name = forms.CharField(min_length=2, max_length=150, validators=[RegexValidator(r'^[-a-zA-ZА-Яа-я]+\Z', message=_('Enter your last name'))],
                                help_text=None,  error_messages={'required': _('Enter your last name')})

    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name')


class ImageForm(forms.ModelForm):
    class Meta:
        model= get_user_model()
        fields= ('image',)

class HealthDataForm(forms.ModelForm):
    MEASURING_SYSTEM = (
        (1, _('Metric')),
        (2, _('Inch'))
    )
    birth_date = forms.DateField(
        label=_('Birth date'),
        help_text=None,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'placeholder': _('birth date: format 26.10.2006'),
                                                         'type': 'date'
                                                         }))
    measuring_system = forms.ChoiceField(choices=MEASURING_SYSTEM, required=True, help_text=None, label=_('Measuring system'))

    height = forms.FloatField(help_text=None, initial=0, required=True, label=_('Height'),
                               widget=forms.TextInput(attrs={'placeholder': ''}))

    class Meta:
        model = HealthData
        fields = ('birth_date', 'country', 'gender', 'height', 'smoker', 'measuring_system')

    def get_initial_for_field(self, field, field_name):
        value = self.initial.get(field_name, field.initial)
        if field_name == 'height':
            field_name = 'measuring_system'
            unit = self.initial.get(field_name, field.initial)
            if unit == 2 and value:
                value = cm_to_feet(value)
                # value_ft = round(value // 30.48)
                # value_in = round((value / 30.48 - value // 30.48) * 12)
                # value = (float(str(value_ft) + "." + str(value_in)))
                # if value < 1.8:
                #     value = 1.8
                # if value > 8.7:
                #     value = 8.7
        return value

    def clean(self):
        cd = self.cleaned_data
        height = cd['height'] if 'height' in cd else None
        if int(cd['measuring_system']) == 2:
            if not height or height < 1.8 or height > 8.7:
                HealthDataForm.add_error(self, field='height', error=ValidationError(_('The value must be between 1.8 up to 8.7 ft')))
        else:
            if not height or height < 50 or height > 260:
                HealthDataForm.add_error(self, field='height', error=ValidationError(_('The value must be between 50 up to 260 cm')))









