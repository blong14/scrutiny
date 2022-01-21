from django.conf import settings


def get_pocket_consumer_key() -> str:
    return getattr(settings, "SOCIAL_AUTH_POCKET_KEY", "")
