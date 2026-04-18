from typing import Optional, Generator
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
import email
from email import policy
from email.parser import BytesParser

from backend.auth.gmail_auth import get_gmail_auth
from backend.services.unsubscribe import (
    extract_unsubscribe_url_from_headers,
    extract_unsubscribe_url_from_html,
    extract_unsubscribe_url_from_plain,
    extract_sender_domain,
    simplify_html_for_preview,
    extract_snippet,
)
from backend.models.subscription import EmailExampleCreate


CATEGORY_QUERY = "category:promotions OR category:updates"


class GmailService:
    def __init__(self, creds: Credentials):
        self.service = build("gmail", "v1", credentials=creds)

    def _fetch_raw_message(self, msg_id: str) -> Optional[bytes]:
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=msg_id, format="raw")
                .execute()
            )

            raw_data = message.get("raw", "")
            return base64.urlsafe_b64decode(raw_data)
        except Exception as e:
            print(f"Error fetching message {msg_id}: {e}")
            return None

    def search_messages(
        self, query: str, max_results: int = 500
    ) -> Generator[dict, None, None]:
        page_token = None

        while True:
            try:
                results = (
                    self.service.users()
                    .messages()
                    .list(
                        userId="me",
                        q=query,
                        maxResults=max_results if max_results <= 500 else 500,
                        pageToken=page_token,
                    )
                    .execute()
                )

                messages = results.get("messages", [])

                for msg in messages:
                    yield msg

                if len(messages) >= max_results:
                    break

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

            except Exception as e:
                print(f"Error searching messages: {e}")
                break

    def get_messages_in_date_range(self, days: int = 30) -> Generator[dict, None, None]:
        after_date = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
        query = f"{CATEGORY_QUERY} after:{after_date}"

        return self.search_messages(query)

    async def get_messages_in_date_rangeAsync(self, days: int = 30):
        for msg in self.get_messages_in_date_range(days):
            yield msg

    def parse_message_for_subscription(self, msg_id: str) -> Optional[dict]:
        raw_message = self._fetch_raw_message(msg_id)
        if not raw_message:
            return None

        headers, html_body, plain_body = self._parse_message_headers(raw_message)

        sender_domain = extract_sender_domain(headers)
        if not sender_domain:
            return None

        unsubscribe_url = self._extract_unsubscribe_url(headers, html_body, plain_body)
        if not unsubscribe_url:
            return None

        subject = headers.get("Subject", "No Subject")
        date_str = headers.get("Date", "")

        try:
            date = email.utils.parsedate_to_datetime(date_str)
        except Exception:
            date = datetime.now()

        snippet = extract_snippet(html_body, is_html=True)
        body_preview = simplify_html_for_preview(html_body, max_length=500)

        return {
            "gmail_message_id": msg_id,
            "subject": subject,
            "snippet": snippet,
            "body_preview": body_preview,
            "date": date,
            "domain": sender_domain,
            "unsubscribe_url": unsubscribe_url,
            "from_email": headers.get("From", ""),
        }

    def _parse_message_headers(self, raw_message: bytes) -> tuple[dict, str, str]:
        msg = BytesParser(policy=policy.default).parsebytes(raw_message)

        headers = {}
        for key, value in msg.items():
            headers[key] = value

        html_body = ""
        plain_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/html" and not html_body:
                    try:
                        html_body = part.get_content()
                    except Exception:
                        pass
                elif content_type == "text/plain" and not plain_body:
                    try:
                        plain_body = part.get_content()
                    except Exception:
                        pass
        else:
            content_type = msg.get_content_type()
            try:
                content = (
                    part.get_content() if msg.is_multipart() else msg.get_content()
                )
                if content_type == "text/html":
                    html_body = content
                else:
                    plain_body = content
            except Exception:
                pass

        return headers, html_body, plain_body

    def _extract_unsubscribe_url(
        self, headers: dict, html_body: str, plain_body: str
    ) -> Optional[str]:
        url = extract_unsubscribe_url_from_headers(headers)
        if url:
            return url

        if html_body:
            url = extract_unsubscribe_url_from_html(html_body)
            if url:
                return url

        if plain_body:
            url = extract_unsubscribe_url_from_plain(plain_body)
            if url:
                return url

        return None


def get_gmail_service() -> Optional[GmailService]:
    auth = get_gmail_auth()
    creds = auth.get_credentials()

    if not creds:
        return None

    return GmailService(creds)


def group_messages_by_domain(messages: list[dict]) -> dict[str, list[dict]]:
    domains = {}

    for msg in messages:
        domain = msg.get("domain")
        if domain:
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(msg)

    return domains
