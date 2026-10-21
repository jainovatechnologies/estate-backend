import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.socket.events import chat_message, chat_join, connect, disconnect
from app.socket.manager import SocketManager


@pytest.mark.asyncio
async def test_socket_lifecycle():
    with patch.object(SocketManager, "register_client") as mock_reg, \
         patch.object(SocketManager, "unregister_client") as mock_unreg:
        await connect("sid_123", {})
        await disconnect("sid_123")
        mock_unreg.assert_called_once_with("sid_123")


@pytest.mark.asyncio
async def test_socket_chat_message_empty():
    with patch.object(SocketManager, "emit_error", new_callable=AsyncMock) as mock_err:
        await chat_message("sid_123", {"session_id": "s1", "message": ""})
        mock_err.assert_called_once()
        assert "empty" in mock_err.call_args[0][1].lower()


@pytest.mark.asyncio
async def test_socket_chat_message_invalid_type():
    with patch.object(SocketManager, "emit_error", new_callable=AsyncMock) as mock_err:
        await chat_message("sid_123", "not a dictionary")
        mock_err.assert_called_once()
