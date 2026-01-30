# DeepSeek with Neo4j Example

This example demonstrates how to use Graphiti with DeepSeek's language models and Neo4j to build a knowledge graph.

## Prerequisites

- Python 3.10+
- Neo4j database (running locally or remotely)
- DeepSeek API key (get one from [DeepSeek Platform](https://platform.deepseek.com/))

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment Variables

Copy the `.env.example` file to `.env` and fill in your credentials:

```bash
cd examples/deepseek
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# Neo4j connection settings
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# DeepSeek API settings
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_URL=https://api.deepseek.com/v1
```

### 3. Neo4j Setup

Make sure Neo4j is running and accessible at the URI specified in your `.env` file.

For local development:
- Download and install [Neo4j Desktop](https://neo4j.com/download/)
- Create a new database
- Start the database
- Use the credentials in your `.env` file

## Running the Example

```bash
cd examples/deepseek
uv run deepseek_neo4j.py
```

## What This Example Does

1. **Initialization**: Sets up connections to Neo4j and DeepSeek API
2. **Adding Episodes**: Ingests text and JSON data about California politics
3. **Basic Search**: Performs hybrid search combining semantic similarity and BM25 retrieval
4. **Center Node Search**: Reranks results based on graph distance to a specific node
5. **Cleanup**: Properly closes database connections

## Key Concepts

### DeepSeek Integration

DeepSeek provides an OpenAI-compatible API, making it easy to integrate with Graphiti. The example shows how to configure Graphiti to use DeepSeek:

```python
# Configure Graphiti to use DeepSeek
config = {
    'llm': {
        'provider': 'deepseek',
        'model': 'deepseek-chat',
        'providers': {
            'deepseek': {
                'api_key': os.environ['DEEPSEEK_API_KEY'],
                'api_url': os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
            }
        }
    }
}

# Initialize Graphiti with DeepSeek configuration
graphiti = Graphiti(
    neo4j_uri,
    neo4j_user,
    neo4j_password,
    llm_config=config
)
```

**Note**: DeepSeek's API follows the OpenAI Chat Completions format, so you can use the same patterns as with OpenAI.

### Available Models

DeepSeek offers several models you can use with Graphiti:

- `deepseek-chat`: General purpose chat model (recommended)
- `deepseek-coder`: Code generation and understanding
- `deepseek-math`: Mathematical reasoning

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

### DeepSeek API Errors

- Verify your API key is correct and has sufficient credits
- Check that the model name is valid
- Ensure your network can access DeepSeek's API endpoints
- Check API rate limits if you're making many requests

### Neo4j Connection Issues

- Ensure Neo4j is running
- Check firewall settings
- Verify credentials are correct
- Check URI format (should be `bolt://` or `neo4j://`)

## Next Steps

- Explore other search recipes in `graphiti_core/search/search_config_recipes.py`
- Try different DeepSeek models for specific tasks
- Experiment with custom entity definitions
- Add more episodes to build a larger knowledge graph

## Related Examples

- `examples/quickstart/` - Basic Graphiti usage with OpenAI
- `examples/azure-openai/` - Using Azure OpenAI services
- `examples/qwen/` - Using Alibaba's Qwen models
- `examples/podcast/` - Processing longer content
- `examples/ecommerce/` - Domain-specific knowledge graphs