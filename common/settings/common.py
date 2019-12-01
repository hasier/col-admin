"""
Django settings for col-admin project on Heroku. For more info, see:
https://github.com/heroku/heroku-django-template

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import logging
import os

import dj_database_url
import environ
import sentry_sdk
from django.contrib.admin.sites import AdminSite
from django.templatetags.static import static
from django.utils.functional import SimpleLazyObject
from material.admin.default.apps import DefaultMaterialConfig
from sentry_sdk.integrations.django import DjangoIntegration

logger = logging.getLogger(__name__)
env = environ.Env()

# Site defaults
AdminSite.site_title = 'Castellers of London'
AdminSite.site_header = 'Castellers of London'
AdminSite.favicon = SimpleLazyObject(lambda: static('CoL_Logo.png'))
DefaultMaterialConfig.default_site = 'apps.sites.NoThemeMaterialAdminSite'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = BASE_DIR

# Development settings
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/
SECRET_KEY = env('DJANGO_SECRET_KEY', default='secret')

DEBUG = env.bool('DEBUG', default=False)
if DEBUG:
    logger.warning('DEBUG is enabled!')

# Logging settings
# https://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/
LOGGING_CONFIG = None
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'},
        'require_debug_true': {'()': 'django.utils.log.RequireDebugTrue'},
    },
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[%(server_time)s] %(message)s',
        },
    },
    'handlers': {
        'console': {'level': 'INFO', 'class': 'logging.StreamHandler'},
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {'handlers': ['console', 'mail_admins'], 'level': 'INFO'},
        'django.server': {'handlers': ['django.server'], 'level': 'INFO', 'propagate': False},
    },
}

# Sentry
sentry_sdk.init(dsn=env('SENTRY_DSN', default=None), integrations=[DjangoIntegration()])

# Email backend settings
# https://github.com/sklarsa/django-sendgrid-v5
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = env('SENDGRID_API_KEY', default=None)
SENDGRID_SANDBOX_MODE_IN_DEBUG = True

# Application definition
INSTALLED_APPS = [
    'apps.membership.apps.MembershipConfig',
    'material.admin',
    'material.admin.default',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # Disable Django's own staticfiles handling in favour of WhiteNoise, for
    # greater consistency between gunicorn and `./manage.py runserver`. See:
    # http://whitenoise.evans.io/en/stable/django.html#using-whitenoise-in-development
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'memoize',
    # allauth
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.instagram',
    'allauth.socialaccount.providers.microsoft',
    'allauth.socialaccount.providers.openid',
    'allauth.socialaccount.providers.twitter',
    # invitations
    'invitations',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'apps.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [(os.path.join(BASE_DIR, 'templates'))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Add each_context from admin sites to all views (used for allauth accounts)
                'common.utils.context_processors.each_context',
            ],
            'libraries': {
                'admin.admin_modify': 'templatetags.admin.admin_modify',
                'admin.material': 'templatetags.admin.material',
            },
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = 'apps.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
# Change 'default' database configuration with $DATABASE_URL.
DATABASES = {'default': dj_database_url.config(conn_max_age=500)}
if not DATABASES['default']:
    raise RuntimeError(
        'Cannot start without a valid DB connection: {}'.format(DATABASES['default'])
    )

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env('REDISCLOUD_URL'),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# Auth
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# allauth
SITE_ID = 1
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': ['id', 'email', 'name', 'first_name', 'last_name'],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v2.12',
    },
    'google': {'SCOPE': ['profile', 'email'], 'AUTH_PARAMS': {'access_type': 'online'}},
    'openid': {'SERVERS': [{'id': 'yahoo', 'name': 'Yahoo', 'openid_url': 'http://me.yahoo.com'}]},
}
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    # 'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = False  # As long as signup remains invite only

# Invitations
ACCOUNT_ADAPTER = 'invitations.models.InvitationsAdapter'
INVITATIONS_INVITATION_ONLY = True
INVITATIONS_ADAPTER = ACCOUNT_ADAPTER

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
