from .dev import *  # noqa

ALLOWED_HOSTS = ["*"]

DEBUG = False

DEPLOY_ENV = "prod"

DATABASES = {
    "default": {
        "ENGINE": "django_cockroachdb",
        "NAME": "app",
        "USER": "root",
        "PASSWORD": "",
        "HOST": "cockroachdb-public",
        "PORT": "26257",
        # If connecting with SSL, include the section below, replacing the
        # file paths as appropriate.
        "OPTIONS": {
            "sslmode": "verify-full",
            "sslrootcert": "/certs/ca.crt",
            # Either sslcert and sslkey (below) or PASSWORD (above) is
            # required.
            "sslcert": "/certs/client.root.crt",
            "sslkey": "/certs/client.root.key",
        },
    }
}

# turns server side events on
MERCURE_URL = "https://scrutiny.local/.well-known/mercure"
SSE = True
