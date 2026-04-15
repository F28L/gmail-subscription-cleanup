import aiosqlite
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional
import uuid

from backend.config import get_settings
from backend.models.subscription import (
    Subscription,
    SubscriptionCreate,
    EmailExample,
    EmailExampleCreate,
)


DATABASE_PATH = "./subscriptions.db"


async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                domain TEXT NOT NULL,
                unsubscribe_url TEXT NOT NULL,
                description TEXT,
                email_count INTEGER DEFAULT 0,
                last_email_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS email_examples (
                id TEXT PRIMARY KEY,
                subscription_id TEXT NOT NULL,
                gmail_message_id TEXT NOT NULL UNIQUE,
                subject TEXT NOT NULL,
                snippet TEXT NOT NULL,
                body_preview TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
            )
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_subscription 
            ON email_examples(subscription_id)
        """)

        await db.commit()


async def create_subscription(sub: SubscriptionCreate) -> Subscription:
    now = datetime.utcnow().isoformat()
    sub_id = str(uuid.uuid4())

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT INTO subscriptions 
            (id, name, email, domain, unsubscribe_url, description, email_count, last_email_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, NULL, ?, ?)
            """,
            (
                sub_id,
                sub.name,
                sub.email,
                sub.domain,
                sub.unsubscribe_url,
                sub.description,
                now,
                now,
            ),
        )
        await db.commit()

    return Subscription(
        id=sub_id,
        name=sub.name,
        email=sub.email,
        domain=sub.domain,
        unsubscribe_url=sub.unsubscribe_url,
        description=sub.description,
        email_count=0,
        last_email_date=datetime.fromisoformat(now),
        created_at=datetime.fromisoformat(now),
        updated_at=datetime.fromisoformat(now),
    )


async def get_subscription_by_domain(domain: str) -> Optional[Subscription]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM subscriptions WHERE domain = ?", (domain,)
        )
        row = await cursor.fetchone()

        if row is None:
            return None

        return Subscription(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            domain=row["domain"],
            unsubscribe_url=row["unsubscribe_url"],
            description=row["description"],
            email_count=row["email_count"],
            last_email_date=datetime.fromisoformat(row["last_email_date"])
            if row["last_email_date"]
            else datetime.utcnow(),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


async def get_all_subscriptions() -> list[Subscription]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM subscriptions ORDER BY last_email_date DESC"
        )
        rows = await cursor.fetchall()

        return [
            Subscription(
                id=row["id"],
                name=row["name"],
                email=row["email"],
                domain=row["domain"],
                unsubscribe_url=row["unsubscribe_url"],
                description=row["description"],
                email_count=row["email_count"],
                last_email_date=datetime.fromisoformat(row["last_email_date"])
                if row["last_email_date"]
                else datetime.utcnow(),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]


async def get_subscription_by_id(sub_id: str) -> Optional[Subscription]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,))
        row = await cursor.fetchone()

        if row is None:
            return None

        return Subscription(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            domain=row["domain"],
            unsubscribe_url=row["unsubscribe_url"],
            description=row["description"],
            email_count=row["email_count"],
            last_email_date=datetime.fromisoformat(row["last_email_date"])
            if row["last_email_date"]
            else datetime.utcnow(),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


async def update_subscription_email_stats(
    sub_id: str, email_count: int, last_email_date: datetime
) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            UPDATE subscriptions 
            SET email_count = ?, last_email_date = ?, updated_at = ?
            WHERE id = ?
            """,
            (email_count, last_email_date.isoformat(), now, sub_id),
        )
        await db.commit()


async def update_subscription_description(sub_id: str, description: str) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            UPDATE subscriptions 
            SET description = ?, updated_at = ?
            WHERE id = ?
            """,
            (description, now, sub_id),
        )
        await db.commit()


async def delete_subscription(sub_id: str) -> bool:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
        await db.commit()
        return cursor.rowcount > 0


async def add_email_example(email: EmailExampleCreate) -> EmailExample:
    email_id = str(uuid.uuid4())
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO email_examples 
            (id, subscription_id, gmail_message_id, subject, snippet, body_preview, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email_id,
                email.subscription_id,
                email.gmail_message_id,
                email.subject,
                email.snippet,
                email.body_preview,
                email.date.isoformat(),
            ),
        )
        await db.commit()

    return EmailExample(
        id=email_id,
        subscription_id=email.subscription_id,
        gmail_message_id=email.gmail_message_id,
        subject=email.subject,
        snippet=email.snippet,
        body_preview=email.body_preview,
        date=email.date,
    )


async def get_email_examples_for_subscription(
    subscription_id: str, limit: int = 5
) -> list[EmailExample]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM email_examples 
            WHERE subscription_id = ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (subscription_id, limit),
        )
        rows = await cursor.fetchall()

        return [
            EmailExample(
                id=row["id"],
                subscription_id=row["subscription_id"],
                gmail_message_id=row["gmail_message_id"],
                subject=row["subject"],
                snippet=row["snippet"],
                body_preview=row["body_preview"],
                date=datetime.fromisoformat(row["date"]),
            )
            for row in rows
        ]


async def get_subscription_count() -> int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM subscriptions")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def clear_all_subscriptions() -> None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM email_examples")
        await db.execute("DELETE FROM subscriptions")
        await db.commit()
