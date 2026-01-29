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

import json
import logging
import typing
from abc import abstractmethod
from typing import Any, ClassVar

import openai
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from ..prompts.models import Message
from .client import LLMClient, get_extraction_language_instruction
from .config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from .errors import RateLimitError, RefusalError

logger = logging.getLogger(__name__)

DEFAULT_MODEL = 'gpt-4.1-mini'
DEFAULT_SMALL_MODEL = 'gpt-4.1-nano'
DEFAULT_REASONING = 'minimal'
DEFAULT_VERBOSITY = 'low'


class BaseOpenAIClient(LLMClient):
    """
    Base client class for OpenAI-compatible APIs (OpenAI and Azure OpenAI).

    This class contains shared logic for both OpenAI and Azure OpenAI clients,
    reducing code duplication while allowing for implementation-specific differences.
    """

    # Class-level constants
    MAX_RETRIES: ClassVar[int] = 2

    def __init__(
        self,
        config: LLMConfig | None = None,
        cache: bool = False,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        reasoning: str | None = DEFAULT_REASONING,
        verbosity: str | None = DEFAULT_VERBOSITY,
    ):
        if cache:
            raise NotImplementedError('Caching is not implemented for OpenAI-based clients')

        if config is None:
            config = LLMConfig()

        super().__init__(config, cache)
        self.max_tokens = max_tokens
        self.reasoning = reasoning
        self.verbosity = verbosity

    @abstractmethod
    async def _create_completion(
        self,
        model: str,
        messages: list[ChatCompletionMessageParam],
        temperature: float | None,
        max_tokens: int,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        """Create a completion using the specific client implementation."""
        pass

    @abstractmethod
    async def _create_structured_completion(
        self,
        model: str,
        messages: list[ChatCompletionMessageParam],
        temperature: float | None,
        max_tokens: int,
        response_model: type[BaseModel],
        reasoning: str | None,
        verbosity: str | None,
    ) -> Any:
        """Create a structured completion using the specific client implementation."""
        pass

    def _convert_messages_to_openai_format(
        self, messages: list[Message]
    ) -> list[ChatCompletionMessageParam]:
        """Convert internal Message format to OpenAI ChatCompletionMessageParam format."""
        openai_messages: list[ChatCompletionMessageParam] = []
        for m in messages:
            m.content = self._clean_input(m.content)
            if m.role == 'user':
                openai_messages.append({'role': 'user', 'content': m.content})
            elif m.role == 'system':
                openai_messages.append({'role': 'system', 'content': m.content})
        return openai_messages

    def _get_model_for_size(self, model_size: ModelSize) -> str:
        """Get the appropriate model name based on the requested size."""
        if model_size == ModelSize.small:
            return self.small_model or DEFAULT_SMALL_MODEL
        else:
            return self.model or DEFAULT_MODEL

    def _handle_structured_response(self, response: Any) -> dict[str, Any]:
        """Handle structured response parsing and validation."""
        # Try to get output_text, if not available, return empty result
        if not hasattr(response, 'output_text'):
            logger.error('[LLM Response] Response object does not have output_text attribute')
            return {'extracted_entities': []}

        response_object = response.output_text

        if response_object:
            # Check if response_object is already a parsed object
            if isinstance(response_object, (list, dict)):
                parsed_result = response_object
                logger.debug(f'[LLM Response] Raw structured response (already parsed): {parsed_result}')
            else:
                # Try to parse as JSON string
                try:
                    parsed_result = json.loads(response_object)
                    logger.debug(f'[LLM Response] Raw parsed structured response: {parsed_result}')
                except (TypeError, json.JSONDecodeError):
                    # If parsing fails, treat as raw value
                    parsed_result = response_object
                    logger.debug(f'[LLM Response] Raw structured response (treated as raw): {parsed_result}')
            
            # Handle list responses by wrapping in appropriate container
            if isinstance(parsed_result, list):
                wrapper_key = self._infer_wrapper_key(parsed_result)
                logger.info(f'[LLM Response] Received list response in structured format, wrapping in {wrapper_key}: {parsed_result[:2]}' + (f'... and {len(parsed_result) - 2} more' if len(parsed_result) > 2 else ''))
                # Convert entity/entity_name fields to name fields
                converted_list = []
                for item in parsed_result:
                    if isinstance(item, dict):
                        # Create a new dict to ensure we don't have entity/entity_name fields
                        new_item = {}
                        for key, value in item.items():
                            if key in ('entity', 'entity_name'):
                                new_item['name'] = value
                            else:
                                new_item[key] = value
                        logger.debug(f'[LLM Response] Converted entity/entity_name field to name field: {new_item}')
                        converted_list.append(new_item)
                    else:
                        converted_list.append(item)
                return {wrapper_key: converted_list}
            
            # Handle {'entities': [...]} format
            if isinstance(parsed_result, dict) and 'entities' in parsed_result and isinstance(parsed_result['entities'], list):
                logger.info(f'[LLM Response] Received entities format in structured format, converting to extracted_entities')
                # Convert entity/entity_name fields to name fields
                converted_list = []
                for item in parsed_result['entities']:
                    if isinstance(item, dict):
                        # Create a new dict to ensure we don't have entity/entity_name fields
                        new_item = {}
                        for key, value in item.items():
                            if key in ('entity', 'entity_name'):
                                new_item['name'] = value
                            else:
                                new_item[key] = value
                        logger.debug(f'[LLM Response] Converted entity/entity_name field to name field: {new_item}')
                        converted_list.append(new_item)
                    else:
                        converted_list.append(item)
                return {'extracted_entities': converted_list}
            
            # Check if extracted_entities exists
            # First check for other known wrapper keys (edges, entity_resolutions, entity_classifications)
            known_wrapper_keys = {'edges', 'entity_resolutions', 'entity_classifications'}
            if isinstance(parsed_result, dict) and any(key in parsed_result for key in known_wrapper_keys):
                logger.debug(f'[LLM Response] Found known wrapper key in structured response, returning as-is')
                return parsed_result
                
            if isinstance(parsed_result, dict) and 'extracted_entities' not in parsed_result:
                # Check if this is a single entity (has entity_type_id or name after conversion)
                # First, convert entity/entity_name field to name if present
                if 'entity' in parsed_result or 'entity_name' in parsed_result:
                    new_item = {}
                    for key, value in parsed_result.items():
                        if key in ('entity', 'entity_name'):
                            new_item['name'] = value
                        else:
                            new_item[key] = value
                    parsed_result = new_item
                    logger.debug(f'[LLM Response] Converted entity/entity_name field to name field: {parsed_result}')

                # Now check if this looks like a single entity
                if 'name' in parsed_result or 'entity_type_id' in parsed_result:
                    logger.info(f'[LLM Response] Received single entity response, wrapping in extracted_entities')
                    return {'extracted_entities': [parsed_result]}
                else:
                    logger.warning(f'[LLM Response] No extracted_entities field found in response: {parsed_result}')
                    # Return empty extracted_entities to avoid validation error
                    return {'extracted_entities': []}
            elif isinstance(parsed_result, dict) and 'extracted_entities' in parsed_result:
                # Convert entity/entity_name fields to name fields in extracted_entities
                if isinstance(parsed_result['extracted_entities'], list):
                    converted_list = []
                    for item in parsed_result['extracted_entities']:
                        if isinstance(item, dict):
                            # Create a new dict to ensure we don't have entity/entity_name fields
                            new_item = {}
                            for key, value in item.items():
                                if key in ('entity', 'entity_name'):
                                    new_item['name'] = value
                                else:
                                    new_item[key] = value
                            logger.debug(f'[LLM Response] Converted entity/entity_name field to name field: {new_item}')
                            converted_list.append(new_item)
                        else:
                            converted_list.append(item)
                    parsed_result['extracted_entities'] = converted_list
            
            # If parsed_result is not a dict, wrap it in extracted_entities
            if not isinstance(parsed_result, dict):
                logger.warning(f'[LLM Response] Received non-dict response: {parsed_result}, wrapping in extracted_entities')
                return {'extracted_entities': []}
            
            return parsed_result
        elif response_object and hasattr(response_object, 'refusal') and response_object.refusal:
            raise RefusalError(response_object.refusal)
        else:
            # Log more details for debugging
            logger.error(f'[LLM Response] Invalid response structure. Type: {type(response_object)}, Has output_text: {hasattr(response_object, "output_text")}, response: {response_object}')
            raise Exception(f'Invalid response from LLM: {response_object}')

    def _infer_wrapper_key(self, items_list: list[dict]) -> str:
        """
        Infer the correct wrapper key based on the structure of list items.
        
        Returns:
            'extracted_entities' for entity extraction responses
            'entity_resolutions' for node deduplication responses
            'items' as fallback for generic list responses
        """
        if not items_list or not isinstance(items_list[0], dict):
            return 'items'
        
        # Check the first item's keys to determine the response type
        first_item = items_list[0]
        keys = set(first_item.keys())
        
        # Node deduplication responses typically have: id, name, duplicate_idx, duplicates
        if 'duplicate_idx' in keys and 'duplicates' in keys:
            return 'entity_resolutions'
        
        # Entity extraction responses typically have: name, entity_type_id
        if 'entity_type_id' in keys:
            return 'extracted_entities'
        
        # Entity classification triples have: uuid, name, entity_type
        if 'uuid' in keys and 'entity_type' in keys:
            return 'entity_classifications'
        
        # Default to extracted_entities for backward compatibility
        return 'extracted_entities'

    def _handle_json_response(self, response: Any) -> dict[str, Any]:
        """Handle JSON response parsing."""
        result = response.choices[0].message.content or '{}'
        parsed_result = json.loads(result)
        logger.debug(f'[LLM Response] Raw parsed JSON response: {parsed_result}')
        
        # Handle list responses by wrapping in appropriate container
        if isinstance(parsed_result, list):
            # Try to infer the correct wrapper field based on the list items
            wrapper_key = self._infer_wrapper_key(parsed_result)
            logger.info(f'[LLM Response] Received list response, wrapping in {wrapper_key}: {parsed_result[:2]}' + (f'... and {len(parsed_result) - 2} more' if len(parsed_result) > 2 else ''))
            # Convert entity/entity_name fields to name fields
            converted_list = []
            for item in parsed_result:
                if isinstance(item, dict):
                    # Create a new dict to ensure we don't have entity/entity_name fields
                    new_item = {}
                    for key, value in item.items():
                        if key in ('entity', 'entity_name'):
                            new_item['name'] = value
                        else:
                            new_item[key] = value
                    logger.debug(f'[LLM Response] Converted entity/entity_name field to name field: {new_item}')
                    converted_list.append(new_item)
                else:
                    converted_list.append(item)
            return {wrapper_key: converted_list}
        
        # Handle {'entities': [...]} format
        if 'entities' in parsed_result and isinstance(parsed_result['entities'], list):
            logger.info(f'[LLM Response] Received entities format, converting to extracted_entities')
            # Convert entity/entity_name fields to name fields
            converted_list = []
            for item in parsed_result['entities']:
                if isinstance(item, dict):
                    # Create a new dict to ensure we don't have entity/entity_name fields
                    new_item = {}
                    for key, value in item.items():
                        if key in ('entity', 'entity_name'):
                            new_item['name'] = value
                        else:
                            new_item[key] = value
                    logger.debug(f'[LLM Response] Converted entity/entity_name field to name field: {new_item}')
                    converted_list.append(new_item)
                else:
                    converted_list.append(item)
            return {'extracted_entities': converted_list}
        
        # Check if extracted_entities exists
        # First check for other known wrapper keys (edges, entity_resolutions, entity_classifications)
        known_wrapper_keys = {'edges', 'entity_resolutions', 'entity_classifications'}
        if any(key in parsed_result for key in known_wrapper_keys):
            logger.debug(f'[LLM Response] Found known wrapper key in response, returning as-is')
            return parsed_result
            
        if 'extracted_entities' not in parsed_result:
            # Check if this is a single entity (has entity_type_id or name after conversion)
            # First, convert entity/entity_name field to name if present
            if 'entity' in parsed_result or 'entity_name' in parsed_result:
                new_item = {}
                for key, value in parsed_result.items():
                    if key in ('entity', 'entity_name'):
                        new_item['name'] = value
                    else:
                        new_item[key] = value
                parsed_result = new_item
                logger.debug(f'[LLM Response] Converted entity/entity_name field to name field: {parsed_result}')

            # Now check if this looks like a single entity
            if 'name' in parsed_result or 'entity_type_id' in parsed_result:
                logger.info(f'[LLM Response] Received single entity response, wrapping in extracted_entities')
                return {'extracted_entities': [parsed_result]}
            else:
                logger.warning(f'[LLM Response] No extracted_entities field found in JSON response: {parsed_result}')
                # Return empty extracted_entities to avoid validation error
                return {'extracted_entities': []}
        else:
            # Convert entity/entity_name fields to name fields in extracted_entities
            if isinstance(parsed_result['extracted_entities'], list):
                converted_list = []
                for item in parsed_result['extracted_entities']:
                    if isinstance(item, dict):
                        # Create a new dict to ensure we don't have entity/entity_name fields
                        new_item = {}
                        for key, value in item.items():
                            if key in ('entity', 'entity_name'):
                                new_item['name'] = value
                            else:
                                new_item[key] = value
                        logger.debug(f'[LLM Response] Converted entity/entity_name field to name field: {new_item}')
                        converted_list.append(new_item)
                    else:
                        converted_list.append(item)
                parsed_result['extracted_entities'] = converted_list
        
        return parsed_result

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, Any]:
        """Generate a response using the appropriate client implementation."""
        openai_messages = self._convert_messages_to_openai_format(messages)
        model = self._get_model_for_size(model_size)

        try:
            if response_model:
                response = await self._create_structured_completion(
                    model=model,
                    messages=openai_messages,
                    temperature=self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                    response_model=response_model,
                    reasoning=self.reasoning,
                    verbosity=self.verbosity,
                )
                # Check if response has output_text attribute (responses.parse() format)
                # If not, it's a chat.completions response (JSON format)
                if hasattr(response, 'output_text'):
                    return self._handle_structured_response(response)
                else:
                    return self._handle_json_response(response)
            else:
                response = await self._create_completion(
                    model=model,
                    messages=openai_messages,
                    temperature=self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                )
                return self._handle_json_response(response)

        except openai.LengthFinishReasonError as e:
            raise Exception(f'Output length exceeded max tokens {self.max_tokens}: {e}') from e
        except openai.RateLimitError as e:
            raise RateLimitError from e
        except openai.AuthenticationError as e:
            logger.error(
                f'OpenAI Authentication Error: {e}. Please verify your API key is correct.'
            )
            raise
        except Exception as e:
            # Provide more context for connection errors
            error_msg = str(e)
            if 'Connection error' in error_msg or 'connection' in error_msg.lower():
                logger.error(
                    f'Connection error communicating with OpenAI API. Please check your network connection and API key. Error: {e}'
                )
            else:
                logger.error(f'Error in generating LLM response: {e}')
            raise

    async def generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int | None = None,
        model_size: ModelSize = ModelSize.medium,
        group_id: str | None = None,
        prompt_name: str | None = None,
    ) -> dict[str, typing.Any]:
        """Generate a response with retry logic and error handling."""
        if max_tokens is None:
            max_tokens = self.max_tokens

        # Add multilingual extraction instructions
        messages[0].content += get_extraction_language_instruction(group_id)

        # Wrap entire operation in tracing span
        with self.tracer.start_span('llm.generate') as span:
            attributes = {
                'llm.provider': 'openai',
                'model.size': model_size.value,
                'max_tokens': max_tokens,
            }
            if prompt_name:
                attributes['prompt.name'] = prompt_name
            span.add_attributes(attributes)

            retry_count = 0
            last_error = None

            while retry_count <= self.MAX_RETRIES:
                try:
                    response = await self._generate_response(
                        messages, response_model, max_tokens, model_size
                    )
                    return response
                except (RateLimitError, RefusalError):
                    # These errors should not trigger retries
                    span.set_status('error', str(last_error))
                    raise
                except (
                    openai.APITimeoutError,
                    openai.APIConnectionError,
                    openai.InternalServerError,
                ):
                    # Let OpenAI's client handle these retries
                    span.set_status('error', str(last_error))
                    raise
                except Exception as e:
                    last_error = e

                    # Don't retry if we've hit the max retries
                    if retry_count >= self.MAX_RETRIES:
                        logger.error(f'Max retries ({self.MAX_RETRIES}) exceeded. Last error: {e}')
                        span.set_status('error', str(e))
                        span.record_exception(e)
                        raise

                    retry_count += 1

                    # Construct a detailed error message for the LLM
                    error_context = (
                        f'The previous response attempt was invalid. '
                        f'Error type: {e.__class__.__name__}. '
                        f'Error details: {str(e)}. '
                        f'Please try again with a valid response, ensuring the output matches '
                        f'the expected format and constraints.'
                    )

                    error_message = Message(role='user', content=error_context)
                    messages.append(error_message)
                    logger.warning(
                        f'Retrying after application error (attempt {retry_count}/{self.MAX_RETRIES}): {e}'
                    )

            # If we somehow get here, raise the last error
            span.set_status('error', str(last_error))
            raise last_error or Exception('Max retries exceeded with no specific error')
