"""Music streaming extension for NoSpaceFGK.

Contains the MusicCog which handles voice connection and audio playback,
with support for YouTube and Spotify (resolved through YouTube matching).
"""

import asyncio
import datetime
import logging
from typing import List, Optional
import discord
from discord import app_commands
from discord.ext import commands
from decorators.command_dec import guild_only_command, cooldown_command
from models.music import PlayerState, Track
from services.music.music_service import MusicService
from services.music.matching_service import MatchingService
from services.music.metadata_service import MetadataService
from services.music.provider_router import ProviderRouter, ProviderType
from repositories.spotify_import_repo import SpotifyImportRepository
from ui.pagination import PaginationView
from utils.embeds import success_embed, error_embed, info_embed
from utils.helpers import format_duration

logger = logging.getLogger("NoSpaceFGK.music")


class MusicCog(commands.Cog, name="Music"):
    """Cog for music streaming and audio management commands.

    Supports YouTube and Spotify URLs. Spotify tracks are resolved
    to YouTube audio streams via the MatchingService.
    """

    # Provider icon URLs for embed display
    PROVIDER_ICONS = {
        "youtube": "https://cdn-icons-png.flaticon.com/512/1384/1384060.png",
        "spotify": "https://cdn-icons-png.flaticon.com/512/2111/2111624.png",
    }

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the music cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot: commands.Bot = bot
        self.music_service: MusicService = bot.container.get(MusicService)
        self.router: ProviderRouter = bot.container.get(ProviderRouter)
        self.matching: MatchingService = bot.container.get(MatchingService)
        self.metadata: MetadataService = bot.container.get(MetadataService)
        self.import_repo: SpotifyImportRepository = bot.container.get(SpotifyImportRepository)
        logger.info("MusicCog initialized (Spotify: %s).", "enabled" if self.router.spotify_enabled else "disabled")

    @app_commands.command(name="join", description="Join your active voice channel.")
    @guild_only_command()
    async def join(self, interaction: discord.Interaction) -> None:
        """Connect the bot to the user's voice channel."""
        user_voice = interaction.user.voice
        if not user_voice or not user_voice.channel:
            await interaction.response.send_message(
                embed=error_embed("Voice Connection", "You must be connected to a voice channel to use this command."),
                ephemeral=True
            )
            return

        player = await self.music_service.get_player(interaction.guild_id)
        try:
            await player.voice.join_channel(user_voice.channel)
            await interaction.response.send_message(
                embed=success_embed("Voice Connection", f"Successfully connected to **{user_voice.channel.name}**.")
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=error_embed("Voice Connection Error", str(e)),
                ephemeral=True
            )

    @app_commands.command(name="leave", description="Disconnect from the voice channel.")
    @guild_only_command()
    async def leave(self, interaction: discord.Interaction) -> None:
        """Disconnect the bot from its active voice channel."""
        player = await self.music_service.get_player(interaction.guild_id)
        if not player.voice.is_connected:
            await interaction.response.send_message(
                embed=error_embed("Voice Disconnection", "I am not connected to any voice channels in this server."),
                ephemeral=True
            )
            return

        await player.destroy()
        await interaction.response.send_message(
            embed=success_embed("Voice Disconnection", "Successfully disconnected and cleared guild player session.")
        )

    @app_commands.command(name="play", description="Play a song or playlist from YouTube, Spotify, or search text.")
    @app_commands.describe(query="A YouTube/Spotify link, playlist, album, artist, or search keywords.")
    @guild_only_command()
    @cooldown_command(rate=1, per=3.0)
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        """Universal play command supporting YouTube and Spotify."""
        user_voice = interaction.user.voice
        if not user_voice or not user_voice.channel:
            await interaction.response.send_message(
                embed=error_embed("Playback Error", "You must be connected to a voice channel to play music."),
                ephemeral=True
            )
            return

        await interaction.response.defer()
        player = await self.music_service.get_player(interaction.guild_id)

        if not player.voice.is_connected:
            try:
                await player.voice.join_channel(user_voice.channel)
            except Exception as e:
                await interaction.followup.send(
                    embed=error_embed("Voice Connection Error", f"Failed to join voice channel: {e}")
                )
                return

        # Route query to the correct provider
        provider_type = self.router.detect(query)

        try:
            if provider_type == ProviderType.SPOTIFY:
                await self._handle_spotify(interaction, player, query)
            elif provider_type == ProviderType.SOUNDCLOUD:
                await interaction.followup.send(
                    embed=error_embed("Provider Unavailable", "SoundCloud playback is not yet supported.")
                )
            elif provider_type == ProviderType.UNKNOWN:
                await interaction.followup.send(
                    embed=error_embed("Unknown URL", "This URL is not recognized as a supported music provider.")
                )
            else:
                # YouTube URL or plain search
                await self._handle_youtube(interaction, player, query)
        except Exception as e:
            logger.error(f"Play command error: {e}", exc_info=True)
            await interaction.followup.send(
                embed=error_embed("Playback Error", f"An error occurred while loading audio: {e}")
            )

    async def _handle_youtube(self, interaction: discord.Interaction, player, query: str) -> None:
        """Handle YouTube URLs and plain text search queries."""
        is_playlist = "list=" in query

        if is_playlist:
            provider = self.music_service.providers.resolve_provider_by_url(query)
            if not provider:
                provider = self.music_service.providers.get_provider("youtube")

            playlist = await provider.get_playlist(query)
            if not playlist or not playlist.tracks:
                await interaction.followup.send(
                    embed=error_embed("Resolution Failed", "Failed to retrieve playlist details or playlist is empty.")
                )
                return

            for track in playlist.tracks:
                track.requested_by = interaction.user.id
                await player.queue.add_track(track, interaction.user.id)

            embed = success_embed(
                "Playlist Added 🎶",
                f"Added **{len(playlist.tracks)}** tracks from playlist **{playlist.name}** to the queue."
            )
            embed.set_author(name="YouTube", icon_url=self.PROVIDER_ICONS["youtube"])
            if playlist.tracks[0].thumbnail:
                embed.set_thumbnail(url=playlist.tracks[0].thumbnail)
            await interaction.followup.send(embed=embed)
        else:
            results = await self.music_service.search(query, provider_name="youtube")
            if not results:
                await interaction.followup.send(
                    embed=error_embed("No Results", f"Could not find any results matching '{query}'.")
                )
                return

            track = results[0]
            track.requested_by = interaction.user.id
            await player.queue.add_track(track, interaction.user.id)

            embed = success_embed(
                "Track Added 🎵",
                f"Added [**{track.title}**]({track.url}) to the queue."
            )
            embed.set_author(name="YouTube", icon_url=self.PROVIDER_ICONS["youtube"])
            embed.add_field(name="Duration", value=format_duration(track.duration), inline=True)
            embed.add_field(name="Uploader", value=track.artist, inline=True)
            if track.thumbnail:
                embed.set_thumbnail(url=track.thumbnail)
            await interaction.followup.send(embed=embed)

        if player.state in (PlayerState.IDLE, PlayerState.STOPPED):
            await player.play()

    async def _handle_spotify(self, interaction: discord.Interaction, player, query: str) -> None:
        """Handle Spotify URLs: track, album, playlist, and artist."""
        spotify = self.router.spotify_provider
        if not spotify:
            await interaction.followup.send(
                embed=error_embed(
                    "Spotify Disabled",
                    "Spotify integration is not configured. Ask the bot administrator to set "
                    "`SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in the `.env` file."
                )
            )
            return

        parsed = spotify.parse_spotify_identifier(query)
        if not parsed:
            await interaction.followup.send(
                embed=error_embed("Invalid Spotify URL", "Could not parse the Spotify URL or URI.")
            )
            return

        spotify_type = parsed["type"]

        if spotify_type == "track":
            await self._spotify_track(interaction, player, query)
        elif spotify_type == "playlist":
            await self._spotify_collection(interaction, player, query, "playlist")
        elif spotify_type == "album":
            await self._spotify_collection(interaction, player, query, "album")
        elif spotify_type == "artist":
            await self._spotify_collection(interaction, player, query, "artist")
        else:
            await interaction.followup.send(
                embed=error_embed("Unsupported Spotify Type", f"Spotify resource type '{spotify_type}' is not supported.")
            )

    async def _spotify_track(self, interaction: discord.Interaction, player, url: str) -> None:
        """Resolve and queue a single Spotify track via YouTube matching."""
        spotify = self.router.spotify_provider
        spotify_track = await spotify.get_track(url)
        if not spotify_track:
            await interaction.followup.send(
                embed=error_embed("Resolution Failed", "Failed to retrieve Spotify track metadata.")
            )
            return

        match_result = await self.matching.find_match(spotify_track)
        if not match_result:
            await interaction.followup.send(
                embed=error_embed(
                    "No YouTube Match",
                    f"Could not find a YouTube match for **{spotify_track.artist} - {spotify_track.title}**."
                )
            )
            return

        yt_track = match_result.track
        yt_track.requested_by = interaction.user.id
        await player.queue.add_track(yt_track, interaction.user.id)

        embed = success_embed(
            "Spotify Track Added 🎵",
            f"Added [**{spotify_track.title}**]({spotify_track.url}) to the queue."
        )
        embed.set_author(name="Spotify → YouTube", icon_url=self.PROVIDER_ICONS["spotify"])
        embed.add_field(name="Artist", value=spotify_track.artist, inline=True)
        embed.add_field(name="Duration", value=format_duration(spotify_track.duration), inline=True)
        embed.add_field(name="Match Confidence", value=f"{match_result.confidence:.0%}", inline=True)
        embed.add_field(name="YouTube Source", value=f"[{yt_track.title}]({yt_track.url})", inline=False)
        if spotify_track.thumbnail:
            embed.set_thumbnail(url=spotify_track.thumbnail)
        await interaction.followup.send(embed=embed)

        # Log import
        await self.import_repo.log_import(
            spotify_url=url,
            spotify_type="track",
            track_count=1,
            imported_by=interaction.user.id,
            guild_id=interaction.guild_id
        )

        if player.state in (PlayerState.IDLE, PlayerState.STOPPED):
            await player.play()

    async def _spotify_collection(self, interaction: discord.Interaction, player, url: str, collection_type: str) -> None:
        """Resolve and queue Spotify playlists, albums, or artist top tracks."""
        spotify = self.router.spotify_provider

        # Fetch metadata from Spotify
        spotify_tracks: Optional[List[Track]] = None
        collection_name = "Spotify Collection"

        if collection_type == "playlist":
            playlist = await spotify.get_playlist(url)
            if playlist:
                spotify_tracks = playlist.tracks
                collection_name = playlist.name
        elif collection_type == "album":
            spotify_tracks = await spotify.get_album(url)
            if spotify_tracks:
                collection_name = spotify_tracks[0].metadata.get("album_name", "Spotify Album")
        elif collection_type == "artist":
            spotify_tracks = await spotify.get_artist_top_tracks(url, limit=20)
            collection_name = "Top Tracks"

        if not spotify_tracks:
            await interaction.followup.send(
                embed=error_embed("Resolution Failed", f"Failed to retrieve Spotify {collection_type} metadata.")
            )
            return

        total = len(spotify_tracks)

        # Send initial progress embed
        progress_embed = info_embed(
            f"Importing Spotify {collection_type.capitalize()} 🎶",
            f"**{collection_name}**\n\nResolving tracks... `0/{total}`"
        )
        progress_embed.set_author(name="Spotify → YouTube", icon_url=self.PROVIDER_ICONS["spotify"])
        if spotify_tracks[0].thumbnail:
            progress_embed.set_thumbnail(url=spotify_tracks[0].thumbnail)
        msg = await interaction.followup.send(embed=progress_embed, wait=True)

        # Resolve tracks to YouTube
        resolved_count = 0
        failed_count = 0
        first_resolved = True

        for i, sp_track in enumerate(spotify_tracks):
            try:
                match_result = await self.matching.find_match(sp_track)
                if match_result:
                    yt_track = match_result.track
                    yt_track.requested_by = interaction.user.id
                    await player.queue.add_track(yt_track, interaction.user.id)
                    resolved_count += 1

                    # Start playback after first track resolves
                    if first_resolved and player.state in (PlayerState.IDLE, PlayerState.STOPPED):
                        await player.play()
                        first_resolved = False
                else:
                    failed_count += 1
                    logger.warning(f"Spotify import: No match for '{sp_track.artist} - {sp_track.title}'.")
            except Exception as e:
                failed_count += 1
                logger.error(f"Spotify import: Error matching track '{sp_track.title}': {e}")

            # Update progress every 5 tracks or on the last track
            if (i + 1) % 5 == 0 or (i + 1) == total:
                progress_embed.description = (
                    f"**{collection_name}**\n\n"
                    f"Resolving tracks... `{i + 1}/{total}`\n"
                    f"✅ Resolved: `{resolved_count}` | ❌ Failed: `{failed_count}`"
                )
                try:
                    await msg.edit(embed=progress_embed)
                except discord.HTTPException:
                    pass

        # Final summary embed
        summary_embed = success_embed(
            f"Spotify {collection_type.capitalize()} Imported 🎶",
            f"**{collection_name}**\n\n"
            f"✅ **{resolved_count}** tracks added to queue\n"
            f"❌ **{failed_count}** tracks could not be matched"
        )
        summary_embed.set_author(name="Spotify → YouTube", icon_url=self.PROVIDER_ICONS["spotify"])
        if spotify_tracks[0].thumbnail:
            summary_embed.set_thumbnail(url=spotify_tracks[0].thumbnail)
        try:
            await msg.edit(embed=summary_embed)
        except discord.HTTPException:
            pass

        # Log import
        await self.import_repo.log_import(
            spotify_url=url,
            spotify_type=collection_type,
            track_count=resolved_count,
            imported_by=interaction.user.id,
            guild_id=interaction.guild_id
        )

    @app_commands.command(name="pause", description="Pause playback of the current track.")
    @guild_only_command()
    async def pause(self, interaction: discord.Interaction) -> None:
        """Pause current music playback."""
        player = await self.music_service.get_player(interaction.guild_id)
        if player.state != PlayerState.PLAYING:
            await interaction.response.send_message(
                embed=error_embed("Playback Status", "No tracks are currently playing."),
                ephemeral=True
            )
            return

        await player.pause()
        await interaction.response.send_message(
            embed=success_embed("Playback Status", "Playback has been paused.")
        )

    @app_commands.command(name="resume", description="Resume paused playback.")
    @guild_only_command()
    async def resume(self, interaction: discord.Interaction) -> None:
        """Resume paused music playback."""
        player = await self.music_service.get_player(interaction.guild_id)
        if player.state != PlayerState.PAUSED:
            await interaction.response.send_message(
                embed=error_embed("Playback Status", "Music is not currently paused."),
                ephemeral=True
            )
            return

        await player.resume()
        await interaction.response.send_message(
            embed=success_embed("Playback Status", "Playback has been resumed.")
        )

    @app_commands.command(name="skip", description="Skip the currently playing track.")
    @guild_only_command()
    async def skip(self, interaction: discord.Interaction) -> None:
        """Skip current track."""
        player = await self.music_service.get_player(interaction.guild_id)
        if not player.current_track:
            await interaction.response.send_message(
                embed=error_embed("Playback Status", "There is no track currently playing to skip."),
                ephemeral=True
            )
            return

        title = player.current_track.track.title
        await player.skip()
        await interaction.response.send_message(
            embed=success_embed("Playback Status", f"Skipped **{title}**.")
        )

    @app_commands.command(name="stop", description="Stop music playback and clear the queue.")
    @guild_only_command()
    async def stop(self, interaction: discord.Interaction) -> None:
        """Stop music and clear current tracks."""
        player = await self.music_service.get_player(interaction.guild_id)
        if player.state == PlayerState.IDLE:
            await interaction.response.send_message(
                embed=error_embed("Playback Status", "Player is already stopped and idle."),
                ephemeral=True
            )
            return

        await player.stop()
        await player.queue.clear()
        await interaction.response.send_message(
            embed=success_embed("Playback Status", "Playback stopped and track queue cleared.")
        )

    @app_commands.command(name="volume", description="Get or adjust the playback volume level.")
    @app_commands.describe(level="New volume percentage (0 - 200).")
    @guild_only_command()
    async def volume(self, interaction: discord.Interaction, level: Optional[int] = None) -> None:
        """Get or modify volume setting."""
        player = await self.music_service.get_player(interaction.guild_id)
        current_pct = int(player.audio.volume * 100)

        if level is None:
            await interaction.response.send_message(
                embed=info_embed("Playback Volume", f"The current volume is set to **{current_pct}%**.")
            )
            return

        if not (0 <= level <= 200):
            await interaction.response.send_message(
                embed=error_embed("Playback Volume", "Volume level must be an integer between 0 and 200."),
                ephemeral=True
            )
            return

        player.audio.set_volume(level / 100)
        await interaction.response.send_message(
            embed=success_embed("Playback Volume", f"Volume adjusted from **{current_pct}%** to **{level}%**.")
        )

    @app_commands.command(name="nowplaying", description="Display full details about the track currently playing.")
    @guild_only_command()
    async def nowplaying(self, interaction: discord.Interaction) -> None:
        """Display details about the currently playing track."""
        player = await self.music_service.get_player(interaction.guild_id)
        current = player.current_track
        if not current:
            await interaction.response.send_message(
                embed=error_embed("Playback Status", "There are no tracks currently playing."),
                ephemeral=True
            )
            return

        track = current.track
        position = player.position
        duration = track.duration

        bar_length = 20
        progress = min(1.0, max(0.0, position / duration)) if duration > 0 else 0.0
        filled = int(progress * bar_length)
        bar = "".join(["▬" * filled, "🔘", "▬" * (bar_length - filled)])

        pos_str = format_duration(position)
        dur_str = format_duration(duration)

        embed = info_embed(
            "Now Playing 🎵",
            f"[**{track.title}**]({track.url})\n\n"
            f"`{pos_str}` [{bar}] `{dur_str}`\n\n"
            f"**Uploader**: `{track.artist}`\n"
            f"**Requested By**: <@{track.requested_by}>"
        )
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="queue", description="Display the list of upcoming tracks in the queue.")
    @guild_only_command()
    async def queue(self, interaction: discord.Interaction) -> None:
        """Display the upcoming queue with page controls."""
        player = await self.music_service.get_player(interaction.guild_id)
        upcoming = player.queue.queue

        if not upcoming and not player.current_track:
            await interaction.response.send_message(
                embed=info_embed("Playback Queue", "The queue is currently empty.")
            )
            return

        embeds = []
        page_size = 10
        chunks = [upcoming[i:i + page_size] for i in range(0, len(upcoming), page_size)] or [[]]

        total_duration = sum(t.track.duration for t in upcoming)
        if player.current_track:
            total_duration += player.current_track.track.duration

        for idx, chunk in enumerate(chunks):
            desc = []
            if idx == 0 and player.current_track:
                desc.append(f"**Now Playing:**\n[**{player.current_track.track.title}**]({player.current_track.track.url}) | `{format_duration(player.current_track.track.duration)}` (Requested by: <@{player.current_track.track.requested_by}>)\n")
                if chunk:
                    desc.append("**Up Next:**")

            for j, item in enumerate(chunk):
                pos = idx * page_size + j + 1
                desc.append(f"`{pos}.` [**{item.track.title}**]({item.track.url}) | `{format_duration(item.track.duration)}` (Requested by: <@{item.track.requested_by}>)")

            desc_text = "\n".join(desc) if desc else "No upcoming tracks."

            embed = info_embed(
                f"Playback Queue for {interaction.guild.name} 🎶",
                desc_text
            )
            embed.set_footer(
                text=f"Tracks: {len(upcoming) + (1 if player.current_track else 0)} | Total Duration: {format_duration(total_duration)} | Page {idx + 1}/{len(chunks)}"
            )
            embeds.append(embed)

        view = PaginationView(interaction.user.id, embeds)
        await interaction.response.send_message(embed=embeds[0], view=view)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot) -> None:
    """Load the MusicCog into the bot."""
    await bot.add_cog(MusicCog(bot))
