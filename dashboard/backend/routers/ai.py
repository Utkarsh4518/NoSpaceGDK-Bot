"""AI configuration router for dashboard APIs."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from dashboard.backend.auth.auth_handler import get_session_data
from dashboard.backend.routers.guilds import validate_guild_access, get_current_user_session
from services.ai.ai_service import AIService
from utils.logger import logger

router = APIRouter(prefix="/api/guilds/{guild_id}/ai")

async def _ensure_ai_config_table(db: Any) -> None:
    """Helper to ensure the ai_guild_configs table exists."""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS ai_guild_configs (
            guild_id INTEGER PRIMARY KEY,
            provider TEXT,
            model TEXT,
            system_prompt TEXT,
            disabled_tools TEXT
        );
    """)
    await db.commit()

@router.get("")
async def get_ai_config(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Fetch current AI provider, model, custom prompt, and tool states for a guild."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    ai_service = bot.container.get(AIService)
    db = ai_service.conversations.repo.db # Fetch database manager reference
    await _ensure_ai_config_table(db)

    # Fetch guild custom overrides
    provider = ai_service.providers.default_provider_name
    model = ai_service._default_model
    system_prompt = bot.config.system_prompt
    disabled_tools = []

    query = "SELECT provider, model, system_prompt, disabled_tools FROM ai_guild_configs WHERE guild_id = ?;"
    async with db.connection.execute(query, (guild_id,)) as cursor:
        row = await cursor.fetchone()
        if row:
            if row[0]: provider = row[0]
            if row[1]: model = row[1]
            if row[2]: system_prompt = row[2]
            if row[3]: disabled_tools = row[3].split(",") if row[3] else []

    # Get all tools from agent
    available_tools = []
    if ai_service.agent:
        all_tools = ai_service.agent.tool_manager.get_all_tools()
        for t in all_tools:
            available_tools.append({
                "name": t.name,
                "description": t.description,
                "enabled": t.name not in disabled_tools
            })

    return {
        "providers": ai_service.providers.list_available_providers(),
        "current_provider": provider,
        "current_model": model,
        "system_prompt": system_prompt,
        "tools": available_tools
    }

@router.post("")
async def save_ai_config(guild_id: int, data: Dict[str, Any], request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Save AI configuration overrides for a guild."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    ai_service = bot.container.get(AIService)
    db = ai_service.conversations.repo.db
    await _ensure_ai_config_table(db)

    provider = data.get("provider")
    model = data.get("model")
    system_prompt = data.get("system_prompt")
    
    # List of disabled tool names
    disabled_tools = data.get("disabled_tools", [])
    disabled_tools_str = ",".join(disabled_tools) if disabled_tools else ""

    query = """
        INSERT OR REPLACE INTO ai_guild_configs (guild_id, provider, model, system_prompt, disabled_tools)
        VALUES (?, ?, ?, ?, ?);
    """
    await db.execute(query, (guild_id, provider, model, system_prompt, disabled_tools_str))
    await db.commit()

    # Apply prompt overrides dynamically to the prompt manager
    if system_prompt:
        # User ID of dashboard manager
        user_id = int(session["user"]["id"])
        await ai_service.prompts.set_guild_prompt(guild_id, system_prompt, user_id)

    return {"status": "success", "message": "AI settings updated successfully."}
