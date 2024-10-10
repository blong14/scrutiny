import os

from .local import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("PG_DATABASE", "scrutiny"),
        "USER": os.getenv("PG_USER", "pi"),
        "PASSWORD": os.getenv("PG_PASSWORD", "test"),
        "HOST": os.getenv("PG_HOST", "localhost"),
        "PORT": os.getenv("PG_PORT", "5432"),
    }
}
