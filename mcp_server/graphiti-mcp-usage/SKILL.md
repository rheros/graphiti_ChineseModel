---
name: graphiti-mcp-usage
description: This skill enables Claude to intelligently use Graphiti knowledge graph MCP server for automatic information storage and retrieval, providing personalized continuous conversation experiences.
---

# Graphiti MCP Usage Skill

## Purpose

This skill equips Claude with the ability to intelligently use the Graphiti knowledge graph MCP server to automatically store valuable information during conversations and retrieve historical information when needed, creating a personalized and continuous user experience.

## When to Use This Skill

This skill should be used when Claude is connected to a Graphiti MCP server and needs to:
- Automatically identify and store valuable information from user conversations
- Retrieve historical information to provide context-aware responses
- Maintain continuity across conversations by remembering user preferences, learning notes, and project information
- Provide personalized recommendations based on stored knowledge

## How to Use This Skill

### Automatic Storage Strategy

**When to Automatically Store (execute without asking user):**

1. **Personal Experiences and Stories**
   - User's life experiences, work experiences
   - Learning insights and reflections
   - Travel, activities, important events

2. **Clear Preferences and Choices**
   - Statements like "I like...", "I prefer...", "I choose..."
   - Personal preferences for technologies, tools, methods
   - Work style and learning style preferences

3. **Learning and Growth**
   - Newly learned knowledge points and skills
   - Technical learning notes and summaries
   - Problem-solving approaches and methods

4. **Project and Work Information**
   - Current projects being worked on
   - Technology stack used at work
   - Career plans and goals

5. **Important Personal Information**
   - Professional background, areas of expertise
   - Hobbies, interests, strengths
   - Useful contact information (non-sensitive)

6. **Valuable Conversation Summaries**
   - When user says "remember..."
   - Important conclusions from discussions
   - Key points in decision-making processes

**Smart Tags for Storage:**

When adding episodes, use appropriate source tags:
- `Preference` - User preferences, choices, opinions
- `Procedure` - Learning notes, operating procedures, methodologies
- `Requirement` - Specific needs, functional requirements
- `Experience` - Personal experiences, work experiences
- `Project` - Project information, work content
- `Knowledge` - Knowledge points, technical concepts
- `Decision` - Decision-making processes, choice rationale
- `Goal` - Goals, plans

**Storage Parameters:**
```python
# When adding episodes, set these parameters:
name = "Concise descriptive title"  # Extract key points from content
epsode_body = "Complete content"  # Full content from user
source = "One of the tags above"  # Intelligent judgment
group_id = "User's group or default main"  # Get from context
```

### Automatic Retrieval Strategy

**When to Automatically Retrieve (execute before replying to user):**

1. **User Mentions Past Information**
   - "I said before..."
   - "We discussed before..."
   - "Do you remember..."

2. **Questions Requiring Continuity**
   - Asking about project progress, learning progress
   - Follow-up questions based on previous information
   - "What are my preferences?"

3. **When Providing Personalized Recommendations**
   - "Based on my situation..."
   - Recommending technologies, tools, methods
   - Providing learning path suggestions

4. **When Relevant Information Might Exist in Knowledge Graph**
   - Discussing previously talked about technical topics
   - Mentioning certain projects or experiences
   - Needing context recall

**Retrieval Methods:**
```python
# 1. Search episodes (get original conversation records)
query = "2-3 keywords from user's question"
search_episodes(query=query, group_id="user's group_id")

# 2. Search nodes (get entity information)
search_nodes(query=query, group_id="user's group_id")

# 3. Search facts/relationships (get related information)
search_facts(query=query, group_id="user's group_id")

# 4. Get graph status (understand overall situation)
get_graph_status(group_id="user's group_id")
```

**Keyword Extraction Tips:**
1. Extract core nouns: technical terms, project names, concepts
2. Keep verbs: learn, use, develop, solve
3. Time clues: recently, before, last time, today
4. Avoid stop words: 的, 了, 吗, 呢, etc.

### Interaction Modes

**Mode 1: Fully Automatic**
- User doesn't need any instructions
- AI automatically determines when to store and retrieve
- **Use case**: Long-term conversations, personal assistant, learning companion

**Mode 2: Trigger Word Mode (Recommended)**
- User triggers storage/retrieval with keywords

**Storage Trigger Words:**
- "Remember:..."
- "Save this information:..."
- "This is important:..."
- "Store to knowledge graph:..."

**Retrieval Trigger Words:**
- "What did I say before about [topic]?"
- "Search knowledge graph for [keyword]"
- "The [project/technology] I mentioned before"
- "What are my [preferences/choices]?"

**Mode 3: Confirmation Mode**
- AI actively asks user if they want to store
- Example: "Docker containerization is indeed useful! Should I save this learning note to your knowledge graph?"

## Best Practices

### ✅ Should Do
- Proactively identify valuable information and store it
- Check relevant knowledge before answering
- Use appropriate tags for classification
- Keep stored content concise and accurate
- Regularly summarize and review stored information

### ❌ Should Not Do
- Store sensitive or private information
- Store content without long-term value
- Answer questions requiring historical information without retrieval
- Store duplicate or redundant information
- Over-store causing knowledge graph clutter

## Storage Examples

### Example 1: Storing Learning Notes
```python
# User says: "Today I learned about Python decorators, they're a functional programming technique that can add functionality without modifying the original function"

Tool call:
{
  "name": "Python Decorators Learning Notes",
  "episode_body": "Today I learned about Python decorators, they're a functional programming technique that can add functionality without modifying the original function",
  "source": "Procedure",
  "group_id": "main"
}

AI response: "✓ Saved Python decorators learning notes to knowledge graph"
```

### Example 2: Storing Personal Preferences
```python
# User says: "I prefer using VSCode as my code editor, its plugin ecosystem is very rich"

Tool call:
{
  "name": "Code Editor Preference - VSCode",
  "episode_body": "Prefer using VSCode as code editor, plugin ecosystem is very rich",
  "source": "Preference",
  "group_id": "main"
}

AI response: "✓ Recorded your editor preference: VSCode"
```

### Example 3: Storing Project Information
```python
# User says: "I'm developing a user management system based on FastAPI, using PostgreSQL as the database"

Tool call:
{
  "name": "FastAPI User Management System Project",
  "episode_body": "Developing user management system based on FastAPI, using PostgreSQL as the database",
  "source": "Project",
  "group_id": "main"
}

AI response: "✓ Saved project information: FastAPI User Management System"
```

## Retrieval Examples

### Example 1: Answering Questions Based on Historical Information
```python
# User asks: "How is the FastAPI project I mentioned before progressing?"

AI actions:
1. Extract keywords from question: "FastAPI", "project"
2. Call search_episodes(query="FastAPI project", group_id="main")
3. Find previous project record
4. Reply based on retrieved information

AI response: "According to your knowledge graph records, you mentioned developing a FastAPI-based user management system using PostgreSQL as the database. Any progress recently? Should I help record new progress?"
```

### Example 2: Providing Personalized Recommendations
```python
# User asks: "I want to learn a new Python web framework, any recommendations?"

AI actions:
1. Call search_nodes(query="Python web framework", group_id="main")
2. Find user's existing tech stack: FastAPI, PostgreSQL
3. Analyze user preferences: likes modern, high-performance frameworks

AI response: "Based on your previous learning records, you've already mastered FastAPI. If you want to learn another Python web framework, I recommend Django (comprehensive features, suitable for large projects) or Flask (lightweight, flexible). Considering your preference for FastAPI, you might prefer Flask's simplicity."
```

## Configuration Parameters

### Basic Settings
```python
# Graphiti configuration
group_id = "main"  # Default user group
episode_id_prefix = ""  # Episode ID prefix
user_id = "mcp_user"  # User ID
```

### Retrieval Filters
```python
# Filters can be used when searching
filters = {
    "entity_types": ["Preference", "Procedure", "Project"],  # Search only specific types
    "start_date": "2025-01-01",  # Time range
    "end_date": "2025-12-31",
    "group_ids": ["main"]  # Specify group
}
```

## Troubleshooting

### Common Issues

1. **Cannot retrieve information**
   - Check if group_id is correct
   - Try different keywords
   - Confirm information was actually stored

2. **Storage failure**
   - Check if API key is valid
   - Confirm database connection is normal
   - Check error logs

3. **Duplicate information**
   - Search if it already exists before storing
   - Use more precise keywords
   - Regularly clean up duplicate content
