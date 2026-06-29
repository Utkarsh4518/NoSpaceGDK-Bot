"""Music streaming extension for NoSpaceFGK.

Contains the MusicCog which handles voice connection and audio playback using yt-dlp.
"""

import datetime
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands
from decorators.command_dec import guild_only_command, cooldown_command
from models.music import PlayerState
from services.music.music_service import MusicService
from ui.pagination import PaginationView
from utils.embeds import success_embed, error_embed, info_embed
from utils.helpers import format_duration

logger = logging.getLogger("NoSpaceFGK.music")


class MusicCog(commands.Cog, name="Music"):
    """Cog for music streaming and audio management commands."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the music cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot: commands.Bot = bot
        self.music_service: MusicService = bot.container.get(MusicService)
        logger.info("MusicCog initialized.")

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

    @app_commands.command(name="play", description="Play a song or playlist from YouTube or search text.")
    @app_commands.describe(query="A YouTube link, playlist link, or search keywords.")
    @guild_only_command()
    @cooldown_command(rate=1, per=3.0)
    async def play(self, interaction: discord.Interaction, query: str) -> None:
        """Play command querying YouTube or parsing URLs."""
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

        is_playlist = "list=" in query
        try:
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
                embed.add_field(name="Duration", value=format_duration(track.duration), inline=True)
                embed.add_field(name="Uploader", value=track.artist, inline=True)
                if track.thumbnail:
                    embed.set_thumbnail(url=track.thumbnail)
                await interaction.followup.send(embed=embed)

            if player.state in (PlayerState.IDLE, PlayerState.STOPPED):
                await player.play()
        except Exception as e:
            logger.error(f"Play command error: {e}", exc_info=True)
            await interaction.followup.send(
                embed=error_embed("Playback Error", f"An error occurred while loading audio: {e}")
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
