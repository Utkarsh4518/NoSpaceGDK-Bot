"""Fun Repository for caching entertainment content and logging command usage."""

import datetime
from typing import List, Optional
from models.fun import CachedMeme, CachedJoke, CachedQuote, CachedFact
from repositories.base_repository import BaseRepository

class FunRepository(BaseRepository):
    """Handles persistence and retrieval of cached fun content & analytics."""

    # MEMES
    async def get_cached_meme(self, category: str) -> Optional[CachedMeme]:
        query = """
            SELECT id, category, title, url, post_link, subreddit, nsfw, cached_at
            FROM memes_cache
            WHERE category = ?
            ORDER BY RANDOM() LIMIT 1;
        """
        async with self.db.connection.execute(query, (category,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return CachedMeme(
                id=row[0], category=row[1], title=row[2], url=row[3],
                post_link=row[4], subreddit=row[5], nsfw=bool(row[6]),
                cached_at=datetime.datetime.fromisoformat(row[7])
            )

    async def save_meme(self, category: str, title: Optional[str], url: str, post_link: Optional[str], subreddit: Optional[str], nsfw: bool) -> None:
        query = """
            INSERT INTO memes_cache (category, title, url, post_link, subreddit, nsfw)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        await self.db.execute(query, (category, title, url, post_link, subreddit, int(nsfw)))
        await self.db.commit()

    # JOKES
    async def get_cached_joke(self, category: str) -> Optional[CachedJoke]:
        query = """
            SELECT id, category, setup, delivery, cached_at
            FROM jokes_cache
            WHERE category = ?
            ORDER BY RANDOM() LIMIT 1;
        """
        async with self.db.connection.execute(query, (category,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return CachedJoke(
                id=row[0], category=row[1], setup=row[2], delivery=row[3],
                cached_at=datetime.datetime.fromisoformat(row[4])
            )

    async def save_joke(self, category: str, setup: str, delivery: Optional[str]) -> None:
        query = """
            INSERT INTO jokes_cache (category, setup, delivery)
            VALUES (?, ?, ?);
        """
        await self.db.execute(query, (category, setup, delivery))
        await self.db.commit()

    # QUOTES
    async def get_cached_quote(self, category: str) -> Optional[CachedQuote]:
        query = """
            SELECT id, category, content, author, cached_at
            FROM quotes_cache
            WHERE category = ?
            ORDER BY RANDOM() LIMIT 1;
        """
        async with self.db.connection.execute(query, (category,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return CachedQuote(
                id=row[0], category=row[1], content=row[2], author=row[3],
                cached_at=datetime.datetime.fromisoformat(row[4])
            )

    async def save_quote(self, category: str, content: str, author: Optional[str]) -> None:
        query = """
            INSERT INTO quotes_cache (category, content, author)
            VALUES (?, ?, ?);
        """
        await self.db.execute(query, (category, content, author))
        await self.db.commit()

    # FACTS
    async def get_cached_fact(self) -> Optional[CachedFact]:
        query = """
            SELECT id, content, cached_at
            FROM facts_cache
            ORDER BY RANDOM() LIMIT 1;
        """
        async with self.db.connection.execute(query) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return CachedFact(
                id=row[0], content=row[1],
                cached_at=datetime.datetime.fromisoformat(row[2])
            )

    async def save_fact(self, content: str) -> None:
        query = """
            INSERT INTO facts_cache (content)
            VALUES (?);
        """
        await self.db.execute(query, (content,))
        await self.db.commit()

    # ANALYTICS
    async def log_fun_usage(self, guild_id: Optional[int], user_id: int, command_name: str) -> None:
        query = """
            INSERT INTO fun_usage (guild_id, user_id, command_name)
            VALUES (?, ?, ?);
        """
        await self.db.execute(query, (guild_id, user_id, command_name))
        await self.db.commit()
