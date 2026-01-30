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

import asyncio
from collections.abc import Iterable
from time import time

from openai import AsyncAzureOpenAI, AsyncOpenAI
from openai.types import EmbeddingModel

from .client import EmbedderClient, EmbedderConfig

DEFAULT_EMBEDDING_MODEL = 'text-embedding-3-small'


class OpenAIEmbedderConfig(EmbedderConfig):
    embedding_model: EmbeddingModel | str = DEFAULT_EMBEDDING_MODEL
    api_key: str | None = None
    base_url: str | None = None
    max_batch_size: int = 2048  # OpenAI's limit is 2048 texts per request
    requests_per_second: float = 50.0  # Default: 50 requests per second (for OpenAI)
    # Note: Qwen Embedding API has stricter rate limits, should be set to 10-20


class OpenAIEmbedder(EmbedderClient):
    """
    OpenAI Embedder Client

    This client supports both AsyncOpenAI and AsyncAzureOpenAI clients.
    """

    def __init__(
        self,
        config: OpenAIEmbedderConfig | None = None,
        client: AsyncOpenAI | AsyncAzureOpenAI | None = None,
    ):
        if config is None:
            config = OpenAIEmbedderConfig()
        self.config = config

        if client is not None:
            self.client = client
        else:
            self.client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

    async def create(
        self, input_data: str | list[str] | Iterable[int] | Iterable[Iterable[int]]
    ) -> list[float]:
        result = await self.client.embeddings.create(
            input=input_data, model=self.config.embedding_model
        )
        return result.data[0].embedding[: self.config.embedding_dim]

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        max_batch_size = self.config.max_batch_size
        requests_per_second = self.config.requests_per_second
        min_interval = 1.0 / requests_per_second if requests_per_second > 0 else 0
        
        # For single batch or no rate limiting needed
        if len(input_data_list) <= max_batch_size:
            result = await self.client.embeddings.create(
                input=input_data_list, model=self.config.embedding_model
            )
            return [embedding.embedding[: self.config.embedding_dim] for embedding in result.data]
        
        # Split into chunks of max_batch_size
        chunks = [
            input_data_list[i:i + max_batch_size]
            for i in range(0, len(input_data_list), max_batch_size)
        ]
        all_embeddings = []
        last_request_time = time()
        
        for i, chunk in enumerate(chunks):
            # Calculate time since last request
            current_time = time()
            time_since_last = current_time - last_request_time
            
            # If we need to wait to respect rate limit
            if time_since_last < min_interval and i > 0:
                wait_time = min_interval - time_since_last
                await asyncio.sleep(wait_time)
            
            # Make the request
            result = await self.client.embeddings.create(
                input=chunk, model=self.config.embedding_model
            )
            chunk_embeddings = [embedding.embedding[: self.config.embedding_dim] for embedding in result.data]
            all_embeddings.extend(chunk_embeddings)
            
            # Update last request time
            last_request_time = time()
        
        return all_embeddings
