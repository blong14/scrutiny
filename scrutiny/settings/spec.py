from .dev import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEBUG = True

DEPLOY_ENV = "test"

LOGGING = {}

MERCURE_URL = ""
SSE = False
