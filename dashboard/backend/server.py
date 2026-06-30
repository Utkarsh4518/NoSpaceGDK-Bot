"""Main FastAPI application backend for the bot dashboard."""

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from dashboard.backend.auth.auth_handler import router as auth_router
from dashboard.backend.routers.guilds import router as guilds_router
from dashboard.backend.routers.music import router as music_router
from dashboard.backend.routers.ai import router as ai_router
from dashboard.backend.routers.websockets import router as ws_router
from services.music.player_manager import PlayerManager

app = FastAPI(title="NoSpaceFGK Dashboard", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to dashboard domain if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(guilds_router)
app.include_router(music_router)
app.include_router(ai_router)
app.include_router(ws_router)

# Mount static files folder if it exists
frontend_dist_path = os.path.join("dashboard", "frontend", "dist")
frontend_assets_path = os.path.join(frontend_dist_path, "assets")

if os.path.exists(frontend_assets_path):
    app.mount("/assets", StaticFiles(directory=frontend_assets_path), name="assets")

# Bot stats API endpoint
@app.get("/api/stats")
async def get_stats(request: Request):
    """Retrieve runtime bot and system spec statistics."""
    bot = request.app.state.bot
    
    # Calculate CPU/Memory specs
    import sys
    import platform
    import time
    
    uptime = 0.0
    if bot.start_time:
        import datetime
        uptime = (datetime.datetime.now(datetime.timezone.utc) - bot.start_time).total_seconds()

    return {
        "guild_count": len(bot.guilds),
        "user_count": sum(g.member_count for g in bot.guilds),
        "latency_ms": round(bot.latency * 1000, 2),
        "uptime_seconds": uptime,
        "platform": platform.system(),
        "python_version": sys.version.split()[0],
        "active_music_players": (
            sum(1 for p in bot.container.get(PlayerManager)._players.values() if p.state.name == "PLAYING")
            if hasattr(bot, "container") and bot.container.has(PlayerManager)
            else 0
        )
    }

# Fallback route to serve React Single Page Application (index.html)
@app.get("/{rest_of_path:path}")
async def catch_all(rest_of_path: str):
    """Catch-all router to redirect SPA subpaths back to React router index."""
    # Prevent catching API routes that might be missing/incorrect
    if rest_of_path.startswith("api/"):
        return {"error": "API route not found."}

    index_html = os.path.join(frontend_dist_path, "index.html")
    if os.path.exists(index_html):
        return FileResponse(index_html)
        
    return HTMLResponse(
        content="<h3>NoSpaceFGK Bot API is running!</h3><p>Build the frontend (using <code>npm run build</code>) to view the web dashboard.</p>",
        status_code=200
    )
