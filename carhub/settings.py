"""
Django settings for carhub project.
"""

import os
from pathlib import Path

# Load environment variables from .env file (optional for Docker/production)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

import sys
TESTING = 'test' in sys.argv

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-l)w@5)mnvdg*6950)+7^(75@vw6)uu!ayicvs(3%bba6w2ec80'
)

DEBUG = os.environ.get('DEBUG', '1') == '1'

# Жёсткая гарантия для продакшен-стека (docker-compose.prod.yml выставляет DJANGO_ENV=production)
# Даже если в .env.prod случайно DEBUG=1 или compose не переопределил — в проде будет DEBUG=False.
if os.environ.get('DJANGO_ENV', '').lower() == 'production':
    DEBUG = False

allowed_hosts = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in allowed_hosts.split(',') if h.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*'] if DEBUG else []

# Стартовый лог — будет видно в `docker-compose -f docker-compose.prod.yml logs web`
# Помогает быстро понять, в каком режиме запустился контейнер (особенно на защите).
print(f">>> STARTUP: DEBUG={DEBUG}, DJANGO_ENV={os.environ.get('DJANGO_ENV', 'not-set')}, GLITCHTIP_DSN={'set' if os.environ.get('GLITCHTIP_DSN') else 'not-set'}", flush=True)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'django_filters',
    'simple_history',
    'import_export',
    'core',
    'django_celery_beat',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.vk',
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'carhub.middleware.Capture404Middleware',
]

ROOT_URLCONF = 'carhub.urls'

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

WSGI_APPLICATION = 'carhub.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
AUTH_USER_MODEL = 'core.User'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

if not DEBUG:
    try:
        import whitenoise  # noqa
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
        STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    except ImportError:
        pass

if DEBUG and not TESTING:
    INSTALLED_APPS += ['debug_toolbar', 'silk']

    try:
        common_idx = MIDDLEWARE.index('django.middleware.common.CommonMiddleware')
        MIDDLEWARE.insert(common_idx + 1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    except ValueError:
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

    MIDDLEWARE.insert(1, 'silk.middleware.SilkyMiddleware')

    INTERNAL_IPS = ['127.0.0.1', 'localhost']
    INTERNAL_IPS += ['172.17.0.1', '172.18.0.1']

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'SHOW_TEMPLATE_CONTEXT': False,
        'RESULTS_CACHE_SIZE': 50,
    }

    SILKY_PYTHON_PROFILER = True
    SILKY_AUTHENTICATION = False
    SILKY_AUTHORISATION = False
    SILKY_META = True
    SILKY_INTERCEPT_PERCENT = 100

if TESTING:
    for tool in ['debug_toolbar', 'silk']:
        if tool in INSTALLED_APPS:
            INSTALLED_APPS.remove(tool)

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 1025))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', '0') == '1'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'CarHub <noreply@carhub.local>'

if TESTING:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache'
    CELERY_CACHE_BACKEND = 'memory'
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

SITE_ID = 1

if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_LOGIN_METHODS = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_QUERY_EMAIL = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
        }
    },
    'vk': {
        'SCOPE': [
            'email',
        ],
        'APP': {
            'client_id': os.environ.get('VK_CLIENT_ID', ''),
            'secret': os.environ.get('VK_CLIENT_SECRET', ''),
        }
    }
}

ACCOUNT_LOGIN_ON_GET = True

if not TESTING:
    _raw_dsn = os.environ.get("GLITCHTIP_DSN")
    GLITCHTIP_DSN = None
    if _raw_dsn:
        # Убираем возможные кавычки и пробелы из .env (частая причина, почему события не уходят)
        GLITCHTIP_DSN = _raw_dsn.strip().strip('"').strip("'")
    if GLITCHTIP_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.django import DjangoIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration
            import logging

            sentry_logging = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.WARNING,  # 404-и от django.request идут на WARNING при DEBUG=False
            )

            sentry_sdk.init(
                dsn=GLITCHTIP_DSN,
                integrations=[
                    DjangoIntegration(),
                    sentry_logging,
                ],
                traces_sample_rate=0.01,
                auto_session_tracking=False,
                environment=os.environ.get("DJANGO_ENV", "production"),
                send_default_pii=False,
            )
            # Прямой print + flush — максимально надёжно видно в `docker logs` даже под gunicorn
            print(">>> GlitchTip initialized successfully with DSN (cloud)", flush=True)
            logging.getLogger("gunicorn.error").info(">>> GlitchTip initialized successfully with DSN (cloud)")
        except ImportError:
            import logging
            logging.getLogger(__name__).warning(
                "GLITCHTIP_DSN is set but 'sentry-sdk' package is not installed. "
                "Add it via 'pip install sentry-sdk' and rebuild your Docker image."
            )

# Logging configuration to make sure 404s (logged by Django at WARNING level when DEBUG=False)
# and other errors are sent to GlitchTip via the LoggingIntegration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
