import os
import json
from pathlib import Path
from typing import Optional

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from backend.config import get_settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]

CREDENTIALS_PATH = Path("credentials/credentials.json")
TOKEN_PATH = Path("token.json")

_flow_instance: Optional[InstalledAppFlow] = None


class GmailAuth:
    def __init__(self):
        self._creds: Optional[Credentials] = None
        self._redirect_uri = get_settings().redirect_uri
        self._flow: Optional[InstalledAppFlow] = None
        self._load_credentials()

    def _load_credentials(self) -> None:
        if TOKEN_PATH.exists():
            self._creds = Credentials.from_authorized_user_info(
                json.loads(TOKEN_PATH.read_text()), SCOPES
            )

            if self._creds and self._creds.expired and self._creds.refresh_token:
                try:
                    self._creds.refresh(Request())
                    self._save_credentials()
                except Exception:
                    self._creds = None

    def _save_credentials(self) -> None:
        if self._creds:
            TOKEN_PATH.write_text(self._creds.to_json())

    def is_authenticated(self) -> bool:
        return self._creds is not None and self._creds.valid

    def get_auth_url(self) -> str:
        global _flow_instance

        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"Credentials file not found at {CREDENTIALS_PATH}. "
                "Please download OAuth credentials from Google Cloud Console."
            )

        _flow_instance = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH), SCOPES
        )
        _flow_instance.redirect_uri = self._redirect_uri

        auth_url, _ = _flow_instance.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )

        return auth_url

    def get_credentials(self) -> Optional[Credentials]:
        if self.is_authenticated():
            return self._creds
        return None

    def exchange_code_for_token(self, code: str, state: Optional[str] = None) -> bool:
        global _flow_instance

        try:
            if _flow_instance is None:
                _flow_instance = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_PATH), SCOPES
                )
                _flow_instance.redirect_uri = self._redirect_uri

            authorization_response = (
                f"{self._redirect_uri}?code={code}&state={state or ''}"
            )
            _flow_instance.fetch_token(authorization_response=authorization_response)
            self._creds = _flow_instance.credentials

            self._save_credentials()
            _flow_instance = None
            return True

        except Exception as e:
            print(f"Error exchanging code: {e}")
            _flow_instance = None
            return False

    def get_user_email(self) -> Optional[str]:
        if not self._creds:
            return None

        return self._creds.id_token.get("email") if self._creds.id_token else None

    def logout(self) -> None:
        global _flow_instance

        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()
        self._creds = None
        _flow_instance = None


_gmail_auth: Optional[GmailAuth] = None


def get_gmail_auth() -> GmailAuth:
    global _gmail_auth
    if _gmail_auth is None:
        _gmail_auth = GmailAuth()
    return _gmail_auth


def reset_gmail_auth() -> None:
    global _gmail_auth
    _gmail_auth = None
