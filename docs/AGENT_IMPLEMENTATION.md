# AI Agent for Iterative Contextual Translation

This document describes the implementation of the AI Agent for Iterative Contextual Translation in the po-llm project.

## Overview

The AI Agent enables translation to be an iterative process rather than a single-pass operation. It provides:

- **MCP-style tool integration** for searching suitable translations
- **Interactive confirmation and refinement** of translation context
- **Context awareness** across translation iterations
- **beeai_framework compatibility** for ecosystem integration
- **Multi-LLM support** including Ollama and OpenAI providers

## Architecture

### Core Components

1. **`IterativeTranslationAgent`** (`src/pollm/agent.py`)
   - Main agent class that orchestrates the iterative translation process
   - Manages context across iterations
   - Interfaces with LLM providers
   - Handles user feedback and refinement

2. **`MCPTranslationTool`** (`src/pollm/agent.py`)
   - Model Context Protocol (MCP) style tool for translation search
   - Searches similar translations in context database
   - Provides contextual hints and suggestions
   - Integrates with existing glossary functionality

3. **`TranslationContext`** (`src/pollm/agent.py`)
   - Data structure for managing translation context
   - Tracks iteration count, confidence scores, user feedback
   - Maintains glossary matches and similar translations

4. **`BeeAITranslationAgent`** (`src/pollm/beeai_framework.py`)
   - Compatibility wrapper for beeai_framework integration
   - Provides standardized interface for agent ecosystem
   - Supports configuration schema and capability discovery

### Workflow

1. **Initialization**
   - Load configuration and initialize LLM client
   - Set up MCP tool and context database
   - Load previous session context if available

2. **Translation Generation**
   - Analyze source text for context hints
   - Search glossary and similar translations
   - Build context-aware prompt
   - Generate translation using LLM

3. **Interactive Confirmation**
   - Present translation with confidence score
   - Show context information (glossary matches, similar translations)
   - Allow user to accept, reject, or request refinement

4. **Iterative Refinement**
   - Collect user feedback
   - Update context with feedback
   - Regenerate translation with enhanced context
   - Repeat until acceptance or max iterations reached

5. **Context Learning**
   - Store successful translations in context database
   - Build knowledge base for future translations
   - Maintain consistency across translation sessions

## CLI Usage

### New `agent` Command

```bash
# Interactive iterative translation
pollm agent example/bugs.po --model qwen2.5:14b

# Auto-confirm high confidence translations
pollm agent example/bugs.po --model qwen2.5:14b --auto_confirm --confidence_threshold 0.8

# Limit iterations and target specific entries
pollm agent example/bugs.po --max_iterations 2 --target_entries fuzzy

# Save/load translation context
pollm agent example/bugs.po --context_file translation_context.json
```

### Command Options

- `--model`: LLM model to use (default: qwen/qwen-2.5-72b-instruct:free)
- `--temperature`: Model temperature for creativity (default: 0.1)
- `--max_iterations`: Maximum iterations per translation (default: 3)
- `--target_entries`: Target entries - untranslated, fuzzy, or all (default: untranslated)
- `--auto_confirm`: Auto-confirm translations above confidence threshold
- `--confidence_threshold`: Threshold for auto-confirmation (default: 0.8)
- `--context_file`: File to save/load translation context between sessions

## beeai_framework Integration

### Agent Configuration

```python
from pollm.beeai_framework import create_agent

config = {
    "api_key": "your-api-key",
    "base_url": "https://openrouter.ai/api/v1",
    "max_iterations": 3,
    "confidence_threshold": 0.8
}

agent = create_agent(config)
```

### Supported Actions

1. **`translate_po`** - Process entire PO file
2. **`translate_single`** - Translate single text entry
3. **`get_suggestions`** - Get translation suggestions for text

### Example Usage

```python
# Translate PO file
result = agent.process({
    "action": "translate_po",
    "po_file_path": "/path/to/file.po",
    "model": "qwen2.5:14b",
    "parameters": {
        "temperature": 0.1,
        "target_entries": "untranslated",
        "auto_confirm": False
    }
})

# Translate single entry
result = agent.process({
    "action": "translate_single",
    "source_text": "Hello world",
    "model": "qwen2.5:14b",
    "temperature": 0.1
})

# Get suggestions
result = agent.process({
    "action": "get_suggestions",
    "source_text": "API function"
})
```

## MCP Tool Integration

The `MCPTranslationTool` provides Model Context Protocol style functionality:

### Translation Search
- Searches context database for similar translations
- Returns ranked results by confidence score
- Supports fuzzy matching for related terms

### Context Analysis
- Extracts contextual hints from source text
- Identifies technical documentation, UI elements, error messages
- Provides appropriate translation strategies

### Glossary Integration
- Leverages existing glossary search functionality
- Ensures consistent terminology usage
- Highlights relevant term matches

## Interactive Features

### Confirmation Interface
```
============================================================
Source: Return ``1`` if the mapping object has the key *key* and ``0`` otherwise.
Translation: 回傳 ``1`` 如果該對應物件具有鍵 *key*，否則回傳 ``0``。
Confidence: 0.85
Glossary matches: 2
Similar translations found: 1
Iteration: 1/3
============================================================
Accept translation? (y/n/r/s): 
```

### User Options
- **y** - Accept translation and continue
- **n** - Reject and provide feedback for improvement
- **r** - Request refinement with specific guidance
- **s** - Skip this entry

### Feedback Integration
User feedback is incorporated into subsequent iterations:
- Natural language feedback guides refinement
- Context hints improve translation quality
- Learning accumulates across translation sessions

## Context Management

### Session Context
- Maintains translation history within session
- Builds knowledge base for consistency
- Tracks successful translation patterns

### Persistent Context
- Save/load context between sessions
- Build long-term translation memory
- Improve translation quality over time

### Context Data Structure
```python
{
    "source_text": {
        "target": "translated_text",
        "confidence": 0.85,
        "context": {
            "iteration_count": 2,
            "user_feedback": ["Make it more natural"],
            "glossary_matches": [...],
            "similar_translations": [...]
        }
    }
}
```

## Configuration

### Environment Variables
- `POLLM_OPENAI_API_KEY` - OpenAI API key
- `POLLM_BASE_URL` - LLM API base URL (default: https://openrouter.ai/api/v1)

### Agent Parameters
- `max_iterations` - Maximum refinement iterations (default: 3)
- `confidence_threshold` - Auto-confirmation threshold (default: 0.8)
- `temperature` - LLM temperature setting (default: 0.1)

## Integration Points

### Existing Components
- **Prompt Management** - Uses enhanced agent-specific prompts
- **Glossary Search** - Integrates existing glossary functionality
- **LLM Providers** - Works with current OpenAI/Ollama setup
- **PO File Handling** - Builds on existing polib integration

### New Capabilities
- **Iterative Workflow** - Multi-pass translation refinement
- **Context Awareness** - Cross-iteration learning and consistency
- **Interactive Interface** - User feedback and confirmation
- **MCP Integration** - Standards-compliant tool interface
- **Framework Compatibility** - beeai_framework ecosystem support

## Benefits

1. **Improved Quality** - Iterative refinement produces better translations
2. **Consistency** - Context awareness ensures term consistency
3. **User Control** - Interactive confirmation allows quality oversight
4. **Learning** - Agent improves over time through feedback
5. **Flexibility** - Works with existing tools and new frameworks
6. **Scalability** - Context database grows with usage

## Future Enhancements

- Advanced similarity algorithms for translation search
- Machine learning models for confidence scoring
- Integration with translation memory systems
- Collaborative feedback from multiple translators
- Real-time translation quality metrics