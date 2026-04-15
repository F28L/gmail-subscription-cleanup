import pytest
from datetime import datetime
from pydantic import ValidationError
from backend.models.subscription import (
    ScanDays,
    ScanRequest,
    Subscription,
    SubscriptionCreate,
    EmailExample,
    EmailExampleCreate,
    ScanStatus,
    AuthStatus,
    GenerateDescriptionRequest,
)


class TestScanDays:
    def test_scan_days_values(self):
        assert ScanDays.THIRTY == 30
        assert ScanDays.SIXTY == 60
        assert ScanDays.NINETY == 90


class TestScanRequest:
    def test_default_scan_request(self):
        request = ScanRequest()
        assert request.days == ScanDays.THIRTY

    def test_custom_scan_days(self):
        request = ScanRequest(days=60)
        assert request.days == 60

    def test_invalid_scan_days(self):
        with pytest.raises(ValidationError):
            ScanRequest(days=45)


class TestSubscriptionCreate:
    def test_valid_subscription_create(self):
        sub = SubscriptionCreate(
            name="Test Newsletter",
            email="test@example.com",
            domain="example.com",
            unsubscribe_url="https://example.com/unsubscribe",
        )
        assert sub.name == "Test Newsletter"
        assert sub.email == "test@example.com"
        assert sub.domain == "example.com"
        assert sub.description is None

    def test_subscription_with_description(self):
        sub = SubscriptionCreate(
            name="Test",
            email="test@test.com",
            domain="test.com",
            unsubscribe_url="https://test.com/unsubscribe",
            description="A great newsletter",
        )
        assert sub.description == "A great newsletter"

    def test_subscription_missing_required_field(self):
        with pytest.raises(ValidationError):
            SubscriptionCreate(name="Test", email="test@test.com", domain="test.com")


class TestSubscription:
    def test_subscription_model(self):
        now = datetime.utcnow()
        sub = Subscription(
            id="test-id",
            name="Test",
            email="test@test.com",
            domain="test.com",
            unsubscribe_url="https://test.com/unsubscribe",
            description="Test description",
            email_count=5,
            last_email_date=now,
            created_at=now,
            updated_at=now,
        )
        assert sub.id == "test-id"
        assert sub.email_count == 5


class TestEmailExampleCreate:
    def test_valid_email_example_create(self):
        email = EmailExampleCreate(
            subscription_id="sub-id",
            gmail_message_id="msg-123",
            subject="Test Subject",
            snippet="Snippet text",
            body_preview="Body preview text",
            date=datetime.utcnow(),
        )
        assert email.subscription_id == "sub-id"
        assert email.subject == "Test Subject"

    def test_email_example_missing_field(self):
        with pytest.raises(ValidationError):
            EmailExampleCreate(
                subscription_id="sub-id",
                gmail_message_id="msg-123",
                subject="Test Subject",
            )


class TestEmailExample:
    def test_email_example_model(self):
        now = datetime.utcnow()
        email = EmailExample(
            id="email-id",
            subscription_id="sub-id",
            gmail_message_id="msg-123",
            subject="Test Subject",
            snippet="Snippet",
            body_preview="Body",
            date=now,
        )
        assert email.id == "email-id"
        assert email.gmail_message_id == "msg-123"


class TestScanStatus:
    def test_default_scan_status(self):
        status = ScanStatus()
        assert status.is_scanning is False
        assert status.subscriptions_found == 0
        assert status.messages_processed == 0
        assert status.last_scan_date is None

    def test_scan_status_with_values(self):
        now = datetime.utcnow()
        status = ScanStatus(
            is_scanning=True,
            subscriptions_found=10,
            messages_processed=100,
            last_scan_date=now,
        )
        assert status.is_scanning is True
        assert status.subscriptions_found == 10
        assert status.messages_processed == 100


class TestAuthStatus:
    def test_not_authenticated(self):
        status = AuthStatus()
        assert status.is_authenticated is False
        assert status.email is None

    def test_authenticated_with_email(self):
        status = AuthStatus(is_authenticated=True, email="user@gmail.com")
        assert status.is_authenticated is True
        assert status.email == "user@gmail.com"


class TestGenerateDescriptionRequest:
    def test_default_request(self):
        request = GenerateDescriptionRequest()
        assert request.emails == []

    def test_request_with_emails(self):
        request = GenerateDescriptionRequest(
            emails=[
                {"subject": "Test 1", "body_preview": "Body 1"},
                {"subject": "Test 2", "body_preview": "Body 2"},
            ]
        )
        assert len(request.emails) == 2
