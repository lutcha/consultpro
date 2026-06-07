from .base import *
from .base import _env_list, _unique_list, _origin_from_url

DEBUG = False

_allowed = _env_list('ALLOWED_HOSTS', 'consultpro.cv,www.consultpro.cv,api.consultpro.com')
# DO App Platform health checks use the container's internal IP.
# With SECURE_PROXY_SSL_HEADER set, host validation is handled by DO's proxy layer.
ALLOWED_HOSTS = _unique_list(_allowed + ['localhost', '127.0.0.1', '*'])

# Security
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() not in ('false', '0', 'no')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

import ssl

def _with_celery_ssl_cert_reqs(url):
    if url and url.startswith('rediss://') and 'ssl_cert_reqs=' not in url:
        separator = '&' if '?' in url else '?'
        return f'{url}{separator}ssl_cert_reqs=CERT_NONE'
    return url


CELERY_BROKER_URL = _with_celery_ssl_cert_reqs(CELERY_BROKER_URL)
CELERY_RESULT_BACKEND = _with_celery_ssl_cert_reqs(CELERY_RESULT_BACKEND)
CELERY_BROKER_USE_SSL = {'ssl_cert_reqs': ssl.CERT_NONE}
CELERY_REDIS_BACKEND_USE_SSL = {'ssl_cert_reqs': ssl.CERT_NONE}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
        'OPTIONS': {
            'ssl_cert_reqs': 'none',
        }
    }
}


def _is_placeholder_env(value):
    return not value or value == 'placeholder-set-via-dashboard'


if _is_placeholder_env(os.getenv('AWS_S3_ENDPOINT_URL')):
    try:
        del DEFAULT_FILE_STORAGE
    except NameError:
        pass
    try:
        del STATICFILES_STORAGE
    except NameError:
        pass
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }

# Sentry
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.5,
        send_default_pii=True,
    )
