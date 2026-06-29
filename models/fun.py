"""Fun System cached items domain models."""

import datetime
from dataclasses import dataclass

@dataclass
class CachedMeme:
    id: int | None
    category: str
    title: str | None
    url: str
    post_link: str | None
    subreddit: str | None
    nsfw: bool
    cached_at: datetime.datetime

@dataclass
class CachedJoke:
    id: int | None
    category: str
    setup: str
    delivery: str | None
    cached_at: datetime.datetime

@dataclass
class CachedQuote:
    id: int | None
    category: str
    content: str
    author: str | None
    cached_at: datetime.datetime

@dataclass
class CachedFact:
    id: int | None
    content: str
    cached_at: datetime.datetime
