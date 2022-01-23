from .base import *
from .secrets import *
from datetime import timedelta
from django.conf import settings

DEBUG = False

ALLOWED_HOSTS = ['intime.digital', 'www.intime.digital', 'longevityintime.org', 'ec2-3-143-216-60.us-east-2.compute.amazonaws.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'superintimedb',
        'USER': 'intime',
        'PASSWORD': 'ScgKEhtsSriqQx2q',
        'HOST': 'database-2.cjsljpd52fku.us-east-2.rds.amazonaws.com',
        'PORT': '5432',
    }
}

# MIDDLEWARE += (
#     'api.middleware.LogRestMiddleware',
# )

# email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_HOST_USER = 'noreply@intime.digital'
EMAIL_HOST_PASSWORD = 'R28NuT49pR'
EMAIL_PORT = 465
EMAIL_USE_SSL = True

# token settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=10),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,

    'ALGORITHM': 'RS256',
    'SIGNING_KEY': """-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----""",

    'VERIFYING_KEY': """-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAysobBnNRBXHxSI1X6RFz
MQQRkLvjxfLUFtQMTtBcHhOfpqzamoEyR1MVNQMQcJRGa2n8ZexD6UdutE3Eqzf0
eeSX3qqRE5Fgty2wuPH9NCIEo5ycD82um277+p/jSmTpP2g47htcnCguB3ZAqXGw
Rx22HsocgPyqgcPzSLLAw0qoQOC4kE5nrCD5/G5F/WfRMiYfNdkBKghXx5CLugUH
9GGLEnjUaLP16Hhf6hN/X3wdsoHRdLB4TkBYQ8KRNaQSJRKpiC/pAxj8fDPF53B9
qKx5tHQKlHlPR6lx/kcuTCWB2T4nPn21wIQFLrSf4izMegJO9kVq/b08QW3CYUdF
6hANC18vKWZOvWGU2yadVIgPIKzs8AiVvaP7prJByIVY18mlBr6vA0iFOm2SfKbp
53AqjMTFErzFuBm5kC9EteJ3+vBtxycC773ffrJwS9NXLh8Y13x90956ylXxZySD
vQk7DAwerlFQ/p2bsumHk+HeHYITJT+Ln2UzqOSC8gCCfKa8mspDg3c19825ts+Z
85vk1xWQU+f+PaONDDrUfM9ywaGdpjepM3DFhpn7to6kz2vwiDa79txyzmrk95GD
trvapulWqRx4KyAQMktbWrLVmI2+fI8+TgDnSfk1CNcVSgyQaSqNMQilS1TlS+xx
+aFTRNWE0IJGZHA9FtACOf0CAwEAAQ==
-----END PUBLIC KEY-----""",

    'AUDIENCE': None,
    'ISSUER': None,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'access',
    'JTI_CLAIM': 'jti',
}
