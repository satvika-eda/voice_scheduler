import os
import json
import base64
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import Flow

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CLIENT_SECRET_FILE = os.getenv("GOOGLE_CLIENT_SECRET_FILE", "client_secret.json")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")


def get_flow(state=None):
    """Create an OAuth Flow.

    Priority:
    1. Use client secrets JSON file if present (CLIENT_SECRET_FILE)
    2. Else, build from GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET env vars
    """
    client_path = Path(CLIENT_SECRET_FILE)
    if client_path.exists():
        return Flow.from_client_secrets_file(
            str(client_path),
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
            state=state,
        )

    # Fallback: build from env vars
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if client_id and client_secret:
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        }
        return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=REDIRECT_URI, state=state)

    raise RuntimeError(
        "No Google OAuth client configuration found. Provide a client_secret.json or set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment."
    )


def get_service_account_credentials() -> ServiceAccountCredentials:
    """Get credentials from a service account JSON file or environment variable."""
    service_account_path = Path(SERVICE_ACCOUNT_FILE)
    if service_account_path.exists():
        return ServiceAccountCredentials.from_service_account_file(
            str(service_account_path), scopes=SCOPES
        )
    
    # Try to load from base64-encoded env var (Cloud Run compatible)
    service_account_b64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_B64")
    if service_account_b64:
        try:
            service_account_json = base64.b64decode(service_account_b64).decode('utf-8')
            service_account_info = json.loads(service_account_json)
            return ServiceAccountCredentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )
        except Exception as e:
            raise RuntimeError(f"Failed to decode service account from GOOGLE_SERVICE_ACCOUNT_JSON_B64: {str(e)}")
    
    # Try plain JSON env var
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        service_account_info = json.loads(service_account_json)
        return ServiceAccountCredentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )
    
    raise RuntimeError(
        "No service account configuration found. Provide service_account.json file or set GOOGLE_SERVICE_ACCOUNT_JSON_B64 in environment."
    )


def build_credentials_from_token(token_data: dict) -> Credentials:
    return Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )
