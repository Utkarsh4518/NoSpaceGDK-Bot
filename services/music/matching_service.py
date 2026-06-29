"""YouTube matching service for Spotify tracks.

Matches Spotify track metadata against YouTube search results using
fuzzy string similarity, duration comparison, and uploader quality signals
to find the highest-confidence audio equivalent.
"""

import asyncio
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional

from models.music import Track
from providers.youtube_provider import YouTubeProvider
from repositories.spotify_cache_repo import SpotifyCacheRepository
from utils.logger import logger


@dataclass
class MatchResult:
    """Encapsulates a YouTube match result and its confidence score."""
    track: Track
    confidence: float
    match_reasons: List[str]


class MatchingService:
    """Ranks YouTube search results against Spotify metadata to find
    the best playable audio match.

    Scoring Criteria:
        - Title similarity:      40% weight
        - Artist similarity:     30% weight
        - Duration delta:        20% weight
        - Uploader quality:      10% weight (VEVO, Topic, verified)
    """

    # Weight constants
    TITLE_WEIGHT = 0.40
    ARTIST_WEIGHT = 0.30
    DURATION_WEIGHT = 0.20
    UPLOADER_WEIGHT = 0.10

    # Duration tolerance in seconds before penalising
    DURATION_TOLERANCE = 10.0
    # Maximum duration difference before zero score
    DURATION_MAX_DELTA = 60.0

    # Minimum confidence threshold to accept a match
    MIN_CONFIDENCE = 0.35

    # Known quality uploader patterns
    QUALITY_PATTERNS = [
        re.compile(r'VEVO$', re.IGNORECASE),
        re.compile(r'- Topic$', re.IGNORECASE),
        re.compile(r'Official', re.IGNORECASE),
    ]

    def __init__(
        self,
        youtube_provider: YouTubeProvider,
        spotify_cache_repo: Optional[SpotifyCacheRepository] = None
    ) -> None:
        """Initialize the matching service.

        Args:
            youtube_provider: YouTube provider for searching.
            spotify_cache_repo: Optional cache repository for resolved matches.
        """
        self._youtube = youtube_provider
        self._cache_repo = spotify_cache_repo

    async def find_match(self, spotify_track: Track) -> Optional[MatchResult]:
        """Find the best YouTube match for a Spotify track.

        Checks the database cache first. If no cached match exists,
        performs a YouTube search and scores candidates.

        Args:
            spotify_track: Spotify Track metadata model.

        Returns:
            MatchResult with the best YouTube track and confidence, or None.
        """
        spotify_id = spotify_track.metadata.get("spotify_id", "")

        # 1. Check cache
        if self._cache_repo and spotify_id:
            cached = await self._cache_repo.get_match(spotify_id)
            if cached:
                logger.info(
                    f"Matching service: Cache hit for Spotify ID '{spotify_id}' "
                    f"-> '{cached.youtube_url}' (confidence: {cached.confidence:.2f})."
                )
                # Resolve the cached YouTube URL to a full Track
                yt_track = await self._youtube.get_track(cached.youtube_url)
                if yt_track:
                    return MatchResult(
                        track=yt_track,
                        confidence=cached.confidence,
                        match_reasons=["cached_match"]
                    )

        # 2. Build search query
        search_query = self._build_search_query(spotify_track)
        logger.info(f"Matching service: Searching YouTube for '{search_query}'.")

        # 3. Search YouTube
        candidates = await self._youtube.search(search_query, limit=5)
        if not candidates:
            logger.warning(
                f"Matching service: No YouTube results for '{search_query}'."
            )
            return None

        # 4. Score and rank candidates
        best_match = self._rank_candidates(spotify_track, candidates)

        if not best_match:
            logger.warning(
                f"Matching service: No match above threshold for "
                f"'{spotify_track.artist} - {spotify_track.title}'."
            )
            return None

        # 5. Cache the result
        if self._cache_repo and spotify_id:
            await self._cache_repo.save_match(
                spotify_id=spotify_id,
                youtube_url=best_match.track.url,
                track_title=spotify_track.title,
                artist=spotify_track.artist,
                confidence=best_match.confidence
            )

        logger.info(
            f"Matching service: Matched '{spotify_track.title}' -> "
            f"'{best_match.track.title}' (confidence: {best_match.confidence:.2f}, "
            f"reasons: {best_match.match_reasons})."
        )

        return best_match

    def _build_search_query(self, track: Track) -> str:
        """Build an optimized YouTube search query from Spotify metadata.

        Args:
            track: Spotify Track metadata.

        Returns:
            Search query string.
        """
        title = track.title
        artist = track.artist

        # Remove common suffixes that hurt search precision
        title = re.sub(r'\s*\(feat\..*?\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\[.*?\]', '', title)
        title = re.sub(r'\s*-\s*Remastered.*$', '', title, flags=re.IGNORECASE)

        return f"{artist} {title}"

    def _rank_candidates(
        self,
        spotify_track: Track,
        candidates: List[Track]
    ) -> Optional[MatchResult]:
        """Score all YouTube candidates and return the best match.

        Args:
            spotify_track: Original Spotify Track metadata.
            candidates: List of YouTube Track search results.

        Returns:
            Best MatchResult above the minimum threshold, or None.
        """
        best: Optional[MatchResult] = None

        for candidate in candidates:
            score, reasons = self._score_candidate(spotify_track, candidate)

            if score >= self.MIN_CONFIDENCE:
                if best is None or score > best.confidence:
                    best = MatchResult(
                        track=candidate,
                        confidence=round(score, 4),
                        match_reasons=reasons
                    )

        return best

    def _score_candidate(
        self,
        spotify: Track,
        youtube: Track
    ) -> tuple[float, List[str]]:
        """Compute weighted similarity score between Spotify and YouTube tracks.

        Args:
            spotify: Spotify metadata track.
            youtube: YouTube candidate track.

        Returns:
            Tuple of (score, list_of_match_reasons).
        """
        reasons: List[str] = []

        # --- Title Similarity ---
        title_score = self._string_similarity(
            self._normalize(spotify.title),
            self._normalize(youtube.title)
        )
        reasons.append(f"title:{title_score:.2f}")

        # --- Artist Similarity ---
        artist_score = self._string_similarity(
            self._normalize(spotify.artist),
            self._normalize(youtube.artist)
        )
        reasons.append(f"artist:{artist_score:.2f}")

        # --- Duration Delta ---
        duration_score = self._duration_score(spotify.duration, youtube.duration)
        reasons.append(f"duration:{duration_score:.2f}")

        # --- Uploader Quality ---
        uploader_score = self._uploader_quality_score(youtube.artist)
        reasons.append(f"uploader:{uploader_score:.2f}")

        # Weighted combination
        total = (
            title_score * self.TITLE_WEIGHT
            + artist_score * self.ARTIST_WEIGHT
            + duration_score * self.DURATION_WEIGHT
            + uploader_score * self.UPLOADER_WEIGHT
        )

        return total, reasons

    def _duration_score(self, spotify_dur: float, youtube_dur: float) -> float:
        """Score duration similarity.

        Args:
            spotify_dur: Spotify track duration in seconds.
            youtube_dur: YouTube track duration in seconds.

        Returns:
            Score from 0.0 to 1.0.
        """
        if spotify_dur <= 0 or youtube_dur <= 0:
            return 0.5  # Unknown duration, give neutral score

        delta = abs(spotify_dur - youtube_dur)

        if delta <= self.DURATION_TOLERANCE:
            return 1.0

        if delta >= self.DURATION_MAX_DELTA:
            return 0.0

        # Linear decay between tolerance and max
        return 1.0 - (delta - self.DURATION_TOLERANCE) / (self.DURATION_MAX_DELTA - self.DURATION_TOLERANCE)

    def _uploader_quality_score(self, uploader: str) -> float:
        """Score uploader credibility.

        Args:
            uploader: YouTube uploader/channel name.

        Returns:
            Score from 0.0 to 1.0.
        """
        for pattern in self.QUALITY_PATTERNS:
            if pattern.search(uploader):
                return 1.0
        return 0.3  # Unknown uploader gets a low baseline

    @staticmethod
    def _string_similarity(a: str, b: str) -> float:
        """Calculate fuzzy string similarity using SequenceMatcher.

        Args:
            a: First string.
            b: Second string.

        Returns:
            Ratio from 0.0 to 1.0.
        """
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize a string for comparison by lowercasing and
        stripping non-alphanumeric characters.

        Args:
            text: Input string.

        Returns:
            Normalized string.
        """
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
