from scrutiny.env import (
    get_mercure_sub_token,
    get_mercure_url,
)


mercure_url = get_mercure_url()
mercure_token = get_mercure_sub_token()


def page_id(request):
    return {"page_id": request.resolver_match.view_name}


def news_summary_subscription(_):
    return {"topic": f"{mercure_url}?topic=news-summary&authorization={mercure_token}"}
