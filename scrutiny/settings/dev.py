"""
Django settings for scrutiny project.

Generated by 'django-admin startproject' using Django 3.2.9.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path

import jwt

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-o50c8m6efvnof!0t2w9b+!nn!)j7rsy9+)7citgwpo7e&#o2lw"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DEPLOY_ENV = "dev"

ALLOWED_HOSTS = [
    "localhost",
    "scrutiny.cluster",
    "scrutiny.local",
    "scrutiny-varnish",
    "web",
    "web:8080",
    "web1",
    "web1:8080",
    "web2",
    "web2:8080",
]


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "social_django",
    "rest_framework",
    "features",
    "jobs",
    "library",
    "news",
    "notes",
    "wsgi",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    #     "requestlogs.middleware.RequestLogsMiddleware",
    "features.middleware.FeatureMiddleware",
]

ROOT_URLCONF = "scrutiny.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "scrutiny.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "scrutiny",
        "HOST": os.getenv("PG_HOST", "localhost"),
        "USER": os.getenv("PG_USER", "admin"),
        "PASSWORD": os.getenv("PG_PASSWORD", "!Changeme!"),
        "PORT": os.getenv("PG_PORT", "54321"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = f"{BASE_DIR}/static"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "True"

JWT_PUBLISH_TOKEN = jwt.encode(
    payload={"mercure": {"publish": ["*"]}}, key=os.getenv("JWT_KEY", "!ChangeMe!")
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

REST_FRAMEWORK = {
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 500,
}

MERCURE_URL = ""
SSE = False


AUTHENTICATION_BACKENDS = (
    "social_core.backends.pocket.PocketAuth",
    "django.contrib.auth.backends.ModelBackend",
)

LOGIN_URL = "/login/"
LOGOUT_REDIRECT_URL = "/"

SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/library"
SOCIAL_AUTH_POCKET_KEY = "100485-6d330864127985d949177b3"
