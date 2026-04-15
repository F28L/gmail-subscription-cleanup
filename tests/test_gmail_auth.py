import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
import json


class TestGmailAuth:
    @pytest.fixture
    def clean_auth(self):
        from backend.auth.gmail_auth import reset_gmail_auth

        reset_gmail_auth()
        yield
        reset_gmail_auth()

    def test_is_authenticated_false_when_no_token(self, clean_auth):
        from backend.auth.gmail_auth import GmailAuth

        with patch(
            "backend.auth.gmail_auth.TOKEN_PATH", Path("/nonexistent/token.json")
        ):
            with patch(
                "backend.auth.gmail_auth.CREDENTIALS_PATH",
                Path("/nonexistent/creds.json"),
            ):
                auth = GmailAuth()
                assert auth.is_authenticated() is False

    def test_get_auth_url_raises_when_no_credentials_file(self, clean_auth):
        from backend.auth.gmail_auth import GmailAuth

        with patch(
            "backend.auth.gmail_auth.CREDENTIALS_PATH", Path("/nonexistent/path.json")
        ):
            with patch(
                "backend.auth.gmail_auth.TOKEN_PATH", Path("/nonexistent/token.json")
            ):
                auth = GmailAuth()
                with pytest.raises(FileNotFoundError):
                    auth.get_auth_url()

    @patch("backend.auth.gmail_auth.InstalledAppFlow")
    def test_get_auth_url_success(self, mock_flow_class, clean_auth, tmp_path):
        from backend.auth.gmail_auth import GmailAuth

        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ("https://auth.url", None)
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(
            '{"installed": {"client_id": "test", "client_secret": "test"}}'
        )
        token_file = tmp_path / "token.json"

        with patch("backend.auth.gmail_auth.CREDENTIALS_PATH", creds_file):
            with patch("backend.auth.gmail_auth.TOKEN_PATH", token_file):
                auth = GmailAuth()
                url = auth.get_auth_url()

        assert url == "https://auth.url"
        mock_flow.authorization_url.assert_called_once()

    def test_get_user_email_returns_none_when_not_authenticated(self, clean_auth):
        from backend.auth.gmail_auth import GmailAuth

        with patch(
            "backend.auth.gmail_auth.TOKEN_PATH", Path("/nonexistent/token.json")
        ):
            with patch(
                "backend.auth.gmail_auth.CREDENTIALS_PATH",
                Path("/nonexistent/creds.json"),
            ):
                auth = GmailAuth()
                assert auth.get_user_email() is None

    def test_logout_removes_token(self, clean_auth, tmp_path):
        from backend.auth.gmail_auth import GmailAuth

        token_path = tmp_path / "token.json"
        token_path.write_text(
            json.dumps(
                {
                    "token": "test",
                    "refresh_token": "refresh",
                    "client_id": "id",
                    "client_secret": "secret",
                }
            )
        )

        with patch("backend.auth.gmail_auth.TOKEN_PATH", token_path):
            with patch(
                "backend.auth.gmail_auth.CREDENTIALS_PATH",
                Path("/nonexistent/creds.json"),
            ):
                auth = GmailAuth()
                auth.logout()

        assert not token_path.exists()

    def test_get_credentials_returns_none_when_not_authenticated(self, clean_auth):
        from backend.auth.gmail_auth import GmailAuth

        with patch(
            "backend.auth.gmail_auth.TOKEN_PATH", Path("/nonexistent/token.json")
        ):
            with patch(
                "backend.auth.gmail_auth.CREDENTIALS_PATH",
                Path("/nonexistent/creds.json"),
            ):
                auth = GmailAuth()
                assert auth.get_credentials() is None


class TestGmailAuthSingleton:
    def test_singleton_pattern(self):
        from backend.auth.gmail_auth import get_gmail_auth, reset_gmail_auth

        reset_gmail_auth()

        auth1 = get_gmail_auth()
        auth2 = get_gmail_auth()

        assert auth1 is auth2

        reset_gmail_auth()
