from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.encoding import force_text
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.urls import reverse

from . import app_settings
from django.conf import settings


User = get_user_model()
signer = TimestampSigner(sep='/', salt='abrahadabra')


# Create encode url with uuid
def encoder(scheme, host, user, app_bmi="BMI Disease Tracker"):
    # Encode a uuid
    user_crypt = urlsafe_base64_encode(force_bytes(user.id))
    # Sign encoded uuid
    signed_user = signer.sign(user_crypt)
    kwargs = {
        "signed_user": signed_user
    }
    # Create activation url
    activation_url = reverse("users:activate_user_account", kwargs=kwargs)
    activate_url = "{0}://{1}{2}".format(scheme, host, activation_url)
    static_url = "{0}://{1}{2}".format(scheme, host, settings.STATIC_URL)
    context = {
        'user': user,
        'activate_url': activate_url,
        'fullurlstatic': static_url,
        'app_bmi': app_bmi,
    }
    return context


# decode url with userid
def decoder(request, signed_user):
    try:
        # Check a signature
        user_encrypt = signer.unsign(signed_user, max_age=timedelta(days=app_settings.CONFIRM_EMAIL_LIFETIME))
        signature = True
    except SignatureExpired:
        user_encrypt = signer.unsign(signed_user, max_age=timedelta(days=365))
        signature = False
    except (BadSignature):
        return None, None

    try:
        # decode user uuid
        uid = force_text(urlsafe_base64_decode(user_encrypt))
        user = User.objects.get(pk=uid)
    except User.DoesNotExist:
        user = None
    return user, signature
