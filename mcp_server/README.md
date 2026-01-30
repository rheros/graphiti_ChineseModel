# Graphiti MCP Server

Graphiti is a framework for building and querying temporally-aware knowledge graphs, specifically tailored for AI agents
operating in dynamic environments. Unlike traditional retrieval-augmented generation (RAG) methods, Graphiti
continuously integrates user interactions, structured and unstructured enterprise data, and external information into a
coherent, queryable graph. The framework supports incremental data updates, efficient retrieval, and precise historical
queries without requiring complete graph recomputation, making it suitable for developing interactive, context-aware AI
applications.

This is an experimental Model Context Protocol (MCP) server implementation for Graphiti. The MCP server exposes
Graphiti's key functionality through the MCP protocol, allowing AI assistants to interact with Graphiti's knowledge
graph capabilities.

## 国内大模型快速启动 (Chinese LLM Providers Quick Start)
本功能是由 AI 完全开发完成，本文档也是由 AI 生成，基本写入读取我自己已经测试了，确实可用
本仓库没有使用fork，因为 AI 改动的地方比较多，
原库的地址为：https://github.com/getzep/graphiti

* deepseek 的chat 大模型可以使用
* embedder deepseek 的没有，默认就使用了 千问的
* 千问的 大模型和 embedder 是正常使用的
* 我链接的数据库是 neo4j
### 环境准备

```bash
# 克隆仓库（国内大模型定制版）
git clone git@github.com:rheros/graphiti_ChineseModel.git
cd graphiti_ChineseModel/mcp_server

# 安装依赖（使用uv）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 或直接使用pip
pip install -r requirements.txt
```

### 配置国内大模型

复制环境配置模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置您要使用的国内大模型：

#### 使用 DeepSeek
```bash
# LLM配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat

# Embedding配置（建议同时使用）
EMBEDDER_PROVIDER=qwen
QWEN_API_KEY=sk-your-qwen-api-key
```

#### 使用 Qwen (通义千问) - 默认推荐
```bash
# LLM配置（默认使用最新qwen3-max模型）
LLM_PROVIDER=qwen
QWEN_API_KEY=sk-your-qwen-api-key
QWEN_MODEL=qwen3-max-2026-01-23

# Embedding配置
EMBEDDER_PROVIDER=qwen
QWEN_API_KEY=sk-your-qwen-api-key
```

### 启动命令

#### 方式一：使用Docker（推荐）
```bash
# 使用FalkorDB（默认）
docker compose up

# 或使用Neo4j
docker compose -f docker/docker-compose-neo4j.yml up
```

#### 方式二：本地运行（需单独安装数据库）

**基本启动命令**：
```bash
# 安装Neo4j或FalkorDB后运行
python -m mcp_server.src.graphiti_mcp_server
```

**指定配置参数启动**：
```bash
# 默认启动（使用Qwen qwen3-max-2026-01-23 + text-embedding-v3）
python -m mcp_server.src.graphiti_mcp_server

# 使用DeepSeek + Qwen组合
python -m mcp_server.src.graphiti_mcp_server \
  --llm-provider deepseek \
  --llm-model deepseek-chat \
  --embedder-provider qwen \
  --embedder-model text-embedding-v3

# 使用Qwen全栈（指定模型）
python -m mcp_server.src.graphiti_mcp_server \
  --llm-provider qwen \
  --llm-model qwen3-max-2026-01-23 \
  --embedder-provider qwen \
  --embedder-model text-embedding-v3

# 指定数据库和端口
python -m mcp_server.src.graphiti_mcp_server \
  --database-provider neo4j \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-user neo4j \
  --neo4j-password your-password \
  --port 8000
```

**所有可用的启动参数**：
```bash
# 基础配置
--llm-provider          # LLM提供商: openai, deepseek, qwen, anthropic, gemini, groq, azure_openai (默认: qwen)
--llm-model            # LLM模型名称 (默认: qwen3-max-2026-01-23 或根据提供商自动选择)
--embedder-provider     # Embedding提供商: openai, qwen, gemini, voyage (默认: openai)
--embedder-model       # Embedding模型名称 (默认: text-embedding-3-small 或根据提供商自动选择)
--port                 # 服务端口 (默认: 8000)
--host                 # 服务主机 (默认: 0.0.0.0)

# 数据库配置
--database-provider    # 数据库: neo4j, falkordb (默认: falkordb)
--neo4j-uri           # Neo4j连接地址
--neo4j-user          # Neo4j用户名
--neo4j-password      # Neo4j密码
--falkordb-uri        # FalkorDB连接地址
--falkordb-password   # FalkorDB密码

# 高级配置
--semaphore-limit     # 并发限制 (默认: 10)
--group-id            # 默认group_id
--transport           # 传输方式: http, stdio (默认: http)
```

**默认使用的模型**：
- **LLM**：如果未指定，默认使用 `qwen3-max-2026-01-23` (Qwen通义千问)
- **Embedding**：如果未指定，默认使用 `text-embedding-v3` (Qwen通义千问)
- **DeepSeek用户**：自动使用 `deepseek-chat` 作为主模型，`deepseek-coder` 作为小模型
- **Qwen用户**：自动使用 `qwen-turbo` 作为小模型，主模型默认使用 `qwen3-max-2026-01-23`

### MCP客户端配置示例


#### CodeBuddy配置
在CodeBuddy的MCP设置中添加：
```json
{
  "mcpServers": {
    "graphiti": {
      "url": "http://localhost:8000/mcp/",
      "description": "Graphiti知识图谱 - 默认使用Qwen qwen3-max-2026-01-23"
    }
  }
}
```

### AI助手智能使用指南（推荐Skill方式）

为了让AI助手（如CodeBuddy）能够智能地自动使用Graphiti知识图谱，我们推荐使用Skill方式配置。

#### 快速配置方法（推荐）

**加载Graphiti MCP使用Skill：**

```bash
# 在CodeBuddy中加载Skill
Load skill: c:\Users\TU\Documents\WorkingSpace\Graphiti\mcp_server\graphiti-mcp-usage
```

加载Skill后，AI助手将自动：
- ✅ 识别有价值的信息并存储到知识图谱
- ✅ 需要时自动检索历史信息
- ✅ 提供个性化的连续对话体验
- ✅ 记住用户偏好、学习笔记、项目信息
- ✅ 基于历史信息提供智能建议

#### Skill包含内容

Skill目录：`graphiti-mcp-usage/`
- **SKILL.md** - 主技能文件
- **references/system-prompt-zh.md** - 详细使用说明
- **README.md** - Skill使用指南

#### 使用效果

配置后，AI助手能够智能地进行以下操作：

**自动存储示例：**
```
用户："今天学习了Python的装饰器，很有用"

AI自动执行：
✓ 已将Python装饰器学习笔记保存到知识图谱
（自动添加标签：Procedure，智能分类）
```

**自动检索示例：**
```
用户："我之前说的那个Python知识点是什么？"

AI自动执行：
→ 搜索知识图谱中的Python相关内容
→ 找到之前的学习记录
✓ 回复："根据你的知识图谱记录，你之前学习了Python装饰器..."
```

**个性化建议示例：**
```
用户："我想学一个新的Python框架，有什么推荐？"

AI自动执行：
→ 分析你之前的学习记录
→ 了解你的技术偏好
✓ 回复："根据你之前的学习记录，你已经掌握了FastAPI，推荐你学习..."
```

#### 与传统配置方式的对比

| 特性 | 加载Skill（推荐） | 配置System Prompt |
|------|-------------------|-------------------|
| 安装 | ✅ 一行命令完成 | ❌ 需要复制粘贴大量文本 |
| 更新 | ✅ 重新加载即可 | ❌ 需要手动更新配置 |
| 维护 | ✅ 集中维护 | ❌ 分散在各配置中 |
| 可分享性 | ✅ 易于分享和复用 | ❌ 难以分享 |
| 加载时机 | ✅ 按需加载，节省资源 | ❌ 始终占用上下文 |

#### 备用方案：手动配置System Prompt

如果AI助手不支持Skill加载，可以手动配置System Prompt。详情查看：[SYSTEM_PROMPT.md](./SYSTEM_PROMPT.md)

**注意**：手动配置需要处理JSON转义问题。

## Features

1. **复制System Prompt模板**：
   ```bash
   cp SYSTEM_PROMPT.md your_system_prompt.txt
   ```

2. **在AI助手中配置**：
   - 将`SYSTEM_PROMPT.md`的内容添加到AI助手的System Prompt中
   - 启用`graphiti` MCP工具

#### 配置示例

##### CodeBuddy配置
在CodeBuddy设置中添加自定义System Prompt：
```json
{
  "systemPrompts": {
    "graphiti_auto_mode": {
      "content": "[将SYSTEM_PROMPT.md的内容粘贴到这里]",
      "enabledTools": ["graphiti"],
      "autoInvoke": true
    }
  }
}
```

##### Claude Desktop配置
在Claude Desktop的配置文件中添加：
```json
{
  "mcpServers": {
    "graphiti": {
      "command": "python",
      "args": ["-m", "mcp_server.src.graphiti_mcp_server"],
      "env": {
        "LLM_PROVIDER": "qwen",
        "QWEN_API_KEY": "sk-your-key",
        "EMBEDDER_PROVIDER": "qwen"
      }
    }
  },
  "systemPrompts": ["[将SYSTEM_PROMPT.md的内容粘贴到这里]"]
}
```

#### System Prompt说明

完整的System Prompt配置指南请查看：[SYSTEM_PROMPT.md](./SYSTEM_PROMPT.md)

该System Prompt包含：
- 🤖 **自动存储策略**：AI何时应该自动保存信息到知识图谱
- 🔍 **自动检索策略**：AI何时应该搜索知识图谱中的历史信息
- 💬 **交互模式**：支持完全自动、触发词、确认三种模式
- 📝 **存储示例**：具体的使用示例和最佳实践
- 🎛️ **配置参数**：完整的配置参数说明

#### 使用效果

配置System Prompt后，AI助手将能够：
- ✅ 自动识别有价值的信息并存储
- ✅ 在需要时自动检索历史信息
- ✅ 提供个性化的连续对话体验
- ✅ 记住用户偏好、学习笔记、项目信息
- ✅ 基于历史信息提供智能建议

#### 重要提示：JSON转义处理

**问题**：SYSTEM_PROMPT.md中包含大量双引号，直接复制到JSON配置会导致解析错误。

**解决方案**：

1. **使用预转义的JSON文件（推荐）**
   ```bash
   # 我们已经为你准备了转义好的JSON配置文件
   config/system-prompt.json
   ```
   直接复制该文件内容到你的AI助手配置中即可。

2. **手动转义方法**
   如果需要手动复制SYSTEM_PROMPT.md的内容，请将所有双引号替换为转义形式：
   -  `"`  →  `\"`
   -  例如：`"我喜欢Python"` → `\"我喜欢Python\"`

   可以使用工具自动转义：
   ```python
   import json
   with open('SYSTEM_PROMPT.md', 'r', encoding='utf-8') as f:
       content = f.read()
   escaped_content = json.dumps(content)
   ```

3. **在线转义工具**
   使用在线JSON转义工具：
   - https://www.freeformatter.com/json-escape.html
   - https://www.jsonescape.com/

## Features

The Graphiti MCP server provides comprehensive knowledge graph capabilities:

- **Episode Management**: Add, retrieve, and delete episodes (text, messages, or JSON data)
- **Entity Management**: Search and manage entity nodes and relationships in the knowledge graph
- **Search Capabilities**: Search for facts (edges) and node summaries using semantic and hybrid search
- **Group Management**: Organize and manage groups of related data with group_id filtering
- **Graph Maintenance**: Clear the graph and rebuild indices
- **Graph Database Support**: Multiple backend options including FalkorDB (default) and Neo4j
- **Multiple LLM Providers**: Support for OpenAI, Anthropic, Gemini, Groq, Azure OpenAI, DeepSeek, and Qwen
- **Multiple Embedding Providers**: Support for OpenAI, Voyage, Sentence Transformers, and Gemini embeddings
- **Rich Entity Types**: Built-in entity types including Preferences, Requirements, Procedures, Locations, Events, Organizations, Documents, and more for structured knowledge extraction
- **HTTP Transport**: Default HTTP transport with MCP endpoint at `/mcp/` for broad client compatibility
- **Queue-based Processing**: Asynchronous episode processing with configurable concurrency limits

## Quick Start

### Clone the Graphiti GitHub repo

```bash
git clone https://github.com/getzep/graphiti.git
```

or

```bash
gh repo clone getzep/graphiti
```

### For Claude Desktop and other `stdio` only clients

1. Note the full path to this directory.

```
cd graphiti && pwd
```

2. Install the [Graphiti prerequisites](#prerequisites).

3. Configure Claude, Cursor, or other MCP client to use [Graphiti with a `stdio` transport](#integrating-with-mcp-clients). See the client documentation on where to find their MCP configuration files.

### For Cursor and other HTTP-enabled clients

1. Change directory to the `mcp_server` directory

`cd graphiti/mcp_server`

2. Start the combined FalkorDB + MCP server using Docker Compose (recommended)

```bash
docker compose up
```

This starts both FalkorDB and the MCP server in a single container.

**Alternative**: Run with separate containers using Neo4j:
```bash
docker compose -f docker/docker-compose-neo4j.yml up
```

4. Point your MCP client to `http://localhost:8000/mcp/`

## Installation

### Prerequisites

1. Docker and Docker Compose (for the default FalkorDB setup)
2. OpenAI API key for LLM operations (or API keys for other supported LLM providers)
3. (Optional) Python 3.10+ if running the MCP server standalone with an external FalkorDB instance

### Setup

1. Clone the repository and navigate to the mcp_server directory
2. Use `uv` to create a virtual environment and install dependencies:

```bash
# Install uv if you don't have it already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and install dependencies in one step
uv sync

# Optional: Install additional LLM providers (anthropic, gemini, groq, voyage, sentence-transformers)
uv sync --extra providers
```

## Configuration

The server can be configured using a `config.yaml` file, environment variables, or command-line arguments (in order of precedence).

### Default Configuration

The MCP server comes with sensible defaults:
- **Transport**: HTTP (accessible at `http://localhost:8000/mcp/`)
- **Database**: FalkorDB (combined in single container with MCP server)
- **LLM**: OpenAI with model gpt-5-mini
- **Embedder**: OpenAI text-embedding-3-small

### Database Configuration

#### FalkorDB (Default)

FalkorDB is a Redis-based graph database that comes bundled with the MCP server in a single Docker container. This is the default and recommended setup.

```yaml
database:
  provider: "falkordb"  # Default
  providers:
    falkordb:
      uri: "redis://localhost:6379"
      password: ""  # Optional
      database: "default_db"  # Optional
```

#### Neo4j

For production use or when you need a full-featured graph database, Neo4j is recommended:

```yaml
database:
  provider: "neo4j"
  providers:
    neo4j:
      uri: "bolt://localhost:7687"
      username: "neo4j"
      password: "your_password"
      database: "neo4j"  # Optional, defaults to "neo4j"
```

#### FalkorDB

FalkorDB is another graph database option based on Redis:

```yaml
database:
  provider: "falkordb"
  providers:
    falkordb:
      uri: "redis://localhost:6379"
      password: ""  # Optional
      database: "default_db"  # Optional
```

### Configuration File (config.yaml)

The server supports multiple LLM providers (OpenAI, Anthropic, Gemini, Groq, DeepSeek, Qwen) and embedders. Edit `config.yaml` to configure:

```yaml
server:
  transport: "http"  # Default. Options: stdio, http

llm:
  provider: "openai"  # or "anthropic", "gemini", "groq", "azure_openai", "deepseek", "qwen"
  model: "gpt-4.1"  # Default model

database:
  provider: "falkordb"  # Default. Options: "falkordb", "neo4j"
```

### Using Ollama for Local LLM

To use Ollama with the MCP server, configure it as an OpenAI-compatible endpoint:

```yaml
llm:
  provider: "openai"
  model: "gpt-oss:120b"  # or your preferred Ollama model
  api_base: "http://localhost:11434/v1"
  api_key: "ollama"  # dummy key required

embedder:
  provider: "sentence_transformers"  # recommended for local setup
  model: "all-MiniLM-L6-v2"
```

Make sure Ollama is running locally with: `ollama serve`

### Entity Types

Graphiti MCP Server includes built-in entity types for structured knowledge extraction. These entity types are always enabled and configured via the `entity_types` section in your `config.yaml`:

**Available Entity Types:**

- **Preference**: User preferences, choices, opinions, or selections (prioritized for user-specific information)
- **Requirement**: Specific needs, features, or functionality that must be fulfilled
- **Procedure**: Standard operating procedures and sequential instructions
- **Location**: Physical or virtual places where activities occur
- **Event**: Time-bound activities, occurrences, or experiences
- **Organization**: Companies, institutions, groups, or formal entities
- **Document**: Information content in various forms (books, articles, reports, videos, etc.)
- **Topic**: Subject of conversation, interest, or knowledge domain (used as a fallback)
- **Object**: Physical items, tools, devices, or possessions (used as a fallback)

These entity types are defined in `config.yaml` and can be customized by modifying the descriptions:

```yaml
graphiti:
  entity_types:
    - name: "Preference"
      description: "User preferences, choices, opinions, or selections"
    - name: "Requirement"
      description: "Specific needs, features, or functionality"
    # ... additional entity types
```

The MCP server automatically uses these entity types during episode ingestion to extract and structure information from conversations and documents.

### Environment Variables

The `config.yaml` file supports environment variable expansion using `${VAR_NAME}` or `${VAR_NAME:default}` syntax. Key variables:

- `NEO4J_URI`: URI for the Neo4j database (default: `bolt://localhost:7687`)
- `NEO4J_USER`: Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD`: Neo4j password (default: `demodemo`)
- `OPENAI_API_KEY`: OpenAI API key (required for OpenAI LLM/embedder)
- `ANTHROPIC_API_KEY`: Anthropic API key (for Claude models)
- `GOOGLE_API_KEY`: Google API key (for Gemini models)
- `GROQ_API_KEY`: Groq API key (for Groq models)
- `DEEPSEEK_API_KEY`: DeepSeek API key (for DeepSeek models)
- `QWEN_API_KEY`: Qwen (Tongyi Qianwen) API key (for Qwen models)
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AZURE_OPENAI_DEPLOYMENT`: Azure OpenAI deployment name
- `AZURE_OPENAI_EMBEDDINGS_ENDPOINT`: Optional Azure OpenAI embeddings endpoint URL
- `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`: Optional Azure OpenAI embeddings deployment name
- `AZURE_OPENAI_API_VERSION`: Optional Azure OpenAI API version
- `USE_AZURE_AD`: Optional use Azure Managed Identities for authentication
- `SEMAPHORE_LIMIT`: Episode processing concurrency. See [Concurrency and LLM Provider 429 Rate Limit Errors](#concurrency-and-llm-provider-429-rate-limit-errors)

You can set these variables in a `.env` file in the project directory.

## Running the Server

### Default Setup (FalkorDB Combined Container)

To run the Graphiti MCP server with the default FalkorDB setup:

```bash
docker compose up
```

This starts a single container with:
- HTTP transport on `http://localhost:8000/mcp/`
- FalkorDB graph database on `localhost:6379`
- FalkorDB web UI on `http://localhost:3000`
- OpenAI LLM with gpt-5-mini model

### Running with Neo4j

#### Option 1: Using Docker Compose

The easiest way to run with Neo4j is using the provided Docker Compose configuration:

```bash
# This starts both Neo4j and the MCP server
docker compose -f docker/docker-compose.neo4j.yaml up
```

#### Option 2: Direct Execution with Existing Neo4j

If you have Neo4j already running:

```bash
# Set environment variables
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"

# Run with Neo4j
uv run graphiti_mcp_server.py --database-provider neo4j
```

Or use the Neo4j configuration file:

```bash
uv run graphiti_mcp_server.py --config config/config-docker-neo4j.yaml
```

### Running with FalkorDB

#### Option 1: Using Docker Compose

```bash
# This starts both FalkorDB (Redis-based) and the MCP server
docker compose -f docker/docker-compose.falkordb.yaml up
```

#### Option 2: Direct Execution with Existing FalkorDB

```bash
# Set environment variables
export FALKORDB_URI="redis://localhost:6379"
export FALKORDB_PASSWORD=""  # If password protected

# Run with FalkorDB
uv run graphiti_mcp_server.py --database-provider falkordb
```

Or use the FalkorDB configuration file:

```bash
uv run graphiti_mcp_server.py --config config/config-docker-falkordb.yaml
```

### Available Command-Line Arguments

- `--config`: Path to YAML configuration file (default: config.yaml)
- `--llm-provider`: LLM provider to use (openai, azure_openai, anthropic, gemini, groq, deepseek, qwen)
- `--embedder-provider`: Embedder provider to use (openai, azure_openai, gemini, voyage)
- `--database-provider`: Database provider to use (falkordb, neo4j) - default: falkordb
- `--model`: Model name to use with the LLM client
- `--temperature`: Temperature setting for the LLM (0.0-2.0)
- `--transport`: Choose the transport method (http or stdio, default: http)
- `--group-id`: Set a namespace for the graph (optional). If not provided, defaults to "main"
- `--destroy-graph`: If set, destroys all Graphiti graphs on startup

### Concurrency and LLM Provider 429 Rate Limit Errors

Graphiti's ingestion pipelines are designed for high concurrency, controlled by the `SEMAPHORE_LIMIT` environment variable. This setting determines how many episodes can be processed simultaneously. Since each episode involves multiple LLM calls (entity extraction, deduplication, summarization), the actual number of concurrent LLM requests will be several times higher.

**Default:** `SEMAPHORE_LIMIT=10` (suitable for OpenAI Tier 3, mid-tier Anthropic)

#### Tuning Guidelines by LLM Provider

**OpenAI:**
- Tier 1 (free): 3 RPM → `SEMAPHORE_LIMIT=1-2`
- Tier 2: 60 RPM → `SEMAPHORE_LIMIT=5-8`
- Tier 3: 500 RPM → `SEMAPHORE_LIMIT=10-15`
- Tier 4: 5,000 RPM → `SEMAPHORE_LIMIT=20-50`

**Anthropic:**
- Default tier: 50 RPM → `SEMAPHORE_LIMIT=5-8`
- High tier: 1,000 RPM → `SEMAPHORE_LIMIT=15-30`

**Azure OpenAI:**
- Consult your quota in Azure Portal and adjust accordingly
- Start conservative and increase gradually

**Ollama (local):**
- Hardware dependent → `SEMAPHORE_LIMIT=1-5`
- Monitor CPU/GPU usage and adjust

#### Symptoms

- **Too high**: 429 rate limit errors, increased API costs from parallel processing
- **Too low**: Slow episode throughput, underutilized API quota

#### Monitoring

- Watch logs for `429` rate limit errors
- Monitor episode processing times in server logs
- Check your LLM provider's dashboard for actual request rates
- Track token usage and costs

Set this in your `.env` file:
```bash
SEMAPHORE_LIMIT=10  # Adjust based on your LLM provider tier
```

### Docker Deployment

The Graphiti MCP server can be deployed using Docker with your choice of database backend. The Dockerfile uses `uv` for package management, ensuring consistent dependency installation.

A pre-built Graphiti MCP container is available at: `zepai/knowledge-graph-mcp`

#### Environment Configuration

Before running Docker Compose, configure your API keys using a `.env` file (recommended):

1. **Create a .env file in the mcp_server directory**:
   ```bash
   cd graphiti/mcp_server
   cp .env.example .env
   ```

2. **Edit the .env file** to set your API keys:
   ```bash
   # Required - at least one LLM provider API key
   OPENAI_API_KEY=your_openai_api_key_here

   # Optional - other LLM providers
   ANTHROPIC_API_KEY=your_anthropic_key
   GOOGLE_API_KEY=your_google_key
   GROQ_API_KEY=your_groq_key

   # Optional - embedder providers
   VOYAGE_API_KEY=your_voyage_key
   ```

**Important**: The `.env` file must be in the `mcp_server/` directory (the parent of the `docker/` subdirectory).

#### Running with Docker Compose

**All commands must be run from the `mcp_server` directory** to ensure the `.env` file is loaded correctly:

```bash
cd graphiti/mcp_server
```

##### Option 1: FalkorDB Combined Container (Default)

Single container with both FalkorDB and MCP server - simplest option:

```bash
docker compose up
```

##### Option 2: Neo4j Database

Separate containers with Neo4j and MCP server:

```bash
docker compose -f docker/docker-compose-neo4j.yml up
```

Default Neo4j credentials:
- Username: `neo4j`
- Password: `demodemo`
- Bolt URI: `bolt://neo4j:7687`
- Browser UI: `http://localhost:7474`

##### Option 3: FalkorDB with Separate Containers

Alternative setup with separate FalkorDB and MCP server containers:

```bash
docker compose -f docker/docker-compose-falkordb.yml up
```

FalkorDB configuration:
- Redis port: `6379`
- Web UI: `http://localhost:3000`
- Connection: `redis://falkordb:6379`

#### Accessing the MCP Server

Once running, the MCP server is available at:
- **HTTP endpoint**: `http://localhost:8000/mcp/`
- **Health check**: `http://localhost:8000/health`

#### Running Docker Compose from a Different Directory

If you run Docker Compose from the `docker/` subdirectory instead of `mcp_server/`, you'll need to modify the `.env` file path in the compose file:

```yaml
# Change this line in the docker-compose file:
env_file:
  - path: ../.env    # When running from mcp_server/

# To this:
env_file:
  - path: .env       # When running from mcp_server/docker/
```

However, **running from the `mcp_server/` directory is recommended** to avoid confusion.

## Integrating with MCP Clients

### VS Code / GitHub Copilot

VS Code with GitHub Copilot Chat extension supports MCP servers. Add to your VS Code settings (`.vscode/mcp.json` or global settings):

```json
{
  "mcpServers": {
    "graphiti": {
      "uri": "http://localhost:8000/mcp/",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

### Other MCP Clients

To use the Graphiti MCP server with other MCP-compatible clients, configure it to connect to the server:

> [!IMPORTANT]
> You will need the Python package manager, `uv` installed. Please refer to the [`uv` install instructions](https://docs.astral.sh/uv/getting-started/installation/).
>
> Ensure that you set the full path to the `uv` binary and your Graphiti project folder.

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "transport": "stdio",
      "command": "/Users/<user>/.local/bin/uv",
      "args": [
        "run",
        "--isolated",
        "--directory",
        "/Users/<user>>/dev/zep/graphiti/mcp_server",
        "--project",
        ".",
        "graphiti_mcp_server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
        "OPENAI_API_KEY": "sk-XXXXXXXX",
        "MODEL_NAME": "gpt-4.1-mini"
      }
    }
  }
}
```

For HTTP transport (default), you can use this configuration:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "transport": "http",
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

## Available Tools

The Graphiti MCP server exposes the following tools:

- `add_episode`: Add an episode to the knowledge graph (supports text, JSON, and message formats)
- `search_nodes`: Search the knowledge graph for relevant node summaries
- `search_facts`: Search the knowledge graph for relevant facts (edges between entities)
- `delete_entity_edge`: Delete an entity edge from the knowledge graph
- `delete_episode`: Delete an episode from the knowledge graph
- `get_entity_edge`: Get an entity edge by its UUID
- `get_episodes`: Get the most recent episodes for a specific group
- `clear_graph`: Clear all data from the knowledge graph and rebuild indices
- `get_status`: Get the status of the Graphiti MCP server and Neo4j connection

## Working with JSON Data

The Graphiti MCP server can process structured JSON data through the `add_episode` tool with `source="json"`. This
allows you to automatically extract entities and relationships from structured data:

```

add_episode(
name="Customer Profile",
episode_body="{\"company\": {\"name\": \"Acme Technologies\"}, \"products\": [{\"id\": \"P001\", \"name\": \"CloudSync\"}, {\"id\": \"P002\", \"name\": \"DataMiner\"}]}",
source="json",
source_description="CRM data"
)

```

## Integrating with the Cursor IDE

To integrate the Graphiti MCP Server with the Cursor IDE, follow these steps:

1. Run the Graphiti MCP server using the default HTTP transport:

```bash
uv run graphiti_mcp_server.py --group-id <your_group_id>
```

Hint: specify a `group_id` to namespace graph data. If you do not specify a `group_id`, the server will use "main" as the group_id.

or

```bash
docker compose up
```

2. Configure Cursor to connect to the Graphiti MCP server.

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "url": "http://localhost:8000/mcp/"
    }
  }
}
```

3. Add the Graphiti rules to Cursor's User Rules. See [cursor_rules.md](cursor_rules.md) for details.

4. Kick off an agent session in Cursor.

The integration enables AI assistants in Cursor to maintain persistent memory through Graphiti's knowledge graph
capabilities.

## Integrating with Claude Desktop (Docker MCP Server)

The Graphiti MCP Server uses HTTP transport (at endpoint `/mcp/`). Claude Desktop does not natively support HTTP transport, so you'll need to use a gateway like `mcp-remote`.

1.  **Run the Graphiti MCP server**:

    ```bash
    docker compose up
    # Or run directly with uv:
    uv run graphiti_mcp_server.py
    ```

2.  **(Optional) Install `mcp-remote` globally**:
    If you prefer to have `mcp-remote` installed globally, or if you encounter issues with `npx` fetching the package, you can install it globally. Otherwise, `npx` (used in the next step) will handle it for you.

    ```bash
    npm install -g mcp-remote
    ```

3.  **Configure Claude Desktop**:
    Open your Claude Desktop configuration file (usually `claude_desktop_config.json`) and add or modify the `mcpServers` section as follows:

    ```json
    {
      "mcpServers": {
        "graphiti-memory": {
          // You can choose a different name if you prefer
          "command": "npx", // Or the full path to mcp-remote if npx is not in your PATH
          "args": [
            "mcp-remote",
            "http://localhost:8000/mcp/" // The Graphiti server's HTTP endpoint
          ]
        }
      }
    }
    ```

    If you already have an `mcpServers` entry, add `graphiti-memory` (or your chosen name) as a new key within it.

4.  **Restart Claude Desktop** for the changes to take effect.

## Requirements

- Python 3.10 or higher
- OpenAI API key (for LLM operations and embeddings) or other LLM provider API keys
- MCP-compatible client
- Docker and Docker Compose (for the default FalkorDB combined container)
- (Optional) Neo4j database (version 5.26 or later) if not using the default FalkorDB setup

## Telemetry

The Graphiti MCP server uses the Graphiti core library, which includes anonymous telemetry collection. When you initialize the Graphiti MCP server, anonymous usage statistics are collected to help improve the framework.

### What's Collected

- Anonymous identifier and system information (OS, Python version)
- Graphiti version and configuration choices (LLM provider, database backend, embedder type)
- **No personal data, API keys, or actual graph content is ever collected**

### How to Disable

To disable telemetry in the MCP server, set the environment variable:

```bash
export GRAPHITI_TELEMETRY_ENABLED=false
```

Or add it to your `.env` file:

```
GRAPHITI_TELEMETRY_ENABLED=false
```

For complete details about what's collected and why, see the [Telemetry section in the main Graphiti README](../README.md#telemetry).

## License

This project is licensed under the same license as the parent Graphiti project.
