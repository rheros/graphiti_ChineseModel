# Qwen (Tongyi Qianwen) with Neo4j Example

This example demonstrates how to use Graphiti with Alibaba's Qwen language models (via DashScope API) and Neo4j to build a knowledge graph.

## Prerequisites

- Python 3.10+
- Neo4j database (running locally or remotely)
- Qwen API key (get one from [DashScope Platform](https://dashscope.aliyun.com/))

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment Variables

Copy the `.env.example` file to `.env` and fill in your credentials:

```bash
cd examples/qwen
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# Neo4j connection settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Qwen API settings
QWEN_API_KEY=your-api-key-here
QWEN_MODEL=qwen-turbo
QWEN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

**Note**: DashScope API keys typically need to be prefixed with `sk-` in the Authorization header. The QwenClient automatically handles this for you.

### 3. Neo4j Setup

Make sure Neo4j is running and accessible at the URI specified in your `.env` file.

For local development:
- Download and install [Neo4j Desktop](https://neo4j.com/download/)
- Create a new database
- Start the database
- Use the credentials in your `.env` file

## Running the Example

```bash
cd examples/qwen
uv run qwen_neo4j.py
```

## What This Example Does

1. **Initialization**: Sets up connections to Neo4j and Qwen API
2. **Adding Episodes**: Ingests text and JSON data about California politics
3. **Basic Search**: Performs hybrid search combining semantic similarity and BM25 retrieval
4. **Center Node Search**: Reranks results based on graph distance to a specific node
5. **Cleanup**: Properly closes database connections

## Key Concepts

### Qwen Integration

Alibaba's DashScope provides an OpenAI-compatible API for Qwen models, making integration with Graphiti straightforward. The example shows how to configure Graphiti to use Qwen:

```python
# Configure Graphiti to use Qwen
config = {
    'llm': {
        'provider': 'qwen',
        'model': 'qwen-turbo',
        'providers': {
            'qwen': {
                'api_key': os.environ['QWEN_API_KEY'],
                'api_url': os.environ.get('QWEN_API_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
            }
        }
    }
}

# Initialize Graphiti with Qwen configuration
graphiti = Graphiti(
    neo4j_uri,
    neo4j_user,
    neo4j_password,
    llm_config=config
)
```

**Note**: Qwen's API follows the OpenAI Chat Completions format via DashScope's compatible mode, so you can use the same patterns as with OpenAI.

### API Key Format

DashScope API keys typically need the `sk-` prefix. The QwenClient automatically adds this prefix if it's not already present in your API key.

### Available Models

Qwen offers several models you can use with Graphiti:

- `qwen-turbo`: Fast, efficient model for general tasks
- `qwen-plus`: More powerful version with better reasoning
- `qwen-max`: Largest model with best performance
- `qwen-2.5-coder`: Specialized for code generation

### Episodes

Episodes are the primary units of information in Graphiti. They can be:
- **Text**: Raw text content (e.g., transcripts, documents)
- **JSON**: Structured data with key-value pairs

### Hybrid Search

Graphiti combines multiple search strategies:
- **Semantic Search**: Uses embeddings to find semantically similar content
- **BM25**: Keyword-based text retrieval
- **Graph Traversal**: Leverages relationships between entities

## Troubleshooting

### Qwen API Errors

- Verify your API key is correct and has sufficient credits
- Check that the model name is valid (e.g., `qwen-turbo`, `qwen-plus`)
- Ensure your network can access DashScope's API endpoints
- Check API rate limits if you're making many requests

### Neo4j Connection Issues

- Ensure Neo4j is running
- Check firewall settings
- Verify credentials are correct
- Check URI format (should be `bolt://` or `neo4j://`)

## Next Steps

- Explore other search recipes in `graphiti_core/search/search_config_recipes.py`
- Try different Qwen models for specific tasks
- Experiment with custom entity definitions
- Add more episodes to build a larger knowledge graph

## Related Examples

- `examples/quickstart/` - Basic Graphiti usage with OpenAI
- `examples/azure-openai/` - Using Azure OpenAI services
- `examples/deepseek/` - Using DeepSeek models
- `examples/podcast/` - Processing longer content
- `examples/ecommerce/` - Domain-specific knowledge graphs