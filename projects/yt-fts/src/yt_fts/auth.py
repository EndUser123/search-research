"""
YouTube OAuth 2.0 authentication for private playlist access.

This module provides OAuth credentials for accessing private YouTube playlists
like Watch Later (WL) and Liked Videos (LL) that require user authentication.

Based on yt_sync's OAuth implementation.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
else:
    Credentials = Any
    InstalledAppFlow = Any
    Request = Any
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    HAS_GOOGLE_AUTH = True
except ImportError:
    _credentials_import = None
    _installed_app_flow_import = None
    _request_import = None
    Credentials = Any
    InstalledAppFlow = Any
    Request = Any
    HAS_GOOGLE_AUTH = False
logger = logging.getLogger(__name__)
OAUTH_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
OAUTH_SECRETS_FILE = "client_secrets.json"
OAUTH_TOKEN_FILE = "youtube_oauth_token.json"
DEFAULT_PROFILE = "default"

def get_oauth_credentials(profile_name: str=DEFAULT_PROFILE, secrets_path: str | Path | None=None, token_path: str | Path | None=None) -> Any | None:
    """
    Handles the OAuth 2.0 flow for YouTube API access.

    Args:
        profile_name: Name for the OAuth profile (for token file naming)
        secrets_path: Path to client_secrets.json (default: ./client_secrets.json)
        token_path: Path to save token (default: ./youtube_oauth_token.json)

    Returns:
        Credentials object if successful, None otherwise
    """
    if not HAS_GOOGLE_AUTH:
        logger.error("Google authentication libraries not found. Install with: pip install google-auth-oauthlib google-api-python-client")
        return None
    if TYPE_CHECKING:
        assert Credentials is not None
        assert InstalledAppFlow is not None
        assert (Request is not None)
    if secrets_path is None:
        possible_secrets = [Path(OAUTH_SECRETS_FILE), Path(__file__).parent.parent.parent / OAUTH_SECRETS_FILE, Path.cwd() / OAUTH_SECRETS_FILE, Path.home() / OAUTH_SECRETS_FILE]
        secrets_path = next((p for p in possible_secrets if p.is_file()), None)
    else:
        secrets_path = Path(secrets_path)
    token_path = Path(OAUTH_TOKEN_FILE) if token_path is None else Path(token_path)
    if not secrets_path or not secrets_path.is_file():
        logger.error("OAuth secrets file not found: %s\nCreate one at: https://console.cloud.google.com/apis/credentials", OAUTH_SECRETS_FILE)
        return None
    creds = None
    if token_path.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), OAUTH_SCOPES)
        except Exception as e:
            logger.warning("Could not load existing token: %s", e)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired OAuth token...")
            try:
                creds.refresh(Request())
                logger.info("Token refreshed successfully")
            except Exception as e:
                logger.exception("Failed to refresh OAuth token: %s", e)
                creds = None
        if creds is None:
            logger.info("Starting OAuth flow for profile '%s'...", profile_name)
            try:
                flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), OAUTH_SCOPES)
                creds = flow.run_local_server(port=0, bind_addr="127.0.0.1", authorization_prompt_message="Please visit this URL to authorize this application:")
                logger.info("OAuth authentication successful")
            except Exception as e:
                logger.exception("OAuth flow failed: %s", e)
                return None
        try:
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())
            logger.info("OAuth token saved to %s", token_path)
        except Exception as e:
            logger.warning("Could not save token: %s", e)
    return creds

def test_credentials(creds: Any) -> bool:
    """
    Test if credentials are valid by making a simple API request.

    Args:
        creds: Credentials object to test

    Returns:
        True if credentials work, False otherwise
    """
    if not creds or not creds.valid:
        return False
    try:
        import requests
        headers = {"Authorization": f"Bearer {creds.token}"}
        response = requests.get("https://www.googleapis.com/youtube/v3/channels?part=id&mine=true", headers=headers, timeout=10)
        return response.status_code == 200
    except (OSError, TimeoutError):
        return False

def setup_oauth_instructions() -> str:
    """
    Return instructions for setting up OAuth for YouTube API access.

    Returns:
        Multi-line string with setup instructions
    """
    return '\n[bold cyan]YouTube OAuth Setup for Private Playlists[/bold cyan]\n\nTo access private playlists like Watch Later (WL) or Liked Videos (LL),\nyou need to set up OAuth credentials:\n\n[yellow]1. Create OAuth Credentials[/yellow]\n\n   • Go to: https://console.cloud.google.com/apis/credentials\n   • Create a new project or select existing one\n   • Click "Create Credentials" → "OAuth client ID"\n   • Application type: "Desktop app"\n   • Name: "yt-fts"\n   • Download the credentials as [cyan]client_secrets.json[/cyan]\n\n[yellow]2. Place the file[/yellow]\n\n   • Put [cyan]client_secrets.json[/cyan] in your yt-fts project directory\n   • Or in your home directory\n\n[yellow]3. Run the playlist command again[/yellow]\n\n   The first time will open a browser for authorization.\n\n[bold yellow]Note:[/bold yellow] OAuth is only needed for private playlists (WL, LL).\nPublic playlists work without OAuth.\n'

def is_oauth_required(playlist_id: str) -> bool:
    """
    Check if a playlist requires OAuth authentication.

    Args:
        playlist_id: YouTube playlist ID

    Returns:
        True if OAuth is typically required for this playlist
    """
    oauth_playlists = {"WL", "LL"}
    return playlist_id in oauth_playlists
