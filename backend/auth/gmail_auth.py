import os
import json
from pathlib import Path
from typing import TYPE_CHECKING

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

if TYPE_CHECKING:
    from google.auth.external_account_authorized_user import (
        Credentials as ExternalCredentials,
    )

from backend.config import get_settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]

CREDENTIALS_PATH = Path("credentials/credentials.json")
TOKEN_PATH = Path("token.json")


class GmailAuth:
    def __init__(self):
        self._creds = None
        self._redirect_uri = get_settings().redirect_uri
        self._flow: InstalledAppFlow | None = None
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
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"Credentials file not found at {CREDENTIALS_PATH}. "
                "Please download OAuth credentials from Google Cloud Console."
            )

        self._flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_PATH), SCOPES
        )
        self._flow.redirect_uri = self._redirect_uri

        auth_url, _ = self._flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )

        return auth_url

    def get_credentials(self) -> Credentials | None:
        if self.is_authenticated():
            return self._creds
        return None

    def exchange_code_for_token(self, code: str, state: str | None = None) -> bool:
        try:
            if self._flow is None:
                self._flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_PATH), SCOPES
                )
                self._flow.redirect_uri = self._redirect_uri

            authorization_response = (
                f"{self._redirect_uri}?code={code}&state={state or ''}"
            )
            self._flow.fetch_token(authorization_response=authorization_response)
            self._creds = self._flow.credentials

            self._save_credentials()
            self._flow = None
            return True

        except Exception as e:
            print(f"Error exchanging code: {e}")
            self._flow = None
            return False

    def get_user_email(self) -> str | None:
        if not self._creds:
            return None

        if self._creds.id_token:
            return self._creds.id_token.get("email")

        try:
            from googleapiclient.discovery import build

            service = build("gmail", "v1", credentials=self._creds)
            profile = service.users().getProfile(userId="me").execute()
            return profile.get("emailAddress")
        except Exception as e:
            print(f"Error fetching user email: {e}")
            return None

    def logout(self) -> None:
        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()
        self._creds = None
        self._flow = None


_gmail_auth: GmailAuth | None = None


def get_gmail_auth() -> GmailAuth:
    global _gmail_auth
    if _gmail_auth is None:
        _gmail_auth = GmailAuth()
    return _gmail_auth


def reset_gmail_auth() -> None:
    global _gmail_auth
    _gmail_auth = None
