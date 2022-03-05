from collections.abc import KeysView
from typing import Any, Callable, Dict, List, Optional

import feedparser as default_parser
from pydantic import AnyHttpUrl
from pydantic.dataclasses import dataclass


Parser = Callable[[str], Any]


@dataclass(frozen=True)
class Feed:
    id: str
    title: str
    url: AnyHttpUrl


_active_feeds: Dict[str, Feed] = {}


class FeedRegistry:
    @staticmethod
    def get(feed: str) -> Optional[Feed]:
        return _active_feeds.get(feed)

    @staticmethod
    def titles() -> KeysView:
        return _active_feeds.keys()

    @staticmethod
    def register_feed(feed: str):
        def wrapper(f: Feed):
            _active_feeds[feed] = f
            return f

        return wrapper


@FeedRegistry.register_feed("hackernews")
class HackerNewsFeed(Feed):
    id: str = "hackernews"
    title: str = "Hacker News"
    url: AnyHttpUrl = "https://hnrss.org/frontpage"


@FeedRegistry.register_feed("slashdot")
class SlashDotFeed(Feed):
    id: str = "slashdot"
    title: str = "SlashDot"
    url: AnyHttpUrl = "http://rss.slashdot.org/Slashdot/slashdotDevelopers"  # noqa


@FeedRegistry.register_feed("nautilus")
class NautilusFeed(Feed):
    id: str = "nautilus"
    title: str = "Nautilus"
    url: AnyHttpUrl = "https://nautil.us/feed"


@FeedRegistry.register_feed("bbcnews")  # noqa
class BBCNewsFeed(Feed):
    id: str = "bbcnews"  # noqa
    title: str = "BBC News"
    url: AnyHttpUrl = "https://feeds.bbci.co.uk/news/rss.xml"


@FeedRegistry.register_feed("nature")
class NatureFeed(Feed):
    id: str = "nature"
    title: str = "Nature"
    url: AnyHttpUrl = "http://feeds.nature.com/nature/rss/current"  # noqa


@dataclass(init=True)
class FeedResponse:
    entries: List[dict]


def parse_feed(
    context: dict, feed: Feed, parser: Parser = default_parser.parse, limit: int = 10
) -> dict:
    resp = FeedResponse(entries=getattr(parser(feed.url), "entries"))
    context |= {
        "id": feed.id,
        "title": feed.title,
        "items": resp.entries[0:limit],
    }
    return context
