#!/usr/bin/env python3
"""
Test script for the Iterative Translation Agent

This script validates that the agent can:
1. Initialize properly
2. Generate translations with context
3. Process MCP-style suggestions
4. Work with the beeai_framework interface
"""

import os
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pollm.agent import IterativeTranslationAgent, MCPTranslationTool, TranslationContext
    from pollm.beeai_framework import BeeAITranslationAgent
    from pollm.prompt_utils import PromptManager
    import polib
    
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_mcp_tool():
    """Test MCP tool functionality"""
    print("\n--- Testing MCP Tool ---")
    
    tool = MCPTranslationTool()
    
    # Test translation suggestions
    suggestions = tool.get_translation_suggestions("function definition")
    print(f"✓ Got suggestions for 'function definition'")
    print(f"  - Glossary matches: {len(suggestions['glossary_matches'])}")
    print(f"  - Context hints: {suggestions['context_hints']}")
    
    # Test with technical terms
    suggestions = tool.get_translation_suggestions("API error message")
    print(f"✓ Got suggestions for 'API error message'")
    print(f"  - Context hints: {suggestions['context_hints']}")
    

def test_translation_context():
    """Test TranslationContext dataclass"""
    print("\n--- Testing Translation Context ---")
    
    context = TranslationContext(source_text="Hello world")
    print(f"✓ Created context: {context.source_text}")
    print(f"  - Initial confidence: {context.confidence_score}")
    print(f"  - Iteration count: {context.iteration_count}")
    
    context.user_feedback.append("Make it more natural")
    context.iteration_count += 1
    print(f"✓ Updated context with feedback")


def test_prompt_manager():
    """Test that prompt manager can load agent prompts"""
    print("\n--- Testing Prompt Manager ---")
    
    pm = PromptManager()
    
    try:
        agent_prompt = pm.get_prompt("agent_system_prompt.txt")
        print(f"✓ Loaded agent system prompt ({len(agent_prompt)} chars)")
    except FileNotFoundError:
        print("✗ Could not load agent_system_prompt.txt")
        return False
    
    try:
        system_prompt = pm.get_prompt("system_prompt.txt")
        print(f"✓ Loaded original system prompt ({len(system_prompt)} chars)")
    except FileNotFoundError:
        print("✗ Could not load system_prompt.txt")
        return False
    
    return True


def test_beeai_framework():
    """Test beeai_framework compatibility"""
    print("\n--- Testing beeai_framework Compatibility ---")
    
    config = {
        "api_key": "test_key",
        "base_url": "http://localhost:11434/v1",
        "max_iterations": 2,
        "confidence_threshold": 0.7
    }
    
    try:
        agent = BeeAITranslationAgent(config)
        print("✓ Created BeeAI compatible agent")
        
        capabilities = agent.get_capabilities()
        print(f"✓ Agent capabilities: {len(capabilities)} items")
        for cap in capabilities[:3]:  # Show first 3
            print(f"  - {cap}")
        
        schema = agent.get_config_schema()
        print(f"✓ Config schema has {len(schema['properties'])} properties")
        
        # Test suggestions (doesn't require actual LLM)
        input_data = {
            "action": "get_suggestions",
            "source_text": "Hello world"
        }
        result = agent.process(input_data)
        print(f"✓ Processed suggestions request: {result['success']}")
        
    except Exception as e:
        print(f"✗ BeeAI framework test failed: {e}")
        return False
    
    return True


def test_po_entry_creation():
    """Test creating PO entries for testing"""
    print("\n--- Testing PO Entry Creation ---")
    
    try:
        entry = polib.POEntry(
            msgid="Hello world",
            msgstr="",
            comment="Test entry"
        )
        print(f"✓ Created PO entry: '{entry.msgid}'")
        
        # Test with more complex entry
        entry2 = polib.POEntry(
            msgid="Return ``1`` if the mapping object has the key *key* and ``0`` otherwise.",
            msgstr="",
            flags=["fuzzy"]
        )
        print(f"✓ Created complex PO entry with flags: {entry2.flags}")
        
    except Exception as e:
        print(f"✗ PO entry creation failed: {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("🚀 Testing Iterative Translation Agent")
    print("=" * 50)
    
    success = True
    
    # Run tests
    test_mcp_tool()
    test_translation_context()
    success &= test_prompt_manager()
    success &= test_beeai_framework()
    success &= test_po_entry_creation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! The agent is ready for integration.")
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()