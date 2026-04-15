import re
from typing import Optional
from bs4 import BeautifulSoup
from email import policy
from email.parser import BytesParser


UNSUBSCRIBE_PATTERNS = [
    r"unsubscribe",
    r"opt-out",
    r"optout",
    r"email\s*preferences",
    r"manage\s*subscription",
]


def extract_unsubscribe_url_from_headers(headers: dict) -> Optional[str]:
    list_unsubscribe = headers.get("List-Unsubscribe", "")
    list_unsubscribe_post = headers.get("List-Unsubscribe-Post", "")

    if list_unsubscribe:
        urls = re.findall(r"<([^>]+)>", list_unsubscribe)
        for url in urls:
            if url.startswith("http"):
                return url

        if "mailto:" in list_unsubscribe:
            match = re.search(r"mailto:([^\s>]+)", list_unsubscribe)
            if match:
                return f"mailto:{match.group(1)}"

    if (
        list_unsubscribe_post
        and "List-Unsubscribe-Post=One-Click" in list_unsubscribe_post
    ):
        if list_unsubscribe:
            urls = re.findall(r"<([^>]+)>", list_unsubscribe)
            for url in urls:
                if url.startswith("http"):
                    return url

    return None


def extract_unsubscribe_url_from_html(html_content: str) -> Optional[str]:
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, "lxml")

    for link in soup.find_all("a", href=True):
        link_text = link.get_text().lower()
        href = link["href"]

        for pattern in UNSUBSCRIBE_PATTERNS:
            if re.search(pattern, link_text):
                return href

    for link in soup.find_all("a", href=True):
        href = link["href"].lower()
        if "unsubscribe" in href or "optout" in href or "opt-out" in href:
            return link["href"]

    return None


def extract_unsubscribe_url_from_plain(plain_content: str) -> Optional[str]:
    if not plain_content:
        return None

    for pattern in [
        r'(https?://[^\s<>"]+(?:unsubscribe|optout|opt-out)[^\s<>"]*)',
        r'(https?://[^\s<>"]+)',
    ]:
        matches = re.findall(pattern, plain_content, re.IGNORECASE)
        for match in matches:
            if "unsubscribe" in match.lower() or "optout" in match.lower():
                return match

    return None


def extract_unsubscribe_url(body: str, is_html: bool = True) -> Optional[str]:
    if is_html:
        return extract_unsubscribe_url_from_html(body)
    else:
        return extract_unsubscribe_url_from_plain(body)


def parse_email_message(raw_message: bytes) -> tuple[dict, str, str]:
    msg = BytesParser(policy=policy.default).parsebytes(raw_message)

    headers = {}
    for key, value in msg.items():
        headers[key] = value

    html_body = None
    plain_body = None

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/html" and html_body is None:
                try:
                    html_body = part.get_content()
                except Exception:
                    pass
            elif content_type == "text/plain" and plain_body is None:
                try:
                    plain_body = part.get_content()
                except Exception:
                    pass
    else:
        content_type = msg.get_content_type()
        try:
            content = msg.get_content()
            if content_type == "text/html":
                html_body = content
            else:
                plain_body = content
        except Exception:
            pass

    return headers, html_body or "", plain_body or ""


def extract_sender_domain(headers: dict) -> Optional[str]:
    from_email = headers.get("From", "")

    match = re.search(r"@([^>]+)", from_email)
    if match:
        domain = match.group(1)
        domain = domain.rstrip(">")
        return domain.lower()

    return None


def simplify_html_for_preview(html_content: str, max_length: int = 500) -> str:
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "lxml")

    for script in soup(["script", "style", "head"]):
        script.decompose()

    text = soup.get_text(separator=" ", strip=True)

    text = re.sub(r"\s+", " ", text)

    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def extract_snippet(body: str, is_html: bool = True, max_length: int = 200) -> str:
    if is_html:
        text = simplify_html_for_preview(body, max_length)
    else:
        text = body
        if len(text) > max_length:
            text = text[:max_length] + "..."

    return text
