from .local import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "scrutiny",
        "USER": "pi",
        "PASSWORD": "test",
        "HOST": "postgres",
        "PORT": "5432",
    }
}
