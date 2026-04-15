import pytest
from datetime import datetime
from backend.db.database import (
    init_db,
    create_subscription,
    get_subscription_by_domain,
    get_all_subscriptions,
    get_subscription_by_id,
    update_subscription_email_stats,
    update_subscription_description,
    delete_subscription,
    add_email_example,
    get_email_examples_for_subscription,
    get_subscription_count,
    clear_all_subscriptions,
)
from backend.models.subscription import SubscriptionCreate, EmailExampleCreate


@pytest.mark.asyncio
async def test_init_db(test_db):
    await init_db()
    assert True


@pytest.mark.asyncio
async def test_create_subscription(test_db, sample_subscription_data):
    sub_create = SubscriptionCreate(**sample_subscription_data)
    subscription = await create_subscription(sub_create)

    assert subscription.id is not None
    assert subscription.name == sample_subscription_data["name"]
    assert subscription.email == sample_subscription_data["email"]
    assert subscription.domain == sample_subscription_data["domain"]
    assert subscription.unsubscribe_url == sample_subscription_data["unsubscribe_url"]
    assert subscription.description == sample_subscription_data["description"]
    assert subscription.email_count == 0


@pytest.mark.asyncio
async def test_get_subscription_by_domain(test_db, sample_subscription_data):
    sub_create = SubscriptionCreate(**sample_subscription_data)
    created = await create_subscription(sub_create)

    found = await get_subscription_by_domain(sample_subscription_data["domain"])

    assert found is not None
    assert found.id == created.id
    assert found.domain == sample_subscription_data["domain"]


@pytest.mark.asyncio
async def test_get_subscription_by_domain_not_found(test_db):
    found = await get_subscription_by_domain("nonexistent.com")
    assert found is None


@pytest.mark.asyncio
async def test_get_all_subscriptions(test_db, sample_subscription_data):
    for i in range(3):
        data = sample_subscription_data.copy()
        data["domain"] = f"domain{i}.com"
        data["email"] = f"test{i}@domain{i}.com"
        await create_subscription(SubscriptionCreate(**data))

    subscriptions = await get_all_subscriptions()

    assert len(subscriptions) == 3


@pytest.mark.asyncio
async def test_get_subscription_by_id(test_db, sample_subscription_data):
    sub_create = SubscriptionCreate(**sample_subscription_data)
    created = await create_subscription(sub_create)

    found = await get_subscription_by_id(created.id)

    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
async def test_get_subscription_by_id_not_found(test_db):
    found = await get_subscription_by_id("nonexistent-id")
    assert found is None


@pytest.mark.asyncio
async def test_update_subscription_email_stats(test_db, sample_subscription_data):
    sub_create = SubscriptionCreate(**sample_subscription_data)
    created = await create_subscription(sub_create)

    from datetime import datetime

    await update_subscription_email_stats(
        created.id, email_count=10, last_email_date=datetime(2024, 1, 15)
    )

    updated = await get_subscription_by_id(created.id)

    assert updated.email_count == 10
    assert updated.last_email_date == datetime(2024, 1, 15)


@pytest.mark.asyncio
async def test_update_subscription_description(test_db, sample_subscription_data):
    sub_create = SubscriptionCreate(**sample_subscription_data)
    created = await create_subscription(sub_create)

    new_description = "Updated description"
    await update_subscription_description(created.id, new_description)

    updated = await get_subscription_by_id(created.id)

    assert updated.description == new_description


@pytest.mark.asyncio
async def test_delete_subscription(test_db, sample_subscription_data):
    sub_create = SubscriptionCreate(**sample_subscription_data)
    created = await create_subscription(sub_create)

    result = await delete_subscription(created.id)

    assert result is True
    found = await get_subscription_by_id(created.id)
    assert found is None


@pytest.mark.asyncio
async def test_delete_subscription_not_found(test_db):
    result = await delete_subscription("nonexistent-id")
    assert result is False


@pytest.mark.asyncio
async def test_add_email_example(test_db, sample_subscription_data, sample_email_data):
    sub_create = SubscriptionCreate(**sample_subscription_data)
    created = await create_subscription(sub_create)

    email_data = sample_email_data.copy()
    email_data["subscription_id"] = created.id

    email_create = EmailExampleCreate(**email_data)
    email = await add_email_example(email_create)

    assert email.id is not None
    assert email.subscription_id == created.id
    assert email.subject == email_data["subject"]


@pytest.mark.asyncio
async def test_get_email_examples_for_subscription(test_db, sample_subscription_data):
    sub_create = SubscriptionCreate(**sample_subscription_data)
    created = await create_subscription(sub_create)

    for i in range(7):
        email_data = {
            "subscription_id": created.id,
            "gmail_message_id": f"msg-{i}",
            "subject": f"Email {i}",
            "snippet": f"Snippet {i}",
            "body_preview": f"Body {i}",
            "date": datetime(2024, 1, i + 1, 12, 0, 0),
        }
        await add_email_example(EmailExampleCreate(**email_data))

    emails = await get_email_examples_for_subscription(created.id, limit=5)

    assert len(emails) == 5


@pytest.mark.asyncio
async def test_get_subscription_count(test_db, sample_subscription_data):
    assert await get_subscription_count() == 0

    for i in range(3):
        data = sample_subscription_data.copy()
        data["domain"] = f"domain{i}.com"
        data["email"] = f"test{i}@domain{i}.com"
        await create_subscription(SubscriptionCreate(**data))

    assert await get_subscription_count() == 3


@pytest.mark.asyncio
async def test_clear_all_subscriptions(test_db, sample_subscription_data):
    for i in range(3):
        data = sample_subscription_data.copy()
        data["domain"] = f"domain{i}.com"
        data["email"] = f"test{i}@domain{i}.com"
        await create_subscription(SubscriptionCreate(**data))

    await clear_all_subscriptions()

    count = await get_subscription_count()
    assert count == 0
