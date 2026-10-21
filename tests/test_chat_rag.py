import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.llm_service import LLMService
from app.services.chat_service import ChatService
from app.services.retrieval_service import RetrievedContext
from app.models.chat import MessageRole


@pytest.mark.asyncio
async def test_llm_service_with_mocked_openrouter():
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "Dar Global delivered 66% revenue growth in HY 2026 reaching $258.0 million.\n\n"
        "```chart\n"
        "{\n"
        '  "title": "HY Revenue Growth",\n'
        '  "xAxisCategories": ["HY 2025", "HY 2026"],\n'
        '  "yAxisTitle": "US$ Millions",\n'
        '  "series": [{"name": "Revenue", "data": [155.4, 258.0]}],\n'
        '  "chartType": "column",\n'
        '  "sourceDescription": "Dar Global LSE Disclosures"\n'
        "}\n"
        "```"
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.object(LLMService, "get_client", return_value=mock_client):
        chunks = [
            RetrievedContext("1", "https://darglobal.co.uk", "darglobal.co.uk", "Results", "Revenue was 258M", 5.0)
        ]
        answer, chart = await LLMService.generate_response("What is Dar Global's revenue?", chunks)
        assert "66% revenue growth" in answer
        assert chart is not None
        assert chart.title == "HY Revenue Growth"
        assert len(chart.series) == 1
        assert chart.series[0].data == [155.4, 258.0]


@pytest.mark.asyncio
async def test_chat_service_process_user_message(mock_db):
    with patch("app.database.DatabaseManager.get_database", return_value=mock_db), \
         patch("app.services.retrieval_service.RetrievalService.retrieve_relevant_chunks", new_callable=AsyncMock) as mock_ret, \
         patch("app.services.llm_service.LLMService.generate_response", new_callable=AsyncMock) as mock_llm:

        mock_ret.return_value = [
            RetrievedContext("c1", "https://darglobal.co.uk", "darglobal.co.uk", "Dar Global", "Luxury developer", 4.0)
        ]
        mock_llm.return_value = ("Dar Global is a London-listed developer.", None)

        response = await ChatService.process_user_message("session_123", "Who is Dar Global?")
        assert response.role == MessageRole.ASSISTANT
        assert "London-listed developer" in response.content
        assert len(response.citations) == 1
        assert response.citations[0].url == "https://darglobal.co.uk"


@pytest.mark.asyncio
async def test_chat_completions_rest_validation(async_client):
    resp = await async_client.post("/api/chat/completions", json={"message": ""})
    assert resp.status_code in (400, 422)
