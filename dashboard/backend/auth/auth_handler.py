"""Auth handler for Discord OAuth2 authentication."""

import os
import httpx
from typing import Any, Dict, Optional
from fastapi import APIRouter, Response, Request, HTTPException
from fastapi.responses import RedirectResponse
from utils.logger import logger

router = APIRouter(prefix="/api/auth")

CLIENT_ID = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8000").rstrip("/")
REDIRECT_URI = f"{DASHBOARD_URL}/api/auth/callback"

# Simple stateless JWT/encrypted cookie mechanism. For simplicity we'll use signed session storage or a stateless dict.
# A stateless encrypted token cookie is best, but since we are self-hosting on a single instance,
# an in-memory session mapping token -> UserData is extremely clean and works perfectly!
_sessions: Dict[str, Dict[str, Any]] = {}

def get_session_data(request: Request) -> Optional[Dict[str, Any]]:
    """Retrieve session data from secure cookie."""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in _sessions:
        return _sessions[session_id]
    return None

@router.get("/login")
async def login():
    """Redirect to Discord Authorization URL."""
    if not CLIENT_SECRET:
        logger.error("OAuth2: DISCORD_CLIENT_SECRET environment variable is missing!")
        raise HTTPException(status_code=500, detail="OAuth2 Client Secret not configured on bot.")

    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={httpx.URL(REDIRECT_URI)}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    return RedirectResponse(discord_auth_url)

@router.get("/callback")
async def callback(code: str, response: Response):
    """Callback receiver exchanging code for tokens."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")

    # 1. Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_url = "https://discord.com/api/oauth2/token"
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        token_response = await client.post(token_url, data=data, headers=headers)
        if token_response.status_code != 200:
            logger.error(f"OAuth2: Token exchange failed: {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to retrieve access token from Discord.")
            
        token_data = token_response.json()
        access_token = token_data["access_token"]

        # 2. Fetch User Profile
        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user profile.")
        user_data = user_response.json()

        # 3. Fetch User Guilds
        guilds_response = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        guilds_data = guilds_response.json() if guilds_response.status_code == 200 else []

    # 4. Store Session in Memory
    import uuid
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "user": user_data,
        "guilds": guilds_data,
        "access_token": access_token
    }

    # Set secure session cookie
    # Secure=True is set if DASHBOARD_URL is https
    is_secure = DASHBOARD_URL.startswith("https")
    response = RedirectResponse(url=f"{DASHBOARD_URL}/guilds")
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=3600 * 24 * 7 # 1 week
    )
    return response

@router.get("/logout")
async def logout(request: Request, response: Response):
    """Clear active session cookie."""
    session_id = request.cookies.get("session_id")
    if session_id in _sessions:
        del _sessions[session_id]
        
    response = RedirectResponse(url=f"{DASHBOARD_URL}/")
    response.delete_cookie("session_id")
    return response

@router.get("/me")
async def get_me(request: Request):
    """Retrieve logged-in user profile."""
    session = get_session_data(request)
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user": session["user"]}
