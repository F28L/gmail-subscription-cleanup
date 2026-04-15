from openai import AsyncOpenAI
from typing import Optional
import asyncio

from backend.config import get_settings


class OpenAIService:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"

    async def generate_description(
        self,
        sender_name: str,
        sender_domain: str,
        email_subjects: list[str],
        email_previews: list[str],
    ) -> Optional[str]:
        if not email_subjects and not email_previews:
            return None

        subjects_text = "\n".join(f"- {s}" for s in email_subjects[:5])
        previews_text = "\n".join(f"- {p[:200]}" for p in email_previews[:5])

        prompt = f"""Analyze this email subscription and provide a brief, helpful description.

Sender: {sender_name} ({sender_domain})

Recent email subjects:
{subjects_text}

Email content snippets:
{previews_text}

Based on this information, provide a 1-2 sentence description that helps someone understand what this subscription is about. Be concise and informative. Start directly with the description, no preamble."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes email subscriptions concisely.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error generating description: {e}")
            return None

    async def batch_generate_descriptions(
        self, subscriptions: list[dict]
    ) -> dict[str, str]:
        results = {}

        async def process_one(sub: dict):
            desc = await self.generate_description(
                sender_name=sub["name"],
                sender_domain=sub["domain"],
                email_subjects=sub.get("subjects", []),
                email_previews=sub.get("previews", []),
            )
            return sub["id"], desc

        tasks = [process_one(sub) for sub in subscriptions]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for result in completed:
            if isinstance(result, tuple):
                sub_id, desc = result
                results[sub_id] = desc

        return results


_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service
