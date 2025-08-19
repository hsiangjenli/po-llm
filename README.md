# 🌍 POLLM

A localization-friendly CLI tool powered by LLMs for translating and refining `.po` files with glossary support.

## 🚀 Features

- Translate `.po` files using LLMs like `qwen2.5:14b`, OpenAI-compatible models, or your local Ollama model
- **NEW**: Batch translation for 95%+ token savings and improved performance
- Intelligent caching to avoid duplicate translations
- Glossary integration for consistent terminology

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

### 🚀 Batch Translation (Recommended - 95% Token Savings)

```bash
# Translate untranslated entries in batches
pollm translate-batch example/bugs.po --batch-size 50

# Process fuzzy entries  
pollm translate-batch example/bugs.po --translate-mode fuzzy

# Full translation with custom settings
pollm translate-batch example/bugs.po --translate-mode fully --batch-size 25
```

Batch translation options:
- `--batch-size`: Entries per batch (default: `50`)
- `--translate-mode`: `untranslated`, `fuzzy`, or `fully` (default: `untranslated`)
- `--max-context-pairs`: Translation context pairs (default: `20`)

### Traditional Commands (Individual Entry Processing)

```bash
# Translate all entries
pollm translate example/bugs.po --model qwen2.5:14b

# Translate only fuzzy entries
pollm fuzzy example/bugs.po --model qwen2.5:14b
```

Supported options:

- `--temperature`: Model randomness (default: `0.1`)
- `--max-messages`: Max message history for context (default: `4`)
- `--translate_mode`: `fully` or `untranslated`

## 📈 Performance Comparison

| Approach | 100 Entries | API Calls | Token Usage | Time |
|----------|-------------|-----------|-------------|------|
| Traditional | 100 calls | 46,544 tokens | Slow | Individual processing |
| **Batch** | **2 calls** | **1,994 tokens** | **Fast** | **95.7% savings** |

## 📚 Documentation

- https://hsiangjenli.github.io/po-llm/
- [Batch Translation Guide](docs/BATCH_TRANSLATION.md)
