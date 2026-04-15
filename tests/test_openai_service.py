import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestOpenAIService:
    @pytest.fixture
    def mock_openai(self):
        with patch("backend.services.openai_service.AsyncOpenAI") as mock:
            mock_client = MagicMock()
            mock.return_value = mock_client
            yield mock_client

    def test_service_initialization(self):
        from backend.services.openai_service import OpenAIService

        service = OpenAIService()
        assert service.model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_generate_description_success(self, mock_openai):
        from backend.services.openai_service import OpenAIService

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = "A weekly newsletter about technology trends."

        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

        service = OpenAIService()
        result = await service.generate_description(
            sender_name="Tech Weekly",
            sender_domain="techweekly.com",
            email_subjects=["This week's tech news", "New AI developments"],
            email_previews=[
                "Here's what's happening in tech...",
                "AI is changing everything...",
            ],
        )

        assert result == "A weekly newsletter about technology trends."
        mock_openai.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_description_empty_emails(self, mock_openai):
        from backend.services.openai_service import OpenAIService

        service = OpenAIService()
        result = await service.generate_description(
            sender_name="Test",
            sender_domain="test.com",
            email_subjects=[],
            email_previews=[],
        )

        assert result is None
        mock_openai.chat.completions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_description_api_error(self, mock_openai):
        from backend.services.openai_service import OpenAIService

        mock_openai.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        service = OpenAIService()
        result = await service.generate_description(
            sender_name="Test",
            sender_domain="test.com",
            email_subjects=["Subject 1"],
            email_previews=["Preview 1"],
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_batch_generate_descriptions(self, mock_openai):
        from backend.services.openai_service import OpenAIService

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Description"

        mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

        service = OpenAIService()
        subscriptions = [
            {
                "id": "1",
                "name": "Sub1",
                "domain": "sub1.com",
                "subjects": ["S1"],
                "previews": ["P1"],
            },
            {
                "id": "2",
                "name": "Sub2",
                "domain": "sub2.com",
                "subjects": ["S2"],
                "previews": ["P2"],
            },
        ]

        results = await service.batch_generate_descriptions(subscriptions)

        assert len(results) == 2
        assert "1" in results
        assert "2" in results


class TestGetOpenAIService:
    def test_singleton_pattern(self):
        import backend.services.openai_service as service_module

        service_module._openai_service = None

        service1 = service_module.get_openai_service()
        service2 = service_module.get_openai_service()

        assert service1 is service2

        service_module._openai_service = None
