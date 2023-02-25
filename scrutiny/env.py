from django.conf import settings


def get_graft_api_key() -> str:
    return getattr(settings, "GRAFT_API_KEY", "")


def get_pocket_consumer_key() -> str:
    return getattr(settings, "SOCIAL_AUTH_POCKET_KEY", "")


def get_mercure_token() -> str:
    return getattr(settings, "JWT_PUBLISH_TOKEN", "")


def get_mercure_url() -> str:
    return getattr(
        settings, "MERCURE_URL", "https://scrutiny.local:8089/.well-known/mercure"
    )


def should_trace() -> bool:
    return getattr(settings, "TRACE_ENABLED", False)


def sse() -> bool:
    return getattr(settings, "SSE", False)
