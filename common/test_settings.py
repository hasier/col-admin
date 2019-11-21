from .settings import *

DATABASES = {'default': dj_database_url.config(conn_max_age=500, env='TEST_DATABASE_URL')}
if not DATABASES['default']:
    raise RuntimeError(
        'Cannot start without a valid DB connection: {}'.format(DATABASES['default'])
    )

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": '',
    }
}
