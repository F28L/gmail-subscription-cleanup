from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class ScanDays(int, Enum):
    THIRTY = 30
    SIXTY = 60
    NINETY = 90


class SubscriptionBase(BaseModel):
    name: str
    email: str
    domain: str
    unsubscribe_url: str
    description: Optional[str] = None


class SubscriptionCreate(SubscriptionBase):
    pass


class Subscription(SubscriptionBase):
    id: str
    email_count: int
    last_email_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionWithEmails(Subscription):
    emails: list["EmailExample"] = []


class EmailExampleBase(BaseModel):
    subject: str
    snippet: str
    body_preview: str
    date: datetime


class EmailExampleCreate(EmailExampleBase):
    subscription_id: str
    gmail_message_id: str


class EmailExample(EmailExampleBase):
    id: str
    subscription_id: str
    gmail_message_id: str

    class Config:
        from_attributes = True


class ScanRequest(BaseModel):
    days: ScanDays = Field(default=ScanDays.THIRTY)


class ScanStatus(BaseModel):
    is_scanning: bool = False
    subscriptions_found: int = 0
    messages_processed: int = 0
    last_scan_date: Optional[datetime] = None


class AuthStatus(BaseModel):
    is_authenticated: bool = False
    email: Optional[str] = None


class GenerateDescriptionRequest(BaseModel):
    emails: list[dict] = Field(default_factory=list)


class UnsubscribeResponse(BaseModel):
    success: bool
    message: str
    url_opened: bool = False


SubscriptionWithEmails.model_rebuild()
