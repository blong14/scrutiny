def page_id(request):
    return {"page_id": request.resolver_match.view_name}
