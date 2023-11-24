from django.conf import settings


def get_graft_api_key() -> str:
    return getattr(settings, "GRAFT_API_KEY", "")


def get_pocket_consumer_key() -> str:
    return getattr(settings, "SOCIAL_AUTH_POCKET_KEY", "")


def get_mercure_pub_token() -> str:
    return getattr(settings, "JWT_PUBLISH_TOKEN", "")


def get_mercure_sub_token() -> str:
    return getattr(settings, "JWT_SUBSCRIBE_TOKEN", "")


def get_mercure_url() -> str:
    return getattr(
        settings, "MERCURE_URL", "http://mercure.cluster/.well-known/mercure"
    )


def get_mercure_svc_url() -> str:
    return getattr(
        settings, "MERCURE_SVC_URL", "http://mercure.cluster/.well-known/mercure"
    )


def get_ollama_url() -> str:
    return getattr(settings, "OLLAMA_URL", "http://ollama.cluster")


def get_ollama_svc_url() -> str:
    return getattr(settings, "OLLAMA_SVC_URL", "http://ollama.cluster")


def should_trace() -> bool:
    return getattr(settings, "TRACE_ENABLED", False)


def sse() -> bool:
    return getattr(settings, "SSE", False)
