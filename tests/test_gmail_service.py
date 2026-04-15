import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestGmailService:
    @pytest.fixture
    def mock_gmail_service(self):
        from backend.services.gmail_service import GmailService

        mock_creds = MagicMock()
        mock_service = MagicMock()

        with patch("backend.services.gmail_service.build", return_value=mock_service):
            service = GmailService(mock_creds)
            yield service, mock_service

    def test_init_creates_gmail_service(self, mock_gmail_service):
        service, mock_service = mock_gmail_service
        assert service.service is mock_service

    def test_parse_message_for_subscription(self, mock_gmail_service):
        service, mock_service = mock_gmail_service

        raw_message = b"""From: newsletter@example.com\r\nSubject: Test Subject\r\nDate: Mon, 15 Jan 2024 10:00:00 +0000\r\nList-Unsubscribe: <https://example.com/unsubscribe>\r\nContent-Type: text/html\r\n\r\n<html><body><p>Test body</p></body></html>"""

        import base64

        mock_service.users().messages().get.return_value.execute.return_value = {
            "raw": base64.urlsafe_b64encode(raw_message).decode()
        }

        result = service.parse_message_for_subscription("msg123")

        assert result is not None
        assert result["domain"] == "example.com"
        assert "unsubscribe" in result["unsubscribe_url"]

    def test_parse_message_returns_none_for_no_unsubscribe(self, mock_gmail_service):
        service, mock_service = mock_gmail_service

        raw_message = b"""From: newsletter@example.com\r\nSubject: Test Subject\r\nDate: Mon, 15 Jan 2024 10:00:00 +0000\r\n\r\n<html><body><p>No unsubscribe here</p></body></html>"""

        import base64

        mock_service.users().messages().get.return_value.execute.return_value = {
            "raw": base64.urlsafe_b64encode(raw_message).decode()
        }

        result = service.parse_message_for_subscription("msg123")

        assert result is None

    def test_parse_message_returns_none_for_no_domain(self, mock_gmail_service):
        service, mock_service = mock_gmail_service

        raw_message = b"""Subject: Test Subject\r\nList-Unsubscribe: <https://example.com/unsubscribe>\r\n\r\n<html><body><p>Test</p></body></html>"""

        import base64

        mock_service.users().messages().get.return_value.execute.return_value = {
            "raw": base64.urlsafe_b64encode(raw_message).decode()
        }

        result = service.parse_message_for_subscription("msg123")

        assert result is None

    def test_search_messages(self, mock_gmail_service):
        service, mock_service = mock_gmail_service

        mock_service.users().messages().list.return_value.execute.return_value = {
            "messages": [{"id": "msg1"}, {"id": "msg2"}]
        }

        messages = list(service.search_messages("test query"))

        assert len(messages) == 2
        assert messages[0]["id"] == "msg1"

    def test_search_messages_with_pagination(self, mock_gmail_service):
        service, mock_service = mock_gmail_service

        mock_service.users().messages().list.return_value.execute.side_effect = [
            {"messages": [{"id": "msg1"}, {"id": "msg2"}], "nextPageToken": "token2"},
            {"messages": [{"id": "msg3"}]},
        ]

        messages = list(service.search_messages("test query", max_results=10))

        assert len(messages) == 3

    def test_get_messages_in_date_range(self, mock_gmail_service):
        service, mock_service = mock_gmail_service

        mock_service.users().messages().list.return_value.execute.return_value = {
            "messages": []
        }

        messages = list(service.get_messages_in_date_range(days=30))

        assert isinstance(messages, list)
        mock_service.users().messages().list.assert_called()


class TestGroupMessagesByDomain:
    def test_groups_messages_correctly(self):
        from backend.services.gmail_service import group_messages_by_domain

        messages = [
            {"domain": "example.com", "id": "1"},
            {"domain": "example.com", "id": "2"},
            {"domain": "other.com", "id": "3"},
        ]

        result = group_messages_by_domain(messages)

        assert len(result) == 2
        assert len(result["example.com"]) == 2
        assert len(result["other.com"]) == 1

    def test_handles_missing_domain(self):
        from backend.services.gmail_service import group_messages_by_domain

        messages = [
            {"domain": "example.com", "id": "1"},
            {"id": "2"},
            {"domain": None, "id": "3"},
        ]

        result = group_messages_by_domain(messages)

        assert len(result) == 1
        assert "example.com" in result


class TestGetGmailService:
    @patch("backend.services.gmail_service.get_gmail_auth")
    def test_returns_none_when_not_authenticated(self, mock_auth_func):
        mock_auth = MagicMock()
        mock_auth.get_credentials.return_value = None
        mock_auth_func.return_value = mock_auth

        from backend.services.gmail_service import get_gmail_service

        result = get_gmail_service()

        assert result is None

    @patch("backend.services.gmail_service.get_gmail_auth")
    def test_returns_service_when_authenticated(self, mock_auth_func):
        mock_auth = MagicMock()
        mock_creds = MagicMock()
        mock_auth.get_credentials.return_value = mock_creds
        mock_auth_func.return_value = mock_auth

        with patch("backend.services.gmail_service.build") as mock_build:
            mock_build.return_value = MagicMock()

            from backend.services.gmail_service import get_gmail_service

            result = get_gmail_service()

            assert result is not None
            mock_build.assert_called_once()
