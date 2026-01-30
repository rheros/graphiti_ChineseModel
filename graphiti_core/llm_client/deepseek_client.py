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

import typing
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from .config import DEFAULT_MAX_TOKENS, LLMConfig
from .openai_base_client import DEFAULT_REASONING, DEFAULT_VERBOSITY, BaseOpenAIClient


class DeepSeekClient(BaseOpenAIClient):
    """
    DeepSeekClient is a client class for interacting with DeepSeek's language models.

    This class extends the BaseOpenAIClient and provides DeepSeek-specific implementation
    for creating completions.

    Attributes:
        client (AsyncOpenAI): The OpenAI-compatible client used to interact with the API.
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        cache: bool = False,
        client: typing.Any = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        reasoning: str = DEFAULT_REASONING,
        verbosity: str = DEFAULT_VERBOSITY,
    ):
        """
        Initialize the DeepSeekClient with the provided configuration, cache setting, and client.

        Args:
            config (LLMConfig | None): The configuration for the LLM client, including API key, model, base URL, temperature, and max tokens.
            cache (bool): Whether to use caching for responses. Defaults to False.
            client (Any | None): An optional async client instance to use. If not provided, a new AsyncOpenAI client is created.
        """
        super().__init__(config, cache, max_tokens, reasoning, verbosity)

        if config is None:
            config = LLMConfig()

        if client is None:
            self.client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
        else:
            self.client = client

    async def _create_structured_completion(
        self,
        model: str,
        messages: list[ChatCompletionMessageParam],
        temperature: float | None,
        max_tokens: int,
        response_model: type[BaseModel],
        reasoning: str | None = None,
        verbosity: str | None = None,
    ):
        """Create a structured completion using chat completions with JSON format.

        DeepSeek's API is OpenAI-compatible but may not fully support the
        beta responses.parse endpoint. We use the standard chat completions
        endpoint with JSON format instead.
        """
        import json
        import logging
        from pydantic import TypeAdapter

        logger = logging.getLogger(__name__)

        # DeepSeek has a max_tokens limit of 8192 for most models
        # DeepSeek-V3 may support higher limits
        deepseek_max_limit = 8192
        if 'v3' in model.lower():
            deepseek_max_limit = 8192  # Still using 8192 to be safe

        # Cap max_tokens at the provider's limit
        if max_tokens > deepseek_max_limit:
            logger.warning(
                f'DeepSeek max_tokens capped at {deepseek_max_limit} for model {model} (requested {max_tokens})'
            )
            max_tokens = deepseek_max_limit

        # Generate JSON schema from the response model
        schema = TypeAdapter(response_model).json_schema()

        # Add JSON schema instruction to the last message
        enhanced_messages = list(messages)
        if enhanced_messages and enhanced_messages[-1].get('role') == 'user':
            last_message = enhanced_messages[-1]
            content = last_message.get('content', '')
            schema_json = json.dumps(schema, indent=2, ensure_ascii=True)
            instruction = f'\n\nYour response must be valid JSON that matches this schema:\n{schema_json}'
            last_message['content'] = content + instruction

        response = await self.client.chat.completions.create(
            model=model,
            messages=enhanced_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={'type': 'json_object'},
        )

        return response

    async def _create_completion(
        self,
        model: str,
        messages: list[ChatCompletionMessageParam],
        temperature: float | None,
        max_tokens: int,
        response_model: type[BaseModel] | None = None,
        reasoning: str | None = None,
        verbosity: str | None = None,
    ):
        """Create a regular completion with JSON format."""
        import logging

        logger = logging.getLogger(__name__)

        # DeepSeek has a max_tokens limit of 8192 for most models
        # DeepSeek-V3 may support higher limits
        deepseek_max_limit = 8192
        if 'v3' in model.lower():
            deepseek_max_limit = 8192  # Still using 8192 to be safe

        # Cap max_tokens at the provider's limit
        if max_tokens > deepseek_max_limit:
            logger.warning(
                f'DeepSeek max_tokens capped at {deepseek_max_limit} for model {model} (requested {max_tokens})'
            )
            max_tokens = deepseek_max_limit

        # Reasoning models (gpt-5 family) don't support temperature
        is_reasoning_model = (
            model.startswith('gpt-5') or model.startswith('o1') or model.startswith('o3')
        )

        return await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature if not is_reasoning_model else None,
            max_tokens=max_tokens,
            response_format={'type': 'json_object'},
        )