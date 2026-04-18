from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
import asyncio

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.auth.gmail_auth import get_gmail_auth, reset_gmail_auth
from backend.db.database import (
    init_db,
    get_all_subscriptions,
    get_subscription_by_id,
    get_subscription_by_domain,
    create_subscription,
    update_subscription_email_stats,
    update_subscription_description,
    delete_subscription,
    add_email_example,
    get_email_examples_for_subscription,
    clear_all_subscriptions,
    get_subscription_count,
)
from backend.models.subscription import (
    SubscriptionCreate,
    Subscription as SubscriptionModel,
    SubscriptionWithEmails,
    EmailExampleCreate,
    EmailExample,
    ScanRequest,
    ScanStatus,
    AuthStatus,
    GenerateDescriptionRequest,
    UnsubscribeResponse,
)
from backend.services.gmail_service import get_gmail_service, group_messages_by_domain
from backend.services.openai_service import get_openai_service

scan_status: ScanStatus = ScanStatus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Gmail Subscription Cleanup API",
    description="Backend API for scanning Gmail and managing subscriptions",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8500", "http://127.0.0.1:8500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/auth/url")
async def get_oauth_url():
    auth = get_gmail_auth()
    try:
        url = auth.get_auth_url()
        return {"auth_url": url}
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


@app.get("/auth/callback")
async def auth_callback(code: str, state: Optional[str] = None):
    auth = get_gmail_auth()
    success = auth.exchange_code_for_token(code, state)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to authenticate"
        )

    frontend_url = f"http://localhost:8500"
    return RedirectResponse(url=frontend_url, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/auth/status", response_model=AuthStatus)
async def check_auth_status():
    auth = get_gmail_auth()
    return AuthStatus(
        is_authenticated=auth.is_authenticated(), email=auth.get_user_email()
    )


@app.post("/auth/logout")
async def logout():
    auth = get_gmail_auth()
    auth.logout()
    reset_gmail_auth()
    return {"message": "Logged out successfully"}


@app.post("/scan", response_model=ScanStatus)
async def scan_emails(request: ScanRequest):
    global scan_status

    auth = get_gmail_auth()
    if not auth.is_authenticated():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated with Gmail",
        )

    gmail_service = get_gmail_service()
    if not gmail_service:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to initialize Gmail service",
        )

    scan_status = ScanStatus(is_scanning=True)

    try:
        import asyncio

        await clear_all_subscriptions()

        max_messages = 100

        async def get_messages_with_limit():
            raw = []
            async for msg in gmail_service.get_messages_in_date_rangeAsync(
                days=request.days
            ):
                raw.append(msg)
                if len(raw) >= max_messages:
                    break
            return raw

        raw_messages = await asyncio.wait_for(get_messages_with_limit(), timeout=60.0)
        scan_status.messages_processed = len(raw_messages)

        parsed_messages = []
        for i, raw_msg in enumerate(raw_messages[:50]):
            msg_id = raw_msg.get("id")
            if msg_id:
                parsed = gmail_service.parse_message_for_subscription(msg_id)
                if parsed:
                    parsed_messages.append(parsed)

        domains = group_messages_by_domain(parsed_messages)

        for domain, domain_messages in domains.items():
            existing = await get_subscription_by_domain(domain)
            if existing:
                await update_subscription_email_stats(
                    existing.id,
                    email_count=len(domain_messages),
                    last_email_date=max(m["date"] for m in domain_messages),
                )

                for msg in domain_messages[:5]:
                    await add_email_example(
                        EmailExampleCreate(
                            subscription_id=existing.id,
                            gmail_message_id=msg["gmail_message_id"],
                            subject=msg["subject"],
                            snippet=msg["snippet"],
                            body_preview=msg["body_preview"],
                            date=msg["date"],
                        )
                    )
            else:
                first_msg = domain_messages[0]

                from_address = first_msg.get("from_email", "")
                name = domain.split(".")[0].title()

                new_sub = await create_subscription(
                    SubscriptionCreate(
                        name=name,
                        email=from_address,
                        domain=domain,
                        unsubscribe_url=first_msg["unsubscribe_url"],
                        description=None,
                    )
                )

                await update_subscription_email_stats(
                    new_sub.id,
                    email_count=len(domain_messages),
                    last_email_date=max(m["date"] for m in domain_messages),
                )

                for msg in domain_messages[:5]:
                    await add_email_example(
                        EmailExampleCreate(
                            subscription_id=new_sub.id,
                            gmail_message_id=msg["gmail_message_id"],
                            subject=msg["subject"],
                            snippet=msg["snippet"],
                            body_preview=msg["body_preview"],
                            date=msg["date"],
                        )
                    )

        scan_status.subscriptions_found = await get_subscription_count()
        scan_status.is_scanning = False
        scan_status.last_scan_date = datetime.utcnow()

        return scan_status

    except Exception as e:
        scan_status.is_scanning = False
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}",
        )


@app.get("/scan/status", response_model=ScanStatus)
async def get_scan_status():
    global scan_status
    return scan_status


@app.get("/subscriptions", response_model=list[SubscriptionModel])
async def list_subscriptions():
    return await get_all_subscriptions()


@app.get("/subscriptions/{subscription_id}", response_model=SubscriptionWithEmails)
async def get_subscription(subscription_id: str):
    subscription = await get_subscription_by_id(subscription_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    emails = await get_email_examples_for_subscription(subscription_id)

    return SubscriptionWithEmails(**subscription.model_dump(), emails=emails)


@app.post("/subscriptions/{subscription_id}/generate-description")
async def generate_description(
    subscription_id: str, request: GenerateDescriptionRequest
):
    subscription = await get_subscription_by_id(subscription_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    if not request.emails:
        emails = await get_email_examples_for_subscription(subscription_id)
        request.emails = [
            {"subject": e.subject, "body_preview": e.body_preview} for e in emails
        ]

    if not request.emails:
        return {"description": None, "message": "No emails available"}

    openai_service = get_openai_service()
    description = await openai_service.generate_description(
        sender_name=subscription.name,
        sender_domain=subscription.domain,
        email_subjects=[e["subject"] for e in request.emails],
        email_previews=[e["body_preview"] for e in request.emails],
    )

    if description:
        await update_subscription_description(subscription_id, description)

    return {"description": description}


@app.post("/subscriptions/{subscription_id}/unsubscribe")
async def unsubscribe(subscription_id: str):
    subscription = await get_subscription_by_id(subscription_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    import webbrowser

    try:
        webbrowser.open(subscription.unsubscribe_url)
        return UnsubscribeResponse(
            success=True, message="Unsubscribe page opened in browser", url_opened=True
        )
    except Exception as e:
        return UnsubscribeResponse(
            success=False, message=f"Failed to open browser: {str(e)}", url_opened=False
        )


@app.delete("/subscriptions/{subscription_id}")
async def remove_subscription(subscription_id: str):
    deleted = await delete_subscription(subscription_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    return {"message": "Subscription removed"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
