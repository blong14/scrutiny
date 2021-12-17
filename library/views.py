from library.models import Article
from scrutiny.views import ScrutinyListView


class PocketListView(ScrutinyListView):
    model = Article
    template_name = "library/list.html"
