from .base import *
from .secrets import *
from datetime import timedelta
from django.conf import settings

DEBUG = False

ALLOWED_HOSTS = ['test.intime.digital', 'www.test.intime.digital']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'test-db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': '/cloudsql/intime-267309:us-central1:test-backend',
        'PORT': '5432',
    }
}

MIDDLEWARE += (
    'api.middleware.LogRestMiddleware',
)

# email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_HOST_USER = 'noreply@intime.digital'
EMAIL_HOST_PASSWORD = 'R28NuT49pR'
EMAIL_PORT = 465
EMAIL_USE_SSL = True

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=10),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': settings.SECRET_KEY,

    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'access',
    'JTI_CLAIM': 'jti',
}
