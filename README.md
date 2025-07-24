# 🌍 POLLM

A localization-friendly CLI tool powered by LLMs for translating and refining `.po` files with glossary support.

## 🚀 Features

- Translate `.po` files using LLMs like `qwen2.5:14b`, OpenAI-compatible models, or your local Ollama model
- **NEW**: AI Agent for Iterative Contextual Translation with interactive refinement capabilities
- **NEW**: MCP-style tool integration for translation search and suggestions
- **NEW**: beeai_framework compatibility for agent ecosystem integration

## 📦 Installation

You can install directly from GitHub:

```bash
pip install git+https://github.com/hsiangjenli/po-llm.git
```

## 🔑 Export OpenAI API Key

If you're using OpenAI:

```bash
# zsh
echo 'export POLLM_OPENAI_API_KEY=your-api-key' >> ~/.zshrc
source ~/.zshrc
```

If you're using Ollama, no key is needed and `http://localhost:11434/v1` will be used by default.

## 🧠 CLI Usage

### Traditional Translation Commands

#### Translate all entries

```bash
pollm translate example/bugs.po --model qwen2.5:14b
```

#### Translate only fuzzy entries

```bash
pollm fuzzy example/bugs.po --model qwen2.5:14b
```

### 🤖 NEW: AI Agent for Iterative Translation

The AI Agent provides an interactive, iterative translation workflow with context awareness:

```bash
# Interactive iterative translation
pollm agent example/bugs.po --model qwen2.5:14b

# Auto-confirm high confidence translations  
pollm agent example/bugs.po --model qwen2.5:14b --auto_confirm --confidence_threshold 0.8

# Process only untranslated entries with context persistence
pollm agent example/bugs.po --target_entries untranslated --context_file context.json
```

#### Agent Features:
- **Iterative Refinement**: Multiple passes with user feedback
- **Context Awareness**: Learns from previous translations
- **Interactive Confirmation**: Review and refine translations
- **MCP Integration**: Search for suitable translations
- **Confidence Scoring**: Auto-confirm high-quality translations
- **Persistent Context**: Save translation memory between sessions

### Supported Options

- `--temperature`: Model randomness (default: `0.1`)
- `--max-messages`: Max message history for context (default: `4`)
- `--translate_mode`: `fully` or `untranslated`
- `--max_iterations`: Max iterations per translation (agent only, default: `3`)
- `--auto_confirm`: Auto-confirm high confidence translations (agent only)
- `--confidence_threshold`: Threshold for auto-confirmation (agent only, default: `0.8`)
- `--context_file`: Save/load translation context (agent only)

## 🎯 Agent Workflow

1. **Analysis**: Examine source text and search for contextual clues
2. **Generation**: Create translation using LLM with context awareness
3. **Confirmation**: Present translation with confidence score for review
4. **Refinement**: Collect feedback and improve translation iteratively
5. **Learning**: Store successful translations for future consistency

## 🔧 beeai_framework Integration

The agent properly integrates with the [beeai-framework](https://github.com/i-am-bee/beeai-framework) ecosystem as a native BaseAgent:

```python
from pollm.beeai_framework import create_translation_agent, TranslationRunInput

# Create agent with proper beeai_framework integration
config = {
    "api_key": "your-api-key",
    "max_iterations": 3,
    "confidence_threshold": 0.8
}

agent = create_translation_agent(config)

# Use with beeai_framework patterns
from pathlib import Path

run_input = TranslationRunInput(
    po_file_path=Path("/path/to/file.po"),
    model="qwen2.5:14b",
    auto_confirm=False
)

# Execute with proper async/await patterns
result = await agent.run(run_input)
print(f"Translation completed: {result.state.entries_processed} entries processed")

# Legacy compatibility also available
from pollm.beeai_framework import create_agent  # Deprecated but supported
legacy_agent = create_agent(config)
result = legacy_agent.process({
    "action": "translate_po",
    "po_file_path": "/path/to/file.po",
    "model": "qwen2.5:14b"
})
```

## 📚 Documentation

- https://hsiangjenli.github.io/po-llm/
- [AI Agent Implementation Guide](docs/AGENT_IMPLEMENTATION.md)
