from django.conf import settings


def get_pocket_consumer_key() -> str:
    return getattr(settings, "SOCIAL_AUTH_POCKET_KEY", "")


def get_mercure_token() -> str:
    return getattr(settings, "JWT_PUBLISH_TOKEN", "")


def get_mercure_url() -> str:
    return getattr(settings, "MERCURE_URL", "")
