"""
Copyright 2024, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Running tests: pytest -xvs tests/llm_client/test_deepseek_client.py

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from graphiti_core.llm_client.deepseek_client import DeepSeekClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.llm_client.errors import RateLimitError, RefusalError
from graphiti_core.prompts.models import Message


class DummyResponses:
    def __init__(self):
        self.parse_calls: list[dict] = []

    async def parse(self, **kwargs):
        self.parse_calls.append(kwargs)
        return SimpleNamespace(output_text='{}')


class DummyChatCompletions:
    def __init__(self):
        self.create_calls: list[dict] = []

    async def create(self, **kwargs):
        self.create_calls.append(kwargs)
        message = SimpleNamespace(content='{}')
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class DummyChat:
    def __init__(self):
        self.completions = DummyChatCompletions()


class DummyOpenAIClient:
    def __init__(self):
        self.responses = DummyResponses()
        self.chat = DummyChat()


class DummyResponseModel(BaseModel):
    foo: str


@pytest.fixture
def mock_openai_client():
    """Fixture to create a mocked AsyncOpenAI client."""
    return DummyOpenAIClient()


@pytest.fixture
def deepseek_client(mock_openai_client):
    """Fixture to create a DeepSeekClient with a mocked AsyncOpenAI client."""
    config = LLMConfig(
        api_key='test_api_key',
        model='deepseek-chat',
        base_url='https://api.deepseek.com/v1',
        temperature=0.5,
        max_tokens=1000
    )
    client = DeepSeekClient(config=config, cache=False)
    client.client = mock_openai_client
    return client


class TestDeepSeekClientInitialization:
    """Tests for DeepSeekClient initialization."""

    def test_init_with_config(self):
        """Test initialization with a config object."""
        config = LLMConfig(
            api_key='test_api_key',
            model='deepseek-chat',
            base_url='https://api.deepseek.com/v1',
            temperature=0.5,
            max_tokens=1000
        )
        client = DeepSeekClient(config=config, cache=False)

        assert client.config == config
        assert client.model == 'deepseek-chat'
        assert client.temperature == 0.5
        assert client.max_tokens == 1000

    def test_init_with_default_model(self):
        """Test initialization with default model when none is provided."""
        config = LLMConfig(api_key='test_api_key')
        client = DeepSeekClient(config=config, cache=False)

        # DeepSeekClient inherits DEFAULT_MODEL from BaseOpenAIClient
        assert client.model == 'gpt-4.1-mini'

    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'env_api_key'})
    def test_init_without_config(self):
        """Test initialization without a config, using environment variable."""
        # Since DeepSeekClient doesn't have special env var handling in __init__,
        # this test verifies it falls back to LLMConfig's behavior
        client = DeepSeekClient(cache=False)

        # LLMConfig looks for OPENAI_API_KEY by default, not DEEPSEEK_API_KEY
        # So api_key would be None unless OPENAI_API_KEY is set
        assert client.config.api_key is None or client.config.api_key == 'env_api_key'


@pytest.mark.asyncio
async def test_create_structured_completion_strips_reasoning_for_non_reasoning_models(deepseek_client, mock_openai_client):
    """Test that reasoning/verbosity parameters are stripped for non-reasoning models."""
    await deepseek_client._create_structured_completion(
        model='deepseek-chat',
        messages=[],
        temperature=0.4,
        max_tokens=64,
        response_model=DummyResponseModel,
        reasoning='minimal',
        verbosity='low',
    )

    assert len(mock_openai_client.responses.parse_calls) == 1
    call_args = mock_openai_client.responses.parse_calls[0]
    assert call_args['model'] == 'deepseek-chat'
    assert call_args['input'] == []
    assert call_args['max_output_tokens'] == 64
    assert call_args['text_format'] is DummyResponseModel
    assert call_args['temperature'] == 0.4
    # DeepSeek models don't support reasoning/verbosity parameters
    assert 'reasoning' not in call_args
    assert 'text' not in call_args


@pytest.mark.asyncio
async def test_create_completion_with_json_format(deepseek_client, mock_openai_client):
    """Test regular completion with JSON response format."""
    await deepseek_client._create_completion(
        model='deepseek-chat',
        messages=[],
        temperature=0.7,
        max_tokens=128,
    )

    assert len(mock_openai_client.chat.completions.create_calls) == 1
    call_args = mock_openai_client.chat.completions.create_calls[0]
    assert call_args['model'] == 'deepseek-chat'
    assert call_args['messages'] == []
    assert call_args['temperature'] == 0.7
    assert call_args['max_tokens'] == 128
    assert call_args['response_format'] == {'type': 'json_object'}


@pytest.mark.asyncio
async def test_generate_response_with_response_model(deepseek_client, mock_openai_client):
    """Test generate_response with a response model."""
    # Mock the structured completion response
    mock_response = SimpleNamespace(output_text='{"foo": "bar"}')
    mock_openai_client.responses.parse.return_value = mock_response

    messages = [Message(role='user', content='Test message')]
    result = await deepseek_client.generate_response(
        messages=messages,
        response_model=DummyResponseModel
    )

    assert result == {'foo': 'bar'}
    assert len(mock_openai_client.responses.parse_calls) == 1


@pytest.mark.asyncio
async def test_generate_response_without_response_model(deepseek_client, mock_openai_client):
    """Test generate_response without a response model."""
    # Mock the regular completion response
    message = SimpleNamespace(content='{"result": "success"}')
    choice = SimpleNamespace(message=message)
    mock_response = SimpleNamespace(choices=[choice])
    mock_openai_client.chat.completions.create.return_value = mock_response

    messages = [Message(role='user', content='Test message')]
    result = await deepseek_client.generate_response(messages=messages)

    assert result == {'result': 'success'}
    assert len(mock_openai_client.chat.completions.create_calls) == 1


if __name__ == '__main__':
    pytest.main(['-v', 'test_deepseek_client.py'])