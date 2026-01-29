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

import logging
import typing

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from .config import DEFAULT_MAX_TOKENS, LLMConfig
from .openai_base_client import DEFAULT_REASONING, DEFAULT_VERBOSITY, BaseOpenAIClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseOpenAIClient):
    """
    OpenAIClient is a client class for interacting with OpenAI's language models.

    This class extends the BaseOpenAIClient and provides OpenAI-specific implementation
    for creating completions.

    Attributes:
        client (AsyncOpenAI): The OpenAI client used to interact with the API.
        responses_client (AsyncOpenAI | None): An optional separate client for responses.parse() API.
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
        Initialize the OpenAIClient with the provided configuration, cache setting, and client.

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
            # Create a separate client for responses.parse() if a different URL is provided
            if config.responses_url and config.responses_url != config.base_url:
                self.responses_client = AsyncOpenAI(
                    api_key=config.api_key, base_url=config.responses_url
                )
            else:
                self.responses_client = None
        else:
            self.client = client
            self.responses_client = None

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
        """Create a structured completion using OpenAI's beta parse API."""
        # Reasoning models (gpt-5 family) don't support temperature
        is_reasoning_model = (
            model.startswith('gpt-5') or model.startswith('o1') or model.startswith('o3')
        )

        # For Alibaba Cloud, directly use JSON mode instead of responses.parse()
        # because responses.parse() doesn't work properly with Alibaba Cloud
        is_alibaba = self._is_alibaba_provider()
        logger.debug(f'[LLM Debug] _create_structured_completion: is_alibaba={is_alibaba}, client.base_url={self.client.base_url}')
        
        if is_alibaba:
            logger.info('[LLM] Using JSON mode for Alibaba Cloud provider')
            # Alibaba Cloud requires 'json' to be mentioned in messages when using JSON mode
            modified_messages = self._ensure_json_in_messages(messages)
            return await self.client.chat.completions.create(
                model=model,
                messages=modified_messages,
                temperature=temperature if not is_reasoning_model else None,
                max_tokens=max_tokens,
                response_format={'type': 'json_object'},
            )

        # For other providers, try using responses.parse() first (OpenAI's structured output API)
        request_kwargs = {
            'model': model,
            'input': messages,  # type: ignore
            'max_output_tokens': max_tokens,
            'text_format': response_model,  # type: ignore
        }

        temperature_value = temperature if not is_reasoning_model else None
        if temperature_value is not None:
            request_kwargs['temperature'] = temperature_value

        # Only include reasoning and verbosity parameters for reasoning models
        if is_reasoning_model and reasoning is not None:
            request_kwargs['reasoning'] = {'effort': reasoning}  # type: ignore

        if is_reasoning_model and verbosity is not None:
            request_kwargs['text'] = {'verbosity': verbosity}  # type: ignore

        # Use the responses_client if available, otherwise use the main client
        client_for_responses = self.responses_client or self.client

        try:
            response = await client_for_responses.responses.parse(**request_kwargs)
            return response
        except Exception as e:
            # For non-Alibaba providers, still try the fallback
            logger.warning(
                f'[LLM] responses.parse() failed: {e}. '
                'Falling back to chat.completions with JSON format.'
            )
            return await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature_value,
                max_tokens=max_tokens,
                response_format={'type': 'json_object'},
            )

    def _is_alibaba_provider(self) -> bool:
        """Check if the current client is using Alibaba Cloud (Qwen/DashScope)."""
        # Check main client
        base_url = self.client.base_url
        if base_url:
            base_url_str = str(base_url) if not isinstance(base_url, str) else base_url
            if 'dashscope.aliyuncs.com' in base_url_str:
                logger.debug(f'[LLM Debug] Alibaba provider detected in main client: {base_url_str}')
                return True
        
        # Check responses client if it exists
        if self.responses_client:
            responses_base_url = self.responses_client.base_url
            if responses_base_url:
                responses_base_url_str = str(responses_base_url) if not isinstance(responses_base_url, str) else responses_base_url
                if 'dashscope.aliyuncs.com' in responses_base_url_str:
                    logger.debug(f'[LLM Debug] Alibaba provider detected in responses client: {responses_base_url_str}')
                    return True
        
        logger.debug(f'[LLM Debug] Not an Alibaba provider. Main client base_url: {base_url}')
        return False

    def _ensure_json_in_messages(
        self, messages: list[ChatCompletionMessageParam]
    ) -> list[ChatCompletionMessageParam]:
        """
        Ensure messages contain the word 'json' for Alibaba Cloud's JSON mode requirement.

        Alibaba Cloud's API requires that the word 'json' appears somewhere in the messages
        when using response_format={'type': 'json_object'}.
        """
        import copy

        modified_messages = copy.deepcopy(messages)

        # Check if 'json' already exists in any message content
        has_json = False
        for msg in modified_messages:
            content = msg.get('content', '')
            if isinstance(content, str) and 'json' in content.lower():
                has_json = True
                break

        # If not found, add it to the last message
        if not has_json and modified_messages:
            last_msg = modified_messages[-1]
            current_content = last_msg.get('content', '')

            if isinstance(current_content, str):
                # Append JSON instruction
                last_msg['content'] = (
                    current_content
                    + '\n\nIMPORTANT: You must respond with valid JSON format.'
                )
            elif isinstance(current_content, list) and current_content:
                # Handle multimodal content (text + images)
                last_text_item = None
                for item in reversed(current_content):
                    if isinstance(item, dict) and item.get('type') == 'text':
                        last_text_item = item
                        break

                if last_text_item:
                    last_text_item['text'] = (
                        last_text_item.get('text', '')
                        + '\n\nIMPORTANT: You must respond with valid JSON format.'
                    )

        return modified_messages

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
        # Reasoning models (gpt-5 family) don't support temperature
        is_reasoning_model = (
            model.startswith('gpt-5') or model.startswith('o1') or model.startswith('o3')
        )

        # For Alibaba Cloud, ensure 'json' is in messages for JSON mode
        if self._is_alibaba_provider():
            modified_messages = self._ensure_json_in_messages(messages)
        else:
            modified_messages = messages

        return await self.client.chat.completions.create(
            model=model,
            messages=modified_messages,
            temperature=temperature if not is_reasoning_model else None,
            max_tokens=max_tokens,
            response_format={'type': 'json_object'},
        )
