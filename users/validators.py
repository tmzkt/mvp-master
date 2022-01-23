from django.core.exceptions import ValidationError

from django.utils.translation import gettext_lazy as _


class SpecialCharValidator:
    def __init__(self, special_chars=(' ')):
        self.special_chars = special_chars

    def validate(self, password, user=None):
        if password.isalnum():
            raise ValidationError(
                _('Password must have atleast 1 special character: %s') % ', '.join(self.special_chars),
                code=_('no special chars')
            )

    def get_help_text(self):
        return _('Password must have atleast 1 special character: %s') % ', '.join(self.special_chars)
