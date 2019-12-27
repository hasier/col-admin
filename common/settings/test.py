from .common import *

DATABASES = {'default': dj_database_url.config(conn_max_age=500, env='TEST_DATABASE_URL')}
if not DATABASES['default']:
    raise RuntimeError(
        'Cannot start without a valid DB connection: {}'.format(DATABASES['default'])
    )

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": ''}}

# http://whitenoise.evans.io/en/stable/django.html#whitenoise-makes-my-tests-run-slow
WHITENOISE_AUTOREFRESH = True

# Disable manifest to prevent "Missing staticfiles manifest entry for ..."
# https://stackoverflow.com/a/51060143
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
