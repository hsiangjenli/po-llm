# POLLM - PO File Translation Tool

POLLM is a Python CLI tool for translating `.po` (gettext) files using Large Language Models (LLMs) like OpenAI, OpenRouter, or local Ollama models. The tool supports glossary-based translation and can handle both fuzzy and untranslated entries.

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Installation & Setup

**Primary Method (Rye - Recommended):**
- Install Rye package manager: `sh bin/install_rye.sh`
  - Note: May fail in environments with network restrictions. Use pip fallback below.
- Set up development environment: `make setup` 
- Install dependencies: `rye sync`
- Build package: `rye build` -- takes 2-3 minutes. NEVER CANCEL. Set timeout to 10+ minutes.

**Fallback Method (pip):**
- Install in development mode: `pip install -e .` -- takes 3-5 minutes. NEVER CANCEL. Set timeout to 15+ minutes.
  - May fail due to network connectivity issues with PyPI
- Install core dependencies separately if needed:
  ```bash
  pip install polib typer openai python-dotenv pandas beautifulsoup4 requests
  ```

**Environment Setup:**
- Python version: 3.10+ (project uses 3.10.14, tested with 3.12+)
- Set API key for OpenAI: `export POLLM_OPENAI_API_KEY=your-api-key`
- For Ollama (local): No API key needed, uses `http://localhost:11434/v1` by default

### Running the CLI

**ALWAYS ensure installation is complete before running CLI commands.**

- Check CLI availability: `pollm --help`
  - If not available, ensure `pip install -e .` completed successfully
  - Or run directly: `PYTHONPATH=src python -m pollm.cli --help`

**Core Commands:**
- Translate all entries: `pollm translate src/example/bugs.po --model qwen2.5:14b`
- Translate only fuzzy entries: `pollm fuzzy src/example/bugs.po --model qwen2.5:14b`

**Available Options:**
- `--temperature`: Model randomness (default: 0.1)
- `--max-messages`: Max message history for context (default: 4)  
- `--translate_mode`: `fully` or `untranslated`

### Testing & Validation

**Manual Testing Workflow:**
1. ALWAYS test with example files first: `src/example/bugs.po` (238 lines) and `src/example/mapping.po` (201 lines)
2. Copy example files before testing to avoid modifying originals:
   ```bash
   cp src/example/bugs.po /tmp/test_bugs.po
   cp src/example/mapping.po /tmp/test_mapping.po
   ```
3. Test CLI help: `pollm --help` (requires dependencies installed)
4. Test translation commands (requires API key or local Ollama):
   ```bash
   # Test with OpenAI/OpenRouter
   export POLLM_OPENAI_API_KEY=your-key
   pollm translate /tmp/test_bugs.po --model gpt-4o-mini
   
   # Test with local Ollama (if running)
   pollm translate /tmp/test_bugs.po --model qwen2.5:14b
   ```
5. Verify output .po files are properly formatted and translated

**Unit Testing:**
- No formal test suite exists yet
- Validate functionality through CLI testing with example files
- Test basic imports (works without dependencies):
  ```bash
  python -c "import sys; sys.path.insert(0, 'src'); from pollm.prompt_utils import PromptManager; print('Prompts available:', PromptManager.list())"
  ```
- Test CLI import (requires dependencies):
  ```bash
  python -c "import sys; sys.path.insert(0, 'src'); from pollm.cli import app; print('CLI imports successfully')"
  ```

### Documentation

**Building Documentation:**
- Documentation uses Sphinx
- Check docs structure: `ls -la docs/` shows `Makefile`, `make.bat`, and `source/` directory
- Build HTML docs: `cd docs && make html` -- takes 2-3 minutes. NEVER CANCEL. Set timeout to 10+ minutes.
  - Note: Requires Sphinx and dependencies installed. May fail without network access.
- Build PDF docs: `cd docs && make simplepdf` -- takes 3-5 minutes. NEVER CANCEL. Set timeout to 15+ minutes.
- Documentation source: `docs/source/` (index.rst, commands.rst, glossary.rst)
- Built docs: `docs/build/html/` (HTML) and `docs/build/simplepdf/` (PDF)

**Note:** Documentation build requires Sphinx dependencies. Install with: `pip install sphinx sphinx-rtd-theme myst-parser`

### Code Quality & Pre-commit

**Pre-commit Hooks (configured in `.pre-commit-config.yaml`):**
- Ruff formatting and linting: `ruff --fix` then `ruff format`
- Import sorting: `isort`
- Type checking: `pylint`
- Security scanning: `bandit --severity-level all --exclude tests/`
- Documentation formatting: `docformatter` and `doc8`

**ALWAYS run before committing:**
```bash
# Install pre-commit hooks (if pre-commit is available)
pre-commit install

# Run all checks (requires tools installed)
pre-commit run --all-files
```

**Or run individual tools (install first if needed):**
```bash
# Install tools: pip install ruff isort pylint bandit docformatter doc8
ruff check --fix src/
ruff format src/
isort src/
pylint src/pollm/
bandit --severity-level all --exclude tests/ -r src/
```

**Note:** Code quality tools may not be installed by default. Install individually or via requirements-dev.lock.

## Project Structure

**Core Modules:**
- `src/pollm/cli.py` - Main CLI application with Typer
- `src/pollm/prompt_utils.py` - Prompt template management
- `src/pollm/glossary.py` - Glossary search and management
- `src/pollm/prompts/` - Translation prompt templates
- `src/example/` - Example .po files for testing

**Configuration Files:**
- `pyproject.toml` - Project metadata and dependencies
- `.pre-commit-config.yaml` - Code quality hooks
- `requirements.lock` / `requirements-dev.lock` - Locked dependencies (generated by Rye)

**Documentation:**
- `docs/source/index.rst` - Main documentation
- `docs/source/commands.rst` - CLI command documentation
- `docs/source/glossary.rst` - Glossary documentation

## Common Issues & Workarounds

**Network Connectivity:**
- Rye installation may fail: Use pip fallback method
- PyPI timeouts during `pip install`: Retry with longer timeout or install dependencies individually
- Documentation builds may fail without network access to fetch some dependencies

**Missing Dependencies:**
- If CLI import fails: Ensure `pip install -e .` completed successfully
- For development: Install missing tools individually (`pip install ruff isort pylint`)
- For documentation: `pip install sphinx sphinx-rtd-theme myst-parser`

**API Key Issues:**
- OpenAI: Set `POLLM_OPENAI_API_KEY` environment variable
- OpenRouter: Set `POLLM_OPENAI_API_KEY` and `POLLM_BASE_URL=https://openrouter.ai/api/v1`
- Ollama: Ensure Ollama server is running locally on port 11434

**Make Command Issues:**
- Available make targets: `setup`, `build`, `tag`, `clean`, `docker`
- `make setup` - installs Rye (may fail due to network restrictions)
- `make build` - requires Rye, use `pip install -e .` as fallback
- `make tag` - creates git tag from current version

## Development Workflow

**Making Changes:**
1. Set up development environment (see Installation section above)
2. Make code changes
3. Test with example files: `pollm translate src/example/bugs.po --model your-model`
4. Run code quality checks: `pre-commit run --all-files`
5. Build and test documentation: `cd docs && make html`
6. Commit changes

**Typical Development Tasks:**
- Adding new prompt templates: Create `.txt` files in `src/pollm/prompts/`
- Modifying CLI commands: Edit `src/pollm/cli.py`
- Updating glossary logic: Edit `src/pollm/glossary.py`
- Adding documentation: Edit files in `docs/source/`

**Release Process:**
- Uses GitHub Actions (`.github/workflows/changelog.yaml`)
- Triggered by version tags (`v*.*.*`)
- Builds Python packages, PDF/HTML docs, and creates GitHub releases
- Update version in `pyproject.toml` and create git tag: `sh bin/git_tag.sh`

## Validation Scenarios

**ALWAYS test these scenarios after making changes:**

1. **CLI Functionality:**
   ```bash
   pollm --help
   pollm translate --help
   pollm fuzzy --help
   ```

2. **Translation Workflow:**
   ```bash
   # Copy example file to avoid modifying original
   cp src/example/bugs.po /tmp/test_bugs.po
   pollm translate /tmp/test_bugs.po --model your-model
   # Verify translation completed and file is valid
   ```

3. **Import Testing:**
   ```bash
   python -c "import sys; sys.path.insert(0, 'src'); from pollm.cli import app"
   python -c "import sys; sys.path.insert(0, 'src'); from pollm.prompt_utils import PromptManager; print(PromptManager.list())"
   ```

4. **Documentation Build:**
   ```bash
   cd docs && make html
   # Check that docs/build/html/index.html exists
   ```

## Critical Timing Information

**NEVER CANCEL these long-running operations:**

- **Package Installation**: `pip install -e .` takes 3-5 minutes. Set timeout to 15+ minutes.
- **Rye Build**: `rye build` takes 2-3 minutes. Set timeout to 10+ minutes.  
- **Documentation Build**: `make html` takes 2-3 minutes. Set timeout to 10+ minutes.
- **PDF Documentation**: `make simplepdf` takes 3-5 minutes. Set timeout to 15+ minutes.
- **Translation Operations**: Depends on file size and model speed. Allow 1-5 minutes per operation.

**Expected timeouts due to network limitations:**
- Initial dependency installation may timeout on slow connections
- Rye installation script may fail in restricted network environments
- Use pip fallback and manual dependency installation if needed

## Common Command Outputs

**Repository Structure:**
```bash
ls -la
# Expected output:
.git/ .github/ .gitignore .pre-commit-config.yaml .python-version
Dockerfile.sphinx Makefile README.md bin/ docs/ pyproject.toml
requirements.lock requirements-dev.lock src/
```

**Source Structure:**
```bash
find src -name "*.py" | head -5
# Expected output:
src/pollm/__init__.py
src/pollm/cli.py
src/pollm/glossary.py
src/pollm/prompt_utils.py
src/pollm/test.py
```

**Example Files:**
```bash
ls -la src/example/
# Expected output:
bugs.po (11178 bytes, 238 lines)
mapping.po (7881 bytes, 201 lines)
```

**Prompt Templates:**
```bash
python -c "import sys; sys.path.insert(0, 'src'); from pollm.prompt_utils import PromptManager; print(PromptManager.list())"
# Expected output:
['fuzzy.txt', 'translate.txt', 'system_prompt.txt']
```
