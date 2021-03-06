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

DATABASES = {
    "default": {
        "ENGINE": "django_cockroachdb",
        "NAME": "app",
        "USER": "root",
        "PASSWORD": "",
        "HOST": "cockroachdb-public",
        "PORT": "26257",
    },
}
# turns server side events on
MERCURE_URL = "http://scrutiny-caddy.default.svc.cluster.local:8443/.well-known/mercure"
SSE = True
TRACE_ENABLED = True
