from django.forms import ModelForm

from .models import NewsItem


class NewsItemForm(ModelForm):
    class Meta:
        model = NewsItem
        fields = ["feed_id", "title", "url"]

    def get_url(self) -> str:
        return self.cleaned_data["url"]

    def feed(self) -> str:
        return self.cleaned_data["feed_id"]

    def selected_title(self) -> str:
        return self.cleaned_data["title"]
