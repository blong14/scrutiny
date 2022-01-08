from opentelemetry import trace

from features.views import FeatureListView


tracer = trace.get_tracer(__name__)


class FeatureMiddleware:
    module = "features.middleware.FeatureMiddleware"

    def __init__(self, get_response):
        self.get_response = get_response
        self.view = FeatureListView

    def __call__(self, request):
        with tracer.start_as_current_span(f"{self.module}.__call__"):
            view = self.view()
            view.setup(request=request)
            features = view.get_context_data()
            request.features = features.get("features", {})
            response = self.get_response(request)
            return response
