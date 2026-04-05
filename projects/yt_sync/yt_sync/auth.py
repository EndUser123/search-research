# yt_sync/auth.py

import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .ytdlp_legacy_wrapper import SPOOFED_USER_AGENT, YTDLP_EXECUTABLE

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
except ImportError:
    Credentials, InstalledAppFlow, Request = None, None, None

logger = logging.getLogger(__name__)

OAUTH_SECRETS_FILE = "client_secrets.json"
OAUTH_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
CANARY_VIDEO_ID = "dQw4w9WgXcQ"


def get_oauth_credentials(profile_name: str) -> Any | None:
    """Handles the OAuth 2.0 flow for a named user profile."""
    if not all((Credentials, InstalledAppFlow, Request)):
        logger.error(
            "Google authentication libraries not found. Please run: pip install google-auth-oauthlib google-api-python-client"
        )
        return None

    token_filename = f"token_{profile_name}.json"
    token_path = Path(token_filename)
    secrets_path = Path(OAUTH_SECRETS_FILE)
    creds = None

    # Assertions for type narrowing to satisfy Pylance
    assert (
        Credentials is not None and InstalledAppFlow is not None and Request is not None
    )

    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), OAUTH_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info(
                f"Refreshing expired OAuth token for profile '{profile_name}'..."
            )
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh OAuth token for '{profile_name}': {e}")
                return None
        else:
            if not secrets_path.is_file():
                logger.critical(f"OAuth Error: '{OAUTH_SECRETS_FILE}' not found.")
                return None
            logger.info(f"Starting new OAuth flow for profile '{profile_name}'...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(secrets_path), OAUTH_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
        logger.info(f"OAuth token for '{profile_name}' saved to '{token_path}'")

    return creds


def validate_and_select_profile(config: dict[str, Any]) -> Any | None:
    """Iterates through OAuth profiles from config, tests each one, and returns the first valid credentials."""
    profiles = config.get("oauth_profiles", [])
    if not profiles:
        return None

    logger.info("🔐 Searching for a valid OAuth profile...")
    for profile_name in profiles:
        logger.info(f"  Validating profile '{profile_name}'...")
        creds = get_oauth_credentials(profile_name)
        if not creds:
            logger.warning(
                f"    Profile '{profile_name}' failed to generate credentials."
            )
            continue

        auth_header = f"Authorization: Bearer {creds.token}"
        cmd = [
            YTDLP_EXECUTABLE,
            "--quiet",
            "--no-warnings",
            "--ignore-config",
            "--list-thumbnails",
            "--add-header",
            auth_header,
            "--user-agent",
            SPOOFED_USER_AGENT,
            f"https://www.youtube.com/watch?v={CANARY_VIDEO_ID}",
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", timeout=60
            )
            if result.returncode == 0 and result.stdout.strip():
                logger.info(f"  ✅ Profile '{profile_name}' is valid and active.")
                return creds
            else:
                logger.warning(f"    Profile '{profile_name}' failed validation.")
        except Exception as e:
            logger.warning(
                f"    An error occurred while validating profile '{profile_name}': {e}."
            )

    logger.warning("All defined OAuth profiles failed validation.")
    return None
