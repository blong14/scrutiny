from .dev import *  # noqa

ALLOWED_HOSTS = ["*"]

DEBUG = False

DEPLOY_ENV = "prod"

# DATABASES = {
#     "default": {
#         "ENGINE": "django_cockroachdb",
#         "NAME": "app",
#         "USER": "root",
#         "PASSWORD": "",
#         "HOST": "cockroachdb-public",
#         "PORT": "26257",
#         # If connecting with SSL, include the section below, replacing the
#         # file paths as appropriate.
#         "OPTIONS": {
#             "sslmode": "verify-full",
#             "sslrootcert": "/certs/ca.crt",
#             # Either sslcert and sslkey (below) or PASSWORD (above) is
#             # required.
#             "sslcert": "/certs/client.root.crt",
#             "sslkey": "/certs/client.root.key",
#         },
#     }
# }
# DATABASES = {
#     "default": {
#         "ENGINE": "django_cockroachdb",
#         "NAME": "app",
#         "USER": "root",
#         "PASSWORD": "",
#         "HOST": "cockroachdb-public",
#         "PORT": "26257",
#     },
# }
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("PG_DATABASE", ""),
        "USER": os.getenv("PG_USER", ""),
        "PASSWORD": os.getenv("PG_PASSWORD", ""),
        "HOST": os.getenv("PG_HOST", ""),
        "PORT": os.getenv("PG_PORT", "5432"),
    }
}


# turns server side events on
MERCURE_URL = "http://mercure.default.svc.cluster.local/.well-known/mercure"
SSE = True
