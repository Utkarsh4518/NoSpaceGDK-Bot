"""Automod Service for scanning messages and applying rules."""

import datetime
import re
from typing import Any, Dict, List, Optional
import discord
from repositories.automod_repository import AutomodRepository
from services.moderation.warning_service import WarningService
from services.moderation.case_service import CaseService
from services.base_service import BaseService
from utils.logger import logger

class AutomodService(BaseService):
    """Scans and moderates messages based on configurable guild rules."""

    def __init__(
        self,
        bot: Any,
        automod_repo: AutomodRepository,
        warning_service: WarningService,
        case_service: CaseService
    ) -> None:
        self.bot = bot
        self.repo = automod_repo
        self.warnings = warning_service
        self.cases = case_service
        
        # In-memory user cache: { (guild_id, user_id): {"timestamps": [float], "last_message": str, "last_message_time": float} }
        self._cache: Dict[tuple, dict] = {}

    def _get_user_cache(self, guild_id: int, user_id: int) -> dict:
        key = (guild_id, user_id)
        if key not in self._cache:
            self._cache[key] = {
                "timestamps": [],
                "last_message": "",
                "last_message_time": 0.0
            }
        return self._cache[key]

    async def scan_message(self, message: discord.Message) -> bool:
        """Scan a message against all enabled automod rules for the guild.
        
        Returns:
            True if message was flagged and handled (deleted/moderated), False otherwise.
        """
        if message.author.bot or not message.guild:
            return False
            
        guild_id = message.guild.id
        user_id = message.author.id
        
        # 1. Fetch enabled rules
        rules = await self.repo.get_rules_for_guild(guild_id)
        if not rules:
            return False

        import json
        import time
        now = time.time()
        user_cache = self._get_user_cache(guild_id, user_id)
        
        for rule in rules:
            if not rule.is_enabled:
                continue
                
            config = json.loads(rule.config)
            rule_type = rule.rule_type
            flagged = False
            trigger_reason = ""
            
            # Extract basic config
            action = config.get("action", "delete") # 'delete', 'warn', 'timeout'
            cooldown_seconds = config.get("cooldown", 5)
            
            if rule_type == "spam":
                limit = config.get("limit", 5) # messages allowed
                interval = config.get("interval", 3) # within interval seconds
                
                # Append current timestamp
                user_cache["timestamps"] = [t for t in user_cache["timestamps"] if now - t < interval]
                user_cache["timestamps"].append(now)
                
                if len(user_cache["timestamps"]) > limit:
                    flagged = True
                    trigger_reason = f"Spamming: Sent {len(user_cache['timestamps'])} messages in {interval}s."
                    
            elif rule_type == "duplicate":
                limit = config.get("limit", 3) # duplicate count
                interval = config.get("interval", 10) # within seconds
                
                content = message.content.strip().lower()
                if content:
                    if content == user_cache["last_message"] and now - user_cache["last_message_time"] < interval:
                        user_cache["duplicate_count"] = user_cache.get("duplicate_count", 0) + 1
                    else:
                        user_cache["duplicate_count"] = 1
                        
                    user_cache["last_message"] = content
                    user_cache["last_message_time"] = now
                    
                    if user_cache["duplicate_count"] > limit:
                        flagged = True
                        trigger_reason = f"Duplicate messages: Sent duplicate content {user_cache['duplicate_count']} times."

            elif rule_type == "mentions":
                limit = config.get("limit", 5)
                mention_count = len(message.mentions) + len(message.role_mentions)
                if mention_count > limit:
                    flagged = True
                    trigger_reason = f"Mass mentions: Sent {mention_count} mentions (limit {limit})."
                    
            elif rule_type == "links_invite":
                # Regex for Discord invite links
                invite_regex = r"(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)\/[a-zA-Z0-9-]+"
                if re.search(invite_regex, message.content):
                    flagged = True
                    trigger_reason = "Discord invite link detected."
                    
            elif rule_type == "links_external":
                url_regex = r"https?://[^\s]+"
                # Avoid flagging internal invites if invites are separate, or just general external link block
                if re.search(url_regex, message.content):
                    flagged = True
                    trigger_reason = "External link detected."
                    
            elif rule_type == "bad_words":
                banned_words = config.get("words", [])
                content = message.content.lower()
                for word in banned_words:
                    if word.lower() in content:
                        flagged = True
                        trigger_reason = f"Banned word usage detected."
                        break
                        
            elif rule_type == "caps":
                threshold = config.get("threshold", 0.7) # 70% caps
                min_length = config.get("min_length", 10)
                text = message.content.strip()
                if len(text) >= min_length:
                    caps_count = sum(1 for c in text if c.isupper())
                    alpha_count = sum(1 for c in text if c.isalpha())
                    if alpha_count > 0 and (caps_count / alpha_count) > threshold:
                        flagged = True
                        trigger_reason = f"Caps spam: {int(caps_count/alpha_count*100)}% capitals."
                        
            elif rule_type == "emojis":
                limit = config.get("limit", 10)
                # Count custom emojis and unicode emojis (approximate)
                custom_emojis = len(re.findall(r"<a?:[a-zA-Z0-9_]+:[0-9]+>", message.content))
                if custom_emojis > limit:
                    flagged = True
                    trigger_reason = f"Emoji spam: {custom_emojis} emojis used."
                    
            elif rule_type == "files":
                allowed_extensions = config.get("allowed", [])
                for attachment in message.attachments:
                    ext = attachment.filename.split(".")[-1].lower()
                    if allowed_extensions and ext not in allowed_extensions:
                        flagged = True
                        trigger_reason = f"File restriction: File type .{ext} not permitted."
                        break

            if flagged:
                await self._handle_violation(message, rule_type, action, trigger_reason)
                return True
                
        return False

    async def _handle_violation(self, message: discord.Message, rule_type: str, action: str, reason: str) -> None:
        """Handle flagged user violation according to the configured rule action."""
        guild = message.guild
        member = message.author
        
        # 1. Delete message
        try:
            await message.delete()
        except discord.Forbidden:
            logger.warning(f"AutomodService: Failed to delete violation message (Forbidden).")
            
        # 2. Inform the user in the channel (temporary alert or standard warning)
        try:
            alert = await message.channel.send(
                embed=discord.Embed(
                    title="Automod Alert ⚠️",
                    description=f"{member.mention}, your message was removed. Reason: **{reason}**",
                    color=discord.Color.red()
                )
            )
            # Delete alert after 5 seconds to keep channel clean
            import asyncio
            asyncio.create_task(self._delete_after_delay(alert, 5))
        except Exception:
            pass

        # 3. Apply warning or timeout punishments
        system_mod = self.bot.user # Mod is the bot itself
        
        if action == "warn":
            await self.warnings.warn_user(
                guild_id=guild.id,
                user=member,
                moderator=system_mod,
                reason=f"Automod ({rule_type}): {reason}"
            )
        elif action == "timeout":
            duration = datetime.timedelta(minutes=10) # Default automod timeout
            try:
                await member.timeout(duration, reason=f"Automod ({rule_type}): {reason}")
                await self.cases.create_case(
                    guild_id=guild.id,
                    case_type="timeout",
                    user=member,
                    moderator=system_mod,
                    reason=f"Automod ({rule_type}): {reason}",
                    duration_seconds=600
                )
            except discord.Forbidden:
                pass

        # Fallback create a general case record for the automod trigger itself
        await self.cases.create_case(
            guild_id=guild.id,
            case_type="automod",
            user=member,
            moderator=system_mod,
            reason=f"Automod Rule [{rule_type}] triggered: {reason}"
        )

    async def _delete_after_delay(self, message: discord.Message, delay: float) -> None:
        import asyncio
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except discord.NotFound:
            pass
        except Exception as e:
            logger.error(f"AutomodService: Error deleting alert: {e}")
