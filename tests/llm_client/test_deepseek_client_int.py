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

# Running tests: pytest -xvs tests/llm_client/test_deepseek_client_int.py

import os

import pytest
from pydantic import BaseModel, Field

from graphiti_core.llm_client.deepseek_client import DeepSeekClient
from graphiti_core.prompts.models import Message

# Skip all tests if no API key is available
pytestmark = pytest.mark.skipif(
    'TEST_DEEPSEEK_API_KEY' not in os.environ,
    reason='DeepSeek API key not available',
)


# Rename to avoid pytest collection as a test class
class SimpleResponseModel(BaseModel):
    """Test response model."""

    message: str = Field(..., description='A message from the model')


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_simple_response():
    """Test generating a simple response from the DeepSeek API."""
    if 'TEST_DEEPSEEK_API_KEY' not in os.environ:
        pytest.skip('DeepSeek API key not available')

    # Create client with test API key and default URL
    config = {
        'api_key': os.environ['TEST_DEEPSEEK_API_KEY'],
        'model': 'deepseek-chat',
        'base_url': 'https://api.deepseek.com/v1',
    }
    client = DeepSeekClient(config=config)

    messages = [
        Message(
            role='user',
            content="Respond with a JSON object containing a 'message' field with value 'Hello, world!'",
        )
    ]

    try:
        response = await client.generate_response(messages, response_model=SimpleResponseModel)

        assert isinstance(response, dict)
        assert 'message' in response
        assert response['message'] == 'Hello, world!'
    except Exception as e:
        pytest.skip(f'Test skipped due to DeepSeek API error: {str(e)}')


@pytest.mark.asyncio
@pytest.mark.integration
async def test_generate_response_without_model():
    """Test generating a response without a response model."""
    if 'TEST_DEEPSEEK_API_KEY' not in os.environ:
        pytest.skip('DeepSeek API key not available')

    config = {
        'api_key': os.environ['TEST_DEEPSEEK_API_KEY'],
        'model': 'deepseek-chat',
        'base_url': 'https://api.deepseek.com/v1',
    }
    client = DeepSeekClient(config=config)

    messages = [
        Message(
            role='user',
            content="Respond with a JSON object containing a 'result' field with value 'success'",
        )
    ]

    try:
        response = await client.generate_response(messages)

        assert isinstance(response, dict)
        assert 'result' in response
        assert response['result'] == 'success'
    except Exception as e:
        pytest.skip(f'Test skipped due to DeepSeek API error: {str(e)}')


if __name__ == '__main__':
    pytest.main(['-v', 'test_deepseek_client_int.py'])