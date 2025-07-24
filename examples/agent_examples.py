#!/usr/bin/env python3
"""
Example usage of the Iterative Translation Agent

This script demonstrates how to use the agent programmatically
and through the beeai_framework interface.
"""

from pathlib import Path
import json
import sys
import os

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def example_agent_usage():
    """Example of using the agent programmatically"""
    print("🤖 Iterative Translation Agent Example")
    print("=" * 50)
    
    # This example shows the interfaces without requiring actual LLM calls
    
    # 1. Direct Agent Usage (requires LLM setup)
    print("\n1. Direct Agent Usage:")
    print("```python")
    print("from pollm.agent import IterativeTranslationAgent, MCPTranslationTool")
    print("from pollm.prompt_utils import PromptManager") 
    print("from openai import OpenAI")
    print()
    print("# Initialize LLM client")
    print("client = OpenAI(")
    print("    api_key='your-api-key',")
    print("    base_url='http://localhost:11434/v1'  # For Ollama")
    print(")")
    print()
    print("# Create agent")
    print("agent = IterativeTranslationAgent(")
    print("    client=client,")
    print("    max_iterations=3,")
    print("    confidence_threshold=0.8")
    print(")")
    print()
    print("# Process PO file")
    print("results = agent.process_po_file(")
    print("    po_file_path=Path('example/bugs.po'),")
    print("    model='qwen2.5:14b',")
    print("    auto_confirm=False")
    print(")")
    print("```")
    
    # 2. beeai_framework Integration (Proper BaseAgent)
    print("\n2. beeai_framework Integration (Proper BaseAgent):")
    print("```python")
    print("from pollm.beeai_framework import create_translation_agent, TranslationRunInput")
    print("from pathlib import Path")
    print("import asyncio")
    print()
    print("# Create agent with proper beeai_framework integration")
    print("config = {")
    print("    'api_key': 'your-api-key',")
    print("    'base_url': 'http://localhost:11434/v1',")
    print("    'max_iterations': 3,")
    print("    'confidence_threshold': 0.8")
    print("}")
    print()
    print("agent = create_translation_agent(config)")
    print()
    print("# Use with proper async/await patterns")
    print("async def run_translation():")
    print("    run_input = TranslationRunInput(")
    print("        po_file_path=Path('/path/to/file.po'),")
    print("        model='qwen2.5:14b',")
    print("        auto_confirm=False")
    print("    )")
    print("    ")
    print("    result = await agent.run(run_input)")
    print("    print(f'Processed {result.state.entries_processed} entries')")
    print()
    print("# Execute")
    print("asyncio.run(run_translation())")
    print("```")
    
    # 2b. Legacy Compatibility
    print("\n2b. Legacy Compatibility:")
    print("```python")
    print("from pollm.beeai_framework import create_agent  # Deprecated")
    print()
    print("# Legacy interface (deprecated but supported)")
    print("config = {")
    print("    'api_key': 'your-api-key',")
    print("    'base_url': 'http://localhost:11434/v1',")
    print("    'max_iterations': 3,")
    print("    'confidence_threshold': 0.8")
    print("}")
    print()
    print("agent = create_agent(config)")
    print()
    print("# Process PO file through legacy interface")
    print("result = agent.process({")
    print("    'action': 'translate_po',")
    print("    'po_file_path': '/path/to/file.po',")
    print("    'model': 'qwen2.5:14b',")
    print("    'parameters': {")
    print("        'temperature': 0.1,")
    print("        'target_entries': 'untranslated',")
    print("        'auto_confirm': False")
    print("    }")
    print("})")
    print("```")
    
    # 3. CLI Usage
    print("\n3. CLI Usage:")
    print("```bash")
    print("# Interactive iterative translation")
    print("pollm agent example/bugs.po --model qwen2.5:14b")
    print()
    print("# Auto-confirm high confidence translations")
    print("pollm agent example/bugs.po \\")
    print("  --model qwen2.5:14b \\")
    print("  --auto_confirm \\")
    print("  --confidence_threshold 0.8")
    print()
    print("# Process with context persistence")
    print("pollm agent example/bugs.po \\")
    print("  --target_entries fuzzy \\")
    print("  --max_iterations 2 \\")
    print("  --context_file translation_context.json")
    print("```")


def example_context_management():
    """Example of context management features"""
    print("\n🧠 Context Management Examples")
    print("=" * 50)
    
    try:
        from pollm.agent import TranslationContext, MCPTranslationTool
        
        # Create translation context
        context = TranslationContext(
            source_text="Return the object if found, otherwise None",
            confidence_score=0.75,
            iteration_count=1
        )
        
        # Add user feedback
        context.user_feedback.extend([
            "Make it more natural",
            "Use consistent terminology for 'object'"
        ])
        
        # Add glossary matches
        context.glossary_matches = [
            {"原文": "object", "翻譯": "物件"},
            {"原文": "return", "翻譯": "回傳"}
        ]
        
        print("✓ Created translation context:")
        print(f"  Source: {context.source_text}")
        print(f"  Confidence: {context.confidence_score}")
        print(f"  Iteration: {context.iteration_count}")
        print(f"  Feedback: {len(context.user_feedback)} items")
        print(f"  Glossary matches: {len(context.glossary_matches)} terms")
        
        # MCP Tool demonstration
        mcp_tool = MCPTranslationTool()
        
        # Add some example context
        mcp_tool.context_db.update({
            "return value": {
                "target": "回傳值",
                "confidence": 0.9,
                "context": {"type": "technical"}
            },
            "function object": {
                "target": "函數物件", 
                "confidence": 0.85,
                "context": {"type": "programming"}
            }
        })
        
        # Get suggestions
        suggestions = mcp_tool.get_translation_suggestions("return the object")
        print(f"\n✓ MCP tool suggestions:")
        print(f"  Context hints: {suggestions['context_hints']}")
        print(f"  Similar translations: {len(suggestions['similar_translations'])}")
        
    except ImportError as e:
        print(f"⚠️  Could not demonstrate context management: {e}")
        print("This requires the full package installation.")


def example_workflow_states():
    """Example of workflow states and user interactions"""
    print("\n🔄 Interactive Workflow Example")
    print("=" * 50)
    
    print("During iterative translation, users see:")
    print()
    print("┌" + "─" * 58 + "┐")
    print("│ Source: Return ``1`` if found, ``0`` otherwise.        │")
    print("│ Translation: 回傳 ``1`` 如果找到，否則回傳 ``0``。        │")
    print("│ Confidence: 0.85                                       │")
    print("│ Glossary matches: 2                                    │")
    print("│ Similar translations found: 1                          │")
    print("│ Iteration: 1/3                                         │")
    print("└" + "─" * 58 + "┘")
    print()
    print("Accept translation? (y/n/r/s): r")
    print("How should it be refined? Use more natural phrasing")
    print()
    print("[Agent processes feedback and generates improved translation...]")
    print()
    print("┌" + "─" * 58 + "┐")
    print("│ Source: Return ``1`` if found, ``0`` otherwise.        │")
    print("│ Translation: 找到時回傳 ``1``，否則回傳 ``0``。           │")
    print("│ Confidence: 0.92                                       │")
    print("│ User feedback: Use more natural phrasing               │")
    print("│ Iteration: 2/3                                         │")
    print("└" + "─" * 58 + "┘")
    print()
    print("Accept translation? (y/n/r/s): y")
    print("✓ Translation accepted and saved to context database")


def example_beeai_plugin():
    """Example of beeai_framework plugin metadata"""
    print("\n🔌 beeai_framework Plugin Example")
    print("=" * 50)
    
    try:
        from pollm.beeai_framework import PLUGIN_METADATA
        
        print("Plugin Metadata for beeai-framework integration:")
        print(f"Framework: {PLUGIN_METADATA['framework']}")
        print(f"Framework URL: {PLUGIN_METADATA['framework_url']}")
        print(f"Agent Class: {PLUGIN_METADATA['agent_class']}")
        print()
        print("Full Metadata:")
        print(json.dumps(PLUGIN_METADATA, indent=2))
        
        print("\nCapabilities:")
        for capability in PLUGIN_METADATA["capabilities"]:
            print(f"  ✓ {capability}")
            
        print(f"\nSupported Actions:")
        for action in PLUGIN_METADATA["supported_actions"]:
            print(f"  • {action}")
            
        print(f"\nSchemas:")
        print(f"  Input: {PLUGIN_METADATA['input_schema']}")
        print(f"  Output: {PLUGIN_METADATA['output_schema']}")
        print(f"  Options: {PLUGIN_METADATA['options_schema']}")
            
    except ImportError:
        print("⚠️  Could not load plugin metadata - beeai_framework not available")


def main():
    """Run all examples"""
    example_agent_usage()
    example_context_management()
    example_workflow_states()
    example_beeai_plugin()
    
    print("\n" + "=" * 50)
    print("📋 Quick Start Checklist:")
    print("  1. Set POLLM_OPENAI_API_KEY environment variable")
    print("  2. Choose LLM provider (OpenAI, OpenRouter, or Ollama)")
    print("  3. Run: pollm agent your_file.po --model qwen2.5:14b")
    print("  4. Follow interactive prompts for translation refinement")
    print("  5. Use --context_file to save translation memory")
    print("\n📖 For detailed documentation, see docs/AGENT_IMPLEMENTATION.md")


if __name__ == "__main__":
    main()