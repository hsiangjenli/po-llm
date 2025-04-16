# 🌍 POLLM

A localization-friendly CLI tool powered by LLMs for translating and refining `.po` files with glossary support.

## 🚀 Features

- Translate `.po` files using LLMs like `qwen2.5:14b`, OpenAI-compatible models, or your local Ollama model

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

### Translate all entries

```bash
pollm translate example/bugs.po --model qwen2.5:14b
```

### Translate only fuzzy entries

```bash
pollm fuzzy example/bugs.po --model qwen2.5:14b
```

Supported options:

- `--temperature`: Model randomness (default: `0.1`)
- `--max-messages`: Max message history for context (default: `4`)
- `--translate_mode`: `fully` or `untranslated`

## 📚 Documentation

- https://hsiangjenli.github.io/po-llm/
