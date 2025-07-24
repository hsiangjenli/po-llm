"""
beeai_framework compatibility layer for po-llm

This module provides a compatibility interface for the beeai_framework,
enabling the IterativeTranslationAgent to work within that ecosystem.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import json

from pollm.agent import IterativeTranslationAgent, MCPTranslationTool, TranslationContext


class BeeAIAgent(ABC):
    """Abstract base class for beeai_framework compatibility"""
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass


class BeeAITranslationAgent(BeeAIAgent):
    """
    beeai_framework compatible wrapper for IterativeTranslationAgent
    
    This class provides the interface expected by beeai_framework while
    wrapping our IterativeTranslationAgent implementation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the internal IterativeTranslationAgent"""
        from openai import OpenAI
        import os
        
        # Setup OpenAI client with config
        api_key = self.config.get("api_key") or os.getenv("POLLM_OPENAI_API_KEY")
        base_url = self.config.get("base_url") or os.getenv("POLLM_BASE_URL", "https://openrouter.ai/api/v1")
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        # Initialize MCP tool and agent
        mcp_tool = MCPTranslationTool()
        self.agent = IterativeTranslationAgent(
            client=client,
            mcp_tool=mcp_tool,
            max_iterations=self.config.get("max_iterations", 3),
            confidence_threshold=self.config.get("confidence_threshold", 0.8)
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process translation request through beeai_framework interface
        
        Expected input_data format:
        {
            "action": "translate_po",
            "po_file_path": "/path/to/file.po",
            "model": "model_name",
            "parameters": {
                "temperature": 0.1,
                "target_entries": "untranslated",
                "auto_confirm": False
            }
        }
        """
        action = input_data.get("action")
        
        if action == "translate_po":
            return self._handle_po_translation(input_data)
        elif action == "translate_single":
            return self._handle_single_translation(input_data)
        elif action == "get_suggestions":
            return self._handle_get_suggestions(input_data)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "supported_actions": ["translate_po", "translate_single", "get_suggestions"]
            }
    
    def _handle_po_translation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PO file translation request"""
        try:
            from pathlib import Path
            
            po_file_path = Path(input_data["po_file_path"])
            model = input_data.get("model", "qwen/qwen-2.5-72b-instruct:free")
            params = input_data.get("parameters", {})
            
            results = self.agent.process_po_file(
                po_file_path=po_file_path,
                model=model,
                temperature=params.get("temperature", 0.1),
                auto_confirm=params.get("auto_confirm", False),
                target_entries=params.get("target_entries", "untranslated")
            )
            
            return {
                "success": True,
                "results": results,
                "po_file_path": str(po_file_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_single_translation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle single entry translation request"""
        try:
            import polib
            
            source_text = input_data["source_text"]
            model = input_data.get("model", "qwen/qwen-2.5-72b-instruct:free")
            
            # Create a temporary POEntry for processing
            entry = polib.POEntry(msgid=source_text)
            context = TranslationContext(source_text=source_text)
            
            translation, confidence = self.agent.generate_translation(
                entry=entry,
                context=context,
                model=model,
                temperature=input_data.get("temperature", 0.1)
            )
            
            return {
                "success": True,
                "translation": translation,
                "confidence": confidence,
                "context": {
                    "glossary_matches": len(context.glossary_matches),
                    "similar_translations": len(context.similar_translations)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _handle_get_suggestions(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle translation suggestions request"""
        try:
            source_text = input_data["source_text"]
            suggestions = self.agent.mcp_tool.get_translation_suggestions(source_text)
            
            return {
                "success": True,
                "suggestions": suggestions
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "iterative_translation",
            "context_awareness", 
            "mcp_integration",
            "interactive_refinement",
            "glossary_integration",
            "multi_llm_support",
            "po_file_processing",
            "confidence_scoring"
        ]
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema for beeai_framework"""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "OpenAI API key"
                },
                "base_url": {
                    "type": "string",
                    "description": "LLM API base URL",
                    "default": "https://openrouter.ai/api/v1"
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "Maximum iterations per translation",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10
                },
                "confidence_threshold": {
                    "type": "number",
                    "description": "Confidence threshold for auto-confirmation",
                    "default": 0.8,
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            },
            "required": ["api_key"]
        }


# Factory function for beeai_framework integration
def create_agent(config: Dict[str, Any]) -> BeeAITranslationAgent:
    """Factory function to create a beeai_framework compatible agent"""
    return BeeAITranslationAgent(config)


# Plugin metadata for beeai_framework discovery
PLUGIN_METADATA = {
    "name": "iterative_translation_agent",
    "version": "1.0.0",
    "description": "AI Agent for Iterative Contextual Translation with MCP integration",
    "author": "po-llm team",
    "capabilities": [
        "iterative_translation",
        "context_awareness", 
        "mcp_integration",
        "interactive_refinement",
        "glossary_integration",
        "multi_llm_support",
        "po_file_processing",
        "confidence_scoring"
    ],
    "supported_actions": [
        "translate_po",
        "translate_single", 
        "get_suggestions"
    ],
    "factory_function": "create_agent"
}