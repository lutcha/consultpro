"""
Local development settings - SQLite, no Docker required.
Use this for quick testing and validation.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# SQLite database for local quick testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable S3/MinIO, use local file storage
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email console backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Run Celery tasks synchronously (no Redis needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache'
CELERY_CACHE_BACKEND = 'memory'

# Logging to console only
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
