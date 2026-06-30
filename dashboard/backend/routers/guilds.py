"""Guilds router for managing guild settings, welcome notifications, tickets, and moderation."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from dashboard.backend.auth.auth_handler import get_session_data
from repositories import GuildSettingsRepository, CaseRepository, WarningRepository
from repository import TicketRepository, ReactionRoleRepository
from services.server import WelcomeService, GoodbyeService
from utils.logger import logger

router = APIRouter(prefix="/api/guilds")

def get_current_user_session(request: Request) -> Dict[str, Any]:
    """Dependency to retrieve session or raise 401."""
    session = get_session_data(request)
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return session

def validate_guild_access(guild_id: int, session: Dict[str, Any], bot: Any) -> None:
    """Validates user has admin/manage permissions or is a bot owner."""
    user_id = int(session["user"]["id"])
    
    # Check bot owner bypass
    if user_id in bot.config.owner_ids:
        return # Owner override

    # Check Discord MANAGE_GUILD (0x20) or ADMINISTRATOR (0x8)
    user_guilds = session.get("guilds", [])
    for g in user_guilds:
        if int(g["id"]) == guild_id:
            perms = int(g.get("permissions", 0))
            if (perms & 0x8) == 0x8 or (perms & 0x20) == 0x20:
                return
                
    raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to manage this server.")

@router.get("")
async def get_guilds(request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Fetch user's manageable guilds and mark if bot is present."""
    bot = request.app.state.bot
    user_guilds = session.get("guilds", [])
    
    manageable = []
    user_id = int(session["user"]["id"])
    is_owner = user_id in bot.config.owner_ids

    # If bot owner, they can manage ALL guilds the bot is in
    if is_owner:
        for guild in bot.guilds:
            manageable.append({
                "id": str(guild.id),
                "name": guild.name,
                "icon": guild.icon.url if guild.icon else None,
                "bot_present": True,
                "permissions": "ADMINISTRATOR"
            })
        return manageable

    # Standard user: check guilds they manage
    for g in user_guilds:
        perms = int(g.get("permissions", 0))
        if (perms & 0x8) == 0x8 or (perms & 0x20) == 0x20:
            guild_id = int(g["id"])
            guild = bot.get_guild(guild_id)
            manageable.append({
                "id": g["id"],
                "name": g["name"],
                "icon": f"https://cdn.discordapp.com/icons/{g['id']}/{g['icon']}.png" if g["icon"] else None,
                "bot_present": guild is not None,
                "permissions": "ADMINISTRATOR" if (perms & 0x8) == 0x8 else "MANAGE_GUILD"
            })
            
    return manageable

@router.get("/{guild_id}/settings")
async def get_settings(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Get general guild settings."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    settings_repo = bot.container.get(GuildSettingsRepository)
    settings = await settings_repo.get_settings(guild_id)
    
    return {
        "default_timeout_seconds": settings.default_timeout_seconds,
        "default_warning_limit": settings.default_warning_limit,
        "audit_channel_id": str(settings.audit_channel_id) if settings.audit_channel_id else None,
        "moderator_roles": settings.moderator_roles or "",
        "protected_roles": settings.protected_roles or "",
        "ignored_channels": settings.ignored_channels or "",
        "ignored_roles": settings.ignored_roles or ""
    }

@router.post("/{guild_id}/settings")
async def post_settings(guild_id: int, data: Dict[str, Any], request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Update guild settings."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    settings_repo = bot.container.get(GuildSettingsRepository)
    
    # Save settings in DB
    query = """
        INSERT OR REPLACE INTO guild_settings (
            guild_id, default_timeout_seconds, default_warning_limit, audit_channel_id,
            moderator_roles, protected_roles, ignored_channels, ignored_roles
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    await settings_repo.db.execute(
        query,
        (
            guild_id,
            data.get("default_timeout_seconds", 3600),
            data.get("default_warning_limit", 3),
            int(data["audit_channel_id"]) if data.get("audit_channel_id") else None,
            data.get("moderator_roles", ""),
            data.get("protected_roles", ""),
            data.get("ignored_channels", ""),
            data.get("ignored_roles", "")
        )
    )
    await settings_repo.db.commit()
    
    return {"status": "success", "message": "Settings updated successfully."}

@router.get("/{guild_id}/moderation")
async def get_moderation(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Fetch warnings and cases logs for moderation page."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    case_repo = bot.container.get(CaseRepository)
    warn_repo = bot.container.get(WarningRepository)
    
    # Fetch all active/closed cases
    cases = []
    query = "SELECT id, case_type, user_id, moderator_id, reason, duration_seconds, status, created_at FROM cases WHERE guild_id = ? ORDER BY id DESC;"
    async with case_repo.db.connection.execute(query, (guild_id,)) as cursor:
        async for row in cursor:
            cases.append({
                "id": row[0],
                "type": row[1],
                "user_id": str(row[2]),
                "moderator_id": str(row[3]),
                "reason": row[4],
                "duration": row[5],
                "status": row[6],
                "created_at": row[7]
            })

    return {"cases": cases}

@router.get("/{guild_id}/tickets")
async def get_tickets(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Fetch tickets list and statistics."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    ticket_repo = bot.container.get(TicketRepository)
    tickets = []
    query = "SELECT id, channel_id, creator_id, status, claimed_by, topic, created_at, closed_at FROM tickets WHERE guild_id = ? ORDER BY id DESC;"
    async with ticket_repo.db.connection.execute(query, (guild_id,)) as cursor:
        async for row in cursor:
            tickets.append({
                "id": row[0],
                "channel_id": str(row[1]),
                "creator_id": str(row[2]),
                "status": row[3],
                "claimed_by": str(row[4]) if row[4] else None,
                "topic": row[5],
                "created_at": row[6],
                "closed_at": row[7]
            })
            
    return {"tickets": tickets}

@router.get("/{guild_id}/welcome")
async def get_welcome(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Fetch welcome and goodbye system configuration."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    w_service = bot.container.get(WelcomeService)
    g_service = bot.container.get(GoodbyeService)
    
    w_settings = await w_service.get_settings(guild_id)
    g_settings = await g_service.get_settings(guild_id)
    
    return {
        "welcome": {
            "channel_id": str(w_settings.channel_id) if w_settings and w_settings.channel_id else None,
            "message_text": w_settings.message_text if w_settings else "",
            "embed_json": w_settings.embed_json if w_settings else "",
            "dm_enabled": w_settings.dm_enabled if w_settings else False,
            "enabled": w_settings.enabled if w_settings else False
        },
        "goodbye": {
            "channel_id": str(g_settings.channel_id) if g_settings and g_settings.channel_id else None,
            "message_text": g_settings.message_text if g_settings else "",
            "embed_json": g_settings.embed_json if g_settings else "",
            "enabled": g_settings.enabled if g_settings else False
        }
    }

@router.post("/{guild_id}/welcome")
async def post_welcome(guild_id: int, data: Dict[str, Any], request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Save welcome and goodbye configuration."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    w_service = bot.container.get(WelcomeService)
    g_service = bot.container.get(GoodbyeService)
    
    w_data = data.get("welcome", {})
    g_data = data.get("goodbye", {})
    
    await w_service.save_settings(
        guild_id=guild_id,
        channel_id=int(w_data["channel_id"]) if w_data.get("channel_id") else None,
        message_text=w_data.get("message_text"),
        embed_json=w_data.get("embed_json"),
        dm_enabled=w_data.get("dm_enabled", False),
        enabled=w_data.get("enabled", False)
    )
    
    await g_service.save_settings(
        guild_id=guild_id,
        channel_id=int(g_data["channel_id"]) if g_data.get("channel_id") else None,
        message_text=g_data.get("message_text"),
        embed_json=g_data.get("embed_json"),
        enabled=g_data.get("enabled", False)
    )
    
    return {"status": "success", "message": "Welcome/Goodbye settings saved."}

@router.get("/{guild_id}/reaction_roles")
async def get_reaction_roles(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """List reaction roles panel configurations."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    rr_repo = bot.container.get(ReactionRoleRepository)
    messages = await rr_repo.get_all_reaction_role_messages(guild_id)
    
    panels = []
    for msg in messages:
        roles = await rr_repo.get_reaction_roles(msg.message_id)
        panels.append({
            "message_id": str(msg.message_id),
            "channel_id": str(msg.channel_id),
            "title": msg.title,
            "description": msg.description,
            "group_name": msg.group_name,
            "type": msg.type,
            "roles": [{
                "emoji": r.emoji,
                "role_id": str(r.role_id),
                "label": r.group_name
            } for r in roles]
        })
        
    return {"panels": panels}
