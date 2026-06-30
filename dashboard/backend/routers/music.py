"""Music control router for dashboard."""

from typing import Any, Dict, List
from fastapi import APIRouter, Request, HTTPException, Depends
from dashboard.backend.auth.auth_handler import get_session_data
from dashboard.backend.routers.guilds import validate_guild_access, get_current_user_session
from services.music.music_service import MusicService
from models.music import RepeatMode
from utils.logger import logger

router = APIRouter(prefix="/api/guilds/{guild_id}/music")

def _serialize_queue_item(item: Any) -> Dict[str, Any]:
    return {
        "uuid": item.uuid,
        "added_by": str(item.added_by),
        "added_at": item.added_at.isoformat() if item.added_at else None,
        "track": {
            "uuid": item.track.uuid,
            "title": item.track.title,
            "url": item.track.url,
            "duration": item.track.duration,
            "thumbnail": item.track.thumbnail,
            "provider": item.track.provider
        }
    }

@router.get("/state")
async def get_music_state(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Fetch current music playback state and queue."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    music_service = bot.container.get(MusicService)
    player = await music_service.get_player(guild_id)
    
    # Safely access queue list
    queue_list = []
    async with player.queue._lock:
        queue_list = [_serialize_queue_item(item) for item in player.queue._queue]

    current = None
    if player.current_track:
        current = _serialize_queue_item(player.current_track)
        current["position"] = player.position

    return {
        "state": player.state.name,
        "current": current,
        "queue": queue_list,
        "is_connected": player.voice.is_connected,
        "channel_id": str(player.voice.voice_client.channel.id) if player.voice.is_connected and player.voice.voice_client else None
    }

@router.post("/play")
async def play_track(guild_id: int, data: Dict[str, Any], request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Add a track/query to queue and play it."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Missing query/url to play.")
        
    music_service = bot.container.get(MusicService)
    player = await music_service.get_player(guild_id)
    user_id = int(session["user"]["id"])

    # 1. Connect bot to user's voice channel if not connected
    if not player.voice.is_connected:
        guild = bot.get_guild(guild_id)
        member = guild.get_member(user_id) if guild else None
        if not member or not member.voice or not member.voice.channel:
            raise HTTPException(status_code=400, detail="You must be in a voice channel for the bot to join.")
            
        await player.voice.connect_to_channel(member.voice.channel)

    # 2. Search for tracks
    try:
        tracks = await music_service.search(query)
        if not tracks:
            raise HTTPException(status_code=404, detail="No tracks found.")
            
        # Add first track to queue (or support list if playlist)
        item = await player.queue.add_track(tracks[0], user_id)
        
        # Start playing if idle
        from models.music import PlayerState
        if player.state in (PlayerState.IDLE, PlayerState.STOPPED):
            await player.play()
            
        # Broadcast queue update event to WebSockets
        from dashboard.backend.routers.websockets import manager
        await manager.broadcast({
            "type": "music_update",
            "guild_id": str(guild_id),
            "event": "track_added",
            "track": _serialize_queue_item(item)
        })
        
        return {"status": "success", "track": _serialize_queue_item(item)}
    except Exception as e:
        logger.error(f"Dashboard play_track failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pause")
async def pause_track(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Pause playback."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    music_service = bot.container.get(MusicService)
    player = await music_service.get_player(guild_id)
    await player.pause()
    return {"status": "success"}

@router.post("/resume")
async def resume_track(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Resume playback."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    music_service = bot.container.get(MusicService)
    player = await music_service.get_player(guild_id)
    await player.resume()
    return {"status": "success"}

@router.post("/skip")
async def skip_track(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Skip playback."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    music_service = bot.container.get(MusicService)
    player = await music_service.get_player(guild_id)
    await player.skip()
    return {"status": "success"}

@router.post("/stop")
async def stop_track(guild_id: int, request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Stop playback and clear current status."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    music_service = bot.container.get(MusicService)
    player = await music_service.get_player(guild_id)
    await player.stop()
    return {"status": "success"}

@router.post("/move")
async def move_track(guild_id: int, data: Dict[str, Any], request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Move item in queue."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    from_idx = data.get("from")
    to_idx = data.get("to")
    if from_idx is None or to_idx is None:
        raise HTTPException(status_code=400, detail="Missing from/to indexes.")
        
    music_service = bot.container.get(MusicService)
    player = await music_service.get_player(guild_id)
    moved = await player.queue.move_track(from_idx, to_idx)
    
    if not moved:
        raise HTTPException(status_code=400, detail="Failed to move: Index out of bounds.")
        
    return {"status": "success"}

@router.post("/remove")
async def remove_track(guild_id: int, data: Dict[str, Any], request: Request, session: Dict[str, Any] = Depends(get_current_user_session)):
    """Remove item from queue."""
    bot = request.app.state.bot
    validate_guild_access(guild_id, session, bot)
    
    target = data.get("target") # Can be index or UUID
    if target is None:
        raise HTTPException(status_code=400, detail="Missing target index or UUID.")
        
    music_service = bot.container.get(MusicService)
    player = await music_service.get_player(guild_id)
    removed = await player.queue.remove_track(target)
    
    if not removed:
        raise HTTPException(status_code=400, detail="Failed to remove: target not found.")
        
    return {"status": "success", "removed": _serialize_queue_item(removed)}
