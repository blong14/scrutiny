from django import forms


class NewsItemForm(forms.Form):
    feed_id = forms.CharField()
    title = forms.CharField()
    url = forms.URLField()

    def get_url(self) -> str:
        return self.cleaned_data["url"]

    def feed(self) -> str:
        return self.cleaned_data["feed_id"]

    def selected_title(self) -> str:
        return self.cleaned_data["title"]
