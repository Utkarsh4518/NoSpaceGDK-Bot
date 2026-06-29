"""Music services package for NoSpaceFGK bot.

Exposes base player, managers, coordinators, and provider routing.
"""

from services.music.base_player import BaseMusicPlayer
from services.music.player_manager import PlayerManager
from services.music.queue_manager import QueueManager
from services.music.track_manager import TrackManager
from services.music.voice_manager import VoiceManager
from services.music.audio_manager import AudioManager
from services.music.provider_manager import ProviderManager
from services.music.music_service import MusicService
from services.music.matching_service import MatchingService
from services.music.metadata_service import MetadataService
from services.music.provider_router import ProviderRouter
