import pytest
from backend.services.unsubscribe import (
    extract_unsubscribe_url_from_headers,
    extract_unsubscribe_url_from_html,
    extract_unsubscribe_url_from_plain,
    extract_unsubscribe_url,
    parse_email_message,
    extract_sender_domain,
    simplify_html_for_preview,
    extract_snippet,
)


class TestExtractUnsubscribeUrlFromHeaders:
    def test_single_http_url(self):
        headers = {"List-Unsubscribe": "<https://example.com/unsubscribe>"}
        result = extract_unsubscribe_url_from_headers(headers)
        assert result == "https://example.com/unsubscribe"

    def test_multiple_urls_takes_first_http(self):
        headers = {"List-Unsubscribe": "<https://one.com>, <https://two.com>"}
        result = extract_unsubscribe_url_from_headers(headers)
        assert result == "https://one.com"

    def test_mailto_url(self):
        headers = {"List-Unsubscribe": "<mailto:unsubscribe@example.com>"}
        result = extract_unsubscribe_url_from_headers(headers)
        assert result == "mailto:unsubscribe@example.com"

    def test_mixed_http_and_mailto(self):
        headers = {
            "List-Unsubscribe": "<https://example.com/unsubscribe>, <mailto:unsubscribe@example.com>"
        }
        result = extract_unsubscribe_url_from_headers(headers)
        assert result == "https://example.com/unsubscribe"

    def test_one_click_unsubscribe(self):
        headers = {
            "List-Unsubscribe": "<https://example.com/unsubscribe>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        }
        result = extract_unsubscribe_url_from_headers(headers)
        assert result == "https://example.com/unsubscribe"

    def test_no_list_unsubscribe_header(self):
        headers = {"From": "test@example.com"}
        result = extract_unsubscribe_url_from_headers(headers)
        assert result is None

    def test_empty_list_unsubscribe(self):
        headers = {"List-Unsubscribe": ""}
        result = extract_unsubscribe_url_from_headers(headers)
        assert result is None


class TestExtractUnsubscribeUrlFromHtml:
    def test_simple_unsubscribe_link(self):
        html = '<a href="https://example.com/unsubscribe">Unsubscribe</a>'
        result = extract_unsubscribe_url_from_html(html)
        assert result == "https://example.com/unsubscribe"

    def test_case_insensitive_unsubscribe(self):
        html = '<a href="https://example.com/UNSUBSCRIBE">UNSUBSCRIBE</a>'
        result = extract_unsubscribe_url_from_html(html)
        assert result == "https://example.com/UNSUBSCRIBE"

    def test_opt_out_link(self):
        html = '<a href="https://example.com/opt-out">Click to opt out</a>'
        result = extract_unsubscribe_url_from_html(html)
        assert result == "https://example.com/opt-out"

    def test_optout_no_dash(self):
        html = '<a href="https://example.com/optout">Opt out</a>'
        result = extract_unsubscribe_url_from_html(html)
        assert result == "https://example.com/optout"

    def test_email_preferences_link(self):
        html = '<a href="https://example.com/email-preferences">Manage email preferences</a>'
        result = extract_unsubscribe_url_from_html(html)
        assert result == "https://example.com/email-preferences"

    def test_manage_subscription_link(self):
        html = (
            '<a href="https://example.com/manage-subscription">Manage subscription</a>'
        )
        result = extract_unsubscribe_url_from_html(html)
        assert result == "https://example.com/manage-subscription"

    def test_link_in_nested_html(self):
        html = """
        <div>
            <p>Click here to <a href="https://example.com/unsubscribe">unsubscribe</a></p>
        </div>
        """
        result = extract_unsubscribe_url_from_html(html)
        assert result == "https://example.com/unsubscribe"

    def test_no_unsubscribe_link(self):
        html = '<a href="https://example.com/home">Home</a>'
        result = extract_unsubscribe_url_from_html(html)
        assert result is None

    def test_empty_html(self):
        result = extract_unsubscribe_url_from_html("")
        assert result is None

    def test_none_html(self):
        result = extract_unsubscribe_url_from_html(None)
        assert result is None

    def test_url_in_href_lowercase(self):
        html = '<a href="https://example.com/UNSUBSCRIBE-LINK">Unsubscribe</a>'
        result = extract_unsubscribe_url_from_html(html)
        assert result == "https://example.com/UNSUBSCRIBE-LINK"


class TestExtractUnsubscribeUrlFromPlain:
    def test_plain_text_unsubscribe_url(self):
        text = "Click here to unsubscribe: https://example.com/unsubscribe"
        result = extract_unsubscribe_url_from_plain(text)
        assert result == "https://example.com/unsubscribe"

    def test_plain_text_no_unsubscribe(self):
        text = "Visit our homepage: https://example.com"
        result = extract_unsubscribe_url_from_plain(text)
        assert result is None

    def test_empty_text(self):
        result = extract_unsubscribe_url_from_plain("")
        assert result is None

    def test_none_text(self):
        result = extract_unsubscribe_url_from_plain(None)
        assert result is None

    def test_multiple_urls_takes_unsubscribe(self):
        text = "Visit https://example.com or unsubscribe at https://example.com/unsubscribe"
        result = extract_unsubscribe_url_from_plain(text)
        assert result == "https://example.com/unsubscribe"


class TestExtractUnsubscribeUrl:
    def test_html_content(self):
        html = '<a href="https://example.com/unsubscribe">Unsubscribe</a>'
        result = extract_unsubscribe_url(html, is_html=True)
        assert result == "https://example.com/unsubscribe"

    def test_plain_content(self):
        text = "https://example.com/unsubscribe"
        result = extract_unsubscribe_url(text, is_html=False)
        assert result == "https://example.com/unsubscribe"


class TestExtractSenderDomain:
    def test_simple_email(self):
        headers = {"From": "newsletter@example.com"}
        result = extract_sender_domain(headers)
        assert result == "example.com"

    def test_email_with_name(self):
        headers = {"From": "Newsletter <newsletter@example.com>"}
        result = extract_sender_domain(headers)
        assert result == "example.com"

    def test_email_with_angle_brackets(self):
        headers = {"From": "Newsletter <newsletter@example.com>"}
        result = extract_sender_domain(headers)
        assert result == "example.com"

    def test_no_from_header(self):
        headers = {}
        result = extract_sender_domain(headers)
        assert result is None

    def test_invalid_from(self):
        headers = {"From": "invalid"}
        result = extract_sender_domain(headers)
        assert result is None


class TestSimplifyHtmlForPreview:
    def test_simple_html(self):
        html = "<p>Hello <b>world</b>!</p>"
        result = simplify_html_for_preview(html)
        assert "Hello" in result
        assert "world" in result
        assert "<b>" not in result

    def test_removes_scripts(self):
        html = "<p>Text</p><script>alert('bad')</script>"
        result = simplify_html_for_preview(html)
        assert "alert" not in result

    def test_max_length(self):
        html = "<p>" + "a" * 1000 + "</p>"
        result = simplify_html_for_preview(html, max_length=100)
        assert len(result) <= 103  # 100 + "..."

    def test_empty_html(self):
        result = simplify_html_for_preview("")
        assert result == ""

    def test_none_html(self):
        result = simplify_html_for_preview(None)
        assert result == ""


class TestExtractSnippet:
    def test_html_snippet(self):
        html = "<p>Short content</p>"
        result = extract_snippet(html, is_html=True)
        assert "Short" in result

    def test_plain_snippet(self):
        text = "Short content"
        result = extract_snippet(text, is_html=False)
        assert result == "Short content"

    def test_long_content_truncated(self):
        html = "<p>" + "x" * 300 + "</p>"
        result = extract_snippet(html, is_html=True, max_length=200)
        assert len(result) <= 203  # 200 + "..."


class TestParseEmailMessage:
    def test_simple_text_email(self):
        raw = b"From: test@example.com\r\nSubject: Test\r\n\r\nHello World"
        headers, html, plain = parse_email_message(raw)
        assert "From" in headers
        assert plain == "Hello World"

    def test_multipart_email(self):
        raw = (
            b"From: test@example.com\r\n"
            b"Content-Type: multipart/alternative; boundary=abc\r\n"
            b"\r\n"
            b"--abc\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"Plain text"
            b"\r\n--abc\r\n"
            b"Content-Type: text/html\r\n"
            b"\r\n"
            b"<p>HTML content</p>"
            b"\r\n--abc--"
        )
        headers, html, plain = parse_email_message(raw)
        assert "HTML content" in html
        assert "Plain text" in plain
