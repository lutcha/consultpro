from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    'django_extensions',
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = [
    '127.0.0.1',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'consultpro'),
        'USER': os.getenv('POSTGRES_USER', 'consultpro'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'password'),
        'HOST': os.getenv('POSTGRES_HOST', 'db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Email console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery - run tasks synchronously in development
CELERY_TASK_ALWAYS_EAGER = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'False').lower() == 'true'

# Disable S3 in development, use local storage
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Logging
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'
