"""
Django settings for ConsultPro project.
"""

import os
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables. .env.local is ignored by Git and may override local secrets.
load_dotenv()
load_dotenv(BASE_DIR / '.env.local', override=True)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


def _env_list(name, default=''):
    return [item.strip() for item in os.getenv(name, default).split(',') if item.strip()]


def _unique_list(items):
    return list(dict.fromkeys(item for item in items if item))


def _origin_from_url(url):
    parsed = urlparse(str(url or '').strip())
    if not parsed.scheme or not parsed.netloc:
        return ''
    return f'{parsed.scheme}://{parsed.netloc}'


# Application definition
DJANGO_APPS = [
    'jazzmin',  # must be before django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'storages',
]

LOCAL_APPS = [
    'apps.core',
    'apps.tenants',
    'apps.users',
    'apps.opportunities',
    'apps.proposals',
    'apps.quality_checks',
    'apps.notifications',
    'apps.teams',
    'apps.ai_services',
    'apps.projects',
    'apps.curriculum',
    'apps.scraping',
    'apps.partners',
    'apps.analytics',
    'apps.compliance',
    'apps.issue_tree',
    'apps.knowledge',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

JAZZMIN_SETTINGS = {
    'site_title': 'ConsultPro Admin',
    'site_header': 'ConsultPro',
    'site_brand': 'ConsultPro',
    'site_logo': None,
    'login_logo': None,
    'welcome_sign': 'Bem-vindo ao ConsultPro',
    'copyright': 'ConsultPro © 2026',
    'search_model': [
        'users.User',
        'opportunities.Opportunity',
        'proposals.Proposal',
        'scraping.ScrapingSource',
        'scraping.ScrapedOpportunity',
    ],
    'topmenu_links': [
        {'name': 'Site', 'url': '/', 'new_window': True},
        {'name': 'API Docs', 'url': '/api/docs/', 'new_window': True},
        {'name': 'Sources', 'url': '/admin/scraping/scrapingsource/', 'new_window': False},
    ],
    'usermenu_links': [
        {'name': 'API Docs', 'url': '/api/docs/', 'new_window': True},
    ],
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': [],
    'hide_models': [],
    'order_with_respect_to': [
        'auth',
        'users',
        'opportunities',
        'proposals',
        'projects',
        'teams',
        'curriculum',
        'scraping',
        'notifications',
        'quality_checks',
        'ai_services',
    ],
    'custom_links': {
        'scraping': [
            {
                'name': 'Run All Sources',
                'url': 'run_all_scraping_sources',
                'icon': 'fas fa-play-circle',
                'permissions': ['scraping.change_scrapingsource'],
            },
        ],
    },
    'icons': {
        # Auth
        'auth': 'fas fa-users-cog',
        'auth.user': 'fas fa-user',
        'auth.Group': 'fas fa-users',
        # Users
        'users.User': 'fas fa-user-tie',
        'users.Certification': 'fas fa-certificate',
        # Opportunities
        'opportunities.Opportunity': 'fas fa-briefcase',
        'opportunities.Requirement': 'fas fa-list-check',
        'opportunities.Risk': 'fas fa-exclamation-triangle',
        # Proposals
        'proposals.Proposal': 'fas fa-file-alt',
        'proposals.ProposalSection': 'fas fa-paragraph',
        'proposals.Budget': 'fas fa-coins',
        'proposals.Comment': 'fas fa-comments',
        # Projects
        'projects.Project': 'fas fa-project-diagram',
        'projects.ProjectTask': 'fas fa-tasks',
        'projects.ProjectMilestone': 'fas fa-flag',
        'projects.ProjectRisk': 'fas fa-shield-alt',
        # Teams
        'teams.Team': 'fas fa-users',
        # Curriculum
        'curriculum.Curriculum': 'fas fa-id-card',
        'curriculum.CVTemplate': 'fas fa-file-code',
        # Scraping
        'scraping.ScrapingSource': 'fas fa-spider',
        'scraping.ScrapedOpportunity': 'fas fa-search-dollar',
        'scraping.ScrapingJob': 'fas fa-clock',
        'scraping.ScrapingAlert': 'fas fa-exclamation-circle',
        # Notifications
        'notifications.Notification': 'fas fa-bell',
        'notifications.ActivityLog': 'fas fa-history',
        # Quality
        'quality_checks.QualityCheck': 'fas fa-check-circle',
        'quality_checks.QCCheckCategory': 'fas fa-layer-group',
        # AI
        'ai_services.AIConfiguration': 'fas fa-robot',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',
    'related_modal_active': True,
    'custom_css': None,
    'custom_js': None,
    'use_google_fonts_cdn': True,
    'show_ui_builder': False,
    'changeform_format': 'horizontal_tabs',
    'changeform_format_overrides': {
        'scraping.scrapingsource': 'collapsible',
        'scraping.scrapedopportunity': 'collapsible',
    },
    'language_chooser': False,
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-primary',
    'accent': 'accent-primary',
    'navbar': 'navbar-dark',
    'no_navbar_border': False,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-primary',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'default',
    'dark_mode_theme': None,
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.tenants.middleware.TenantContextMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

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


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'pt-pt'

TIME_ZONE = 'Europe/Lisbon'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 480))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 30))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

# Spectacular (OpenAPI/Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'ConsultPro API',
    'DESCRIPTION': 'API para plataforma de gestão de consultoria internacional',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Redis / Cache
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

# Celery
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/1')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# MinIO / S3 Storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'minioadmin')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'minioadmin')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'consultpro')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL', 'http://minio:9000')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = 'private'
AWS_S3_VERIFY = False

# Email
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.sendgrid.net' if SENDGRID_API_KEY else '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'apikey' if SENDGRID_API_KEY else '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', SENDGRID_API_KEY)
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@consultpro.com')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://consultpro.cv')
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '15'))

# AI / LLM Configuration
# Providers: openai | deepseek | kimi | anthropic | qwen | google | mock
AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')
AI_ALWAYS_MOCK = os.getenv('AI_ALWAYS_MOCK', 'False').lower() == 'true'

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# DeepSeek (https://platform.deepseek.com) - very cost-effective
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

# Kimi / Moonshot AI (https://platform.moonshot.cn) - excellent long context
KIMI_API_KEY = os.getenv('KIMI_API_KEY', '')
KIMI_MODEL = os.getenv('KIMI_MODEL', 'moonshot-v1-128k')

# Anthropic Claude (https://console.anthropic.com) - best reasoning quality
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-haiku-20241022')

# Qwen / Alibaba Cloud (https://www.alibabacloud.com/help/en/model-studio) - strong multilingual
QWEN_API_KEY = os.getenv('QWEN_API_KEY', '')
QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-max')

# Google Gemini (https://aistudio.google.com) - fast, generous free tier
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_MODEL = os.getenv('GOOGLE_MODEL', 'gemini-2.0-flash')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
