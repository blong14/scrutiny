import requests
from django import forms

from library.models import Article
from scrutiny.env import get_pocket_consumer_key


class NewsItemForm(forms.Form):
    feed_id = forms.CharField()
    title = forms.CharField()
    url = forms.URLField()

    def feed(self) -> str:
        return self.cleaned_data["feed_id"]

    def save_item(self, usr):
        url = self.cleaned_data["url"]
        resp = requests.post(
            "https://getpocket.com/v3/add",
            json={
                "consumer_key": get_pocket_consumer_key(),
                "access_token": usr.social_auth.first().extra_data.get(
                    "access_token", ""
                ),
                "title": self.selected_title(),
                "url": url,
            },
        )
        resp.raise_for_status()
        item = resp.json().get("item")
        Article(
            id=int(item.get("item_id")),
            authors=item.get("authors", {}),
            excerpt=item.get("excerpt"),
            user=usr,
            listen_duration_estimate=0,
            resolved_title=item.get("title"),
        ).save()

    def selected_title(self) -> str:
        return self.cleaned_data["title"]
