from features.views import FeatureListView


class FeatureMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.view = FeatureListView

    def __call__(self, request):
        view = self.view()
        view.setup(request=request)
        features = view.get_context_data()
        request.features = features.get("features", {})
        response = self.get_response(request)
        return response
