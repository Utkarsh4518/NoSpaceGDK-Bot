"""Lockdown Service for managing channel, category, and guild restrictions."""

import json
from typing import Any, Optional
import discord
from repositories.base_repository import BaseRepository
from services.base_service import BaseService
from utils.logger import logger

class LockdownService(BaseService):
    """Handles channel permissions lockouts and restorations."""

    def __init__(self, db: Any) -> None:
        self.db = db

    async def lock_channel(
        self,
        guild: discord.Guild,
        channel: discord.TextChannel | discord.VoiceChannel | discord.abc.GuildChannel,
        moderator: discord.Member | discord.User,
        reason: Optional[str] = None
    ) -> bool:
        """Lock a single channel by denying Send Messages / Connect to @everyone."""
        try:
            # 1. Capture original overwrites
            original_overwrites = {}
            for role_or_member, overwrite in channel.overwrites.items():
                original_overwrites[str(role_or_member.id)] = {
                    "type": "role" if isinstance(role_or_member, discord.Role) else "member",
                    "pair": overwrite.pair()  # returns (allow, deny) bitfield pairs
                }
                
            serialized_overwrites = json.dumps(original_overwrites)
            
            # 2. Modify overwrites for @everyone
            everyone_role = guild.default_role
            current_overwrite = channel.overwrites_for(everyone_role)
            
            if isinstance(channel, discord.TextChannel):
                current_overwrite.send_messages = False
                current_overwrite.add_reactions = False
            elif isinstance(channel, discord.VoiceChannel):
                current_overwrite.connect = False
                current_overwrite.speak = False
                
            await channel.set_permissions(everyone_role, overwrite=current_overwrite, reason=reason or "Lockdown activated")
            
            # 3. Store lock in DB
            query = """
                INSERT INTO locks (guild_id, target_id, target_type, moderator_id, original_overwrites, is_active)
                VALUES (?, ?, 'channel', ?, ?, 1);
            """
            await self.db.execute(query, (guild.id, channel.id, moderator.id, serialized_overwrites))
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"LockdownService: Failed to lock channel {channel.id}: {e}")
            return False

    async def unlock_channel(self, guild: discord.Guild, channel: discord.abc.GuildChannel, reason: Optional[str] = None) -> bool:
        """Restore a locked channel's original permissions."""
        try:
            # 1. Fetch from DB
            query = """
                SELECT original_overwrites, id FROM locks
                WHERE guild_id = ? AND target_id = ? AND is_active = 1
                ORDER BY id DESC LIMIT 1;
            """
            async with self.db.connection.execute(query, (guild.id, channel.id)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    # Fallback default reset if not tracked
                    everyone_role = guild.default_role
                    current_overwrite = channel.overwrites_for(everyone_role)
                    current_overwrite.send_messages = None
                    current_overwrite.add_reactions = None
                    current_overwrite.connect = None
                    current_overwrite.speak = None
                    await channel.set_permissions(everyone_role, overwrite=current_overwrite, reason=reason or "Unlock default reset")
                    return True
                    
                serialized_overwrites, lock_id = row
                original_overwrites = json.loads(serialized_overwrites)
                
            # 2. Restore all overwrites
            # Start fresh or reset @everyone
            everyone_role = guild.default_role
            everyone_overwrites = original_overwrites.get(str(everyone_role.id))
            
            if everyone_overwrites:
                allow_bits, deny_bits = everyone_overwrites["pair"]
                restored_overwrite = discord.PermissionOverwrite.from_pair(
                    discord.Permissions(allow_bits),
                    discord.Permissions(deny_bits)
                )
                await channel.set_permissions(everyone_role, overwrite=restored_overwrite, reason=reason or "Lockdown deactivated")
            else:
                # If no original override, clear it
                await channel.set_permissions(everyone_role, overwrite=None, reason=reason or "Lockdown deactivated")
                
            # 3. Mark lock as inactive
            query_update = "UPDATE locks SET is_active = 0 WHERE id = ?;"
            await self.db.execute(query_update, (lock_id,))
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"LockdownService: Failed to unlock channel {channel.id}: {e}")
            return False

    async def lock_category(self, guild: discord.Guild, category: discord.CategoryChannel, moderator: discord.Member | discord.User, reason: Optional[str] = None) -> bool:
        """Lock all channels inside a category."""
        success = True
        for channel in category.channels:
            if not await self.lock_channel(guild, channel, moderator, reason):
                success = False
        return success

    async def unlock_category(self, guild: discord.Guild, category: discord.CategoryChannel, reason: Optional[str] = None) -> bool:
        """Unlock all channels inside a category."""
        success = True
        for channel in category.channels:
            if not await self.unlock_channel(guild, channel, reason):
                success = False
        return success

    async def lock_guild(self, guild: discord.Guild, moderator: discord.Member | discord.User, reason: Optional[str] = None) -> bool:
        """Lock all text and voice channels in the guild."""
        success = True
        for channel in guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                if not await self.lock_channel(guild, channel, moderator, reason):
                    success = False
        return success

    async def unlock_guild(self, guild: discord.Guild, reason: Optional[str] = None) -> bool:
        """Unlock all text and voice channels in the guild."""
        success = True
        for channel in guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                if not await self.unlock_channel(guild, channel, reason):
                    success = False
        return success
