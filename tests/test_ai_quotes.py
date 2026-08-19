import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_quotes import generate_ai_message


def _fake_response(text):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


def test_returns_none_with_no_api_key():
    assert generate_ai_message("") is None
    assert generate_ai_message(None) is None


@patch("anthropic.Anthropic")
def test_successful_generation_parses_json(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response(
        '{"intro": "For today:", "text": "Small steps still move you forward.", '
        '"author": "Unknown", "reflection": "You do not have to rush this."}'
    )
    mock_anthropic_cls.return_value = mock_client

    result = generate_ai_message("fake-key")
    assert result is not None
    assert result["text"] == "Small steps still move you forward."
    assert result["reflection"] == "You do not have to rush this."


@patch("anthropic.Anthropic")
def test_strips_markdown_fences(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response(
        '```json\n{"intro": "Hi", "text": "Quote text.", "author": "Unknown", "reflection": "Reflection text."}\n```'
    )
    mock_anthropic_cls.return_value = mock_client

    result = generate_ai_message("fake-key")
    assert result is not None
    assert result["text"] == "Quote text."


@patch("anthropic.Anthropic")
def test_returns_none_on_malformed_json(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response("not valid json at all")
    mock_anthropic_cls.return_value = mock_client

    assert generate_ai_message("fake-key") is None


@patch("anthropic.Anthropic")
def test_returns_none_on_missing_required_fields(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response('{"intro": "Hi"}')
    mock_anthropic_cls.return_value = mock_client

    assert generate_ai_message("fake-key") is None


@patch("anthropic.Anthropic")
def test_returns_none_on_api_exception(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = RuntimeError("network error")
    mock_anthropic_cls.return_value = mock_client

    assert generate_ai_message("fake-key") is None


@patch("anthropic.Anthropic")
def test_missing_author_defaults_to_unknown(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response(
        '{"intro": "Hi", "text": "Quote.", "reflection": "Reflection."}'
    )
    mock_anthropic_cls.return_value = mock_client

    result = generate_ai_message("fake-key")
    assert result["author"] == "Unknown"
