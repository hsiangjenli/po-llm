"""
beeai_framework compatibility layer for po-llm

This module provides a proper integration with the beeai-framework
(https://github.com/i-am-bee/beeai-framework), enabling the IterativeTranslationAgent
to work within that ecosystem as a proper BaseAgent.
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path

# Try to import beeai_framework components
try:
    from beeai_framework.agents import BaseAgent, AgentMeta
    from beeai_framework.agents.types import BaseAgentRunOptions
    from beeai_framework.context import Run, RunContext
    from beeai_framework.emitter import Emitter
    from beeai_framework.memory import BaseMemory, UnconstrainedMemory
    from beeai_framework.backend import AnyMessage, AssistantMessage, UserMessage
    BEEAI_AVAILABLE = True
except ImportError:
    BEEAI_AVAILABLE = False
    # Fallback types when beeai_framework is not available
    BaseAgent = object
    AgentMeta = object
    BaseAgentRunOptions = object
    Run = object
    RunContext = object
    Emitter = object
    BaseMemory = object
    UnconstrainedMemory = object
    AnyMessage = object
    AssistantMessage = object
    UserMessage = object

# Try to import pydantic for data models
try:
    from pydantic import BaseModel, Field, InstanceOf
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback BaseModel when pydantic is not available
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def Field(**kwargs):
        return None
        
    def InstanceOf(cls):
        return cls

from pollm.agent import IterativeTranslationAgent, MCPTranslationTool, TranslationContext


# Input/Output models for the translation agent
class TranslationRunInput(BaseModel):
    """Input for translation agent runs"""
    def __init__(self, po_file_path: Path, model: str = "qwen/qwen-2.5-72b-instruct:free", 
                 temperature: float = 0.1, auto_confirm: bool = False, target_entries: str = "untranslated"):
        if PYDANTIC_AVAILABLE:
            super().__init__(po_file_path=po_file_path, model=model, temperature=temperature, 
                           auto_confirm=auto_confirm, target_entries=target_entries)
        else:
            self.po_file_path = po_file_path
            self.model = model
            self.temperature = temperature
            self.auto_confirm = auto_confirm
            self.target_entries = target_entries


class TranslationRunOptions(BaseAgentRunOptions if BEEAI_AVAILABLE else BaseModel):
    """Run options for translation agent"""
    def __init__(self, max_iterations: int = 3, confidence_threshold: float = 0.8, signal=None):
        if BEEAI_AVAILABLE:
            super().__init__(signal=signal)
            self.max_iterations = max_iterations
            self.confidence_threshold = confidence_threshold
        else:
            self.max_iterations = max_iterations
            self.confidence_threshold = confidence_threshold
            self.signal = signal


class TranslationState(BaseModel):
    """State tracking for translation process"""
    def __init__(self, entries_processed: int = 0, entries_accepted: int = 0, 
                 entries_skipped: int = 0, avg_confidence: float = 0.0, 
                 context_file_path: Optional[str] = None):
        if PYDANTIC_AVAILABLE:
            super().__init__(entries_processed=entries_processed, entries_accepted=entries_accepted,
                           entries_skipped=entries_skipped, avg_confidence=avg_confidence,
                           context_file_path=context_file_path)
        else:
            self.entries_processed = entries_processed
            self.entries_accepted = entries_accepted
            self.entries_skipped = entries_skipped
            self.avg_confidence = avg_confidence
            self.context_file_path = context_file_path


class TranslationRunOutput(BaseModel):
    """Output from translation agent runs"""
    def __init__(self, message: str, state: TranslationState, success: bool = True):
        if PYDANTIC_AVAILABLE:
            super().__init__(message=message, state=state, success=success)
        else:
            self.message = message
            self.state = state
            self.success = success


class IterativeTranslationBeeAIAgent(BaseAgent[TranslationRunOutput] if BEEAI_AVAILABLE else object):
    """
    beeai_framework compatible agent for Iterative Contextual Translation
    
    This class properly extends BaseAgent from beeai-framework to provide
    iterative translation capabilities within that ecosystem.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if BEEAI_AVAILABLE:
            super().__init__()
        
        self.config = config or {}
        self.agent = None
        self._memory = UnconstrainedMemory() if BEEAI_AVAILABLE else None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the internal IterativeTranslationAgent"""
        from openai import OpenAI
        
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

    @property
    def memory(self) -> BaseMemory:
        """Return the agent's memory"""
        return self._memory

    @memory.setter
    def memory(self, memory: BaseMemory) -> None:
        """Set the agent's memory"""
        self._memory = memory

    def _create_emitter(self) -> Emitter:
        """Create emitter for the agent"""
        if not BEEAI_AVAILABLE:
            raise ImportError("beeai_framework is required for emitter functionality")
        
        return Emitter.root().child(
            namespace=["agent", "iterative_translation"],
            creator=self,
        )

    def run(
        self,
        run_input: TranslationRunInput,
        options: TranslationRunOptions | None = None,
    ) -> Run[TranslationRunOutput]:
        """
        Run the iterative translation process
        
        Args:
            run_input: Translation input parameters
            options: Run options including max_iterations and confidence_threshold
            
        Returns:
            Run object containing translation results
        """
        if not BEEAI_AVAILABLE:
            raise ImportError("beeai_framework is required for run functionality")

        async def handler(context: RunContext) -> TranslationRunOutput:
            try:
                # Process the PO file using our iterative agent
                results = self.agent.process_po_file(
                    po_file_path=run_input.po_file_path,
                    model=run_input.model,
                    temperature=run_input.temperature,
                    auto_confirm=run_input.auto_confirm,
                    target_entries=run_input.target_entries
                )
                
                # Calculate summary statistics
                total_processed = len(results.get("translations", []))
                accepted = sum(1 for t in results.get("translations", []) if t.get("accepted", False))
                skipped = total_processed - accepted
                avg_conf = sum(t.get("confidence", 0) for t in results.get("translations", [])) / max(total_processed, 1)
                
                state = TranslationState(
                    entries_processed=total_processed,
                    entries_accepted=accepted,
                    entries_skipped=skipped,
                    avg_confidence=avg_conf,
                    context_file_path=str(results.get("context_file")) if results.get("context_file") else None
                )
                
                message = f"Processed {total_processed} entries, accepted {accepted}, average confidence {avg_conf:.2f}"
                
                # Add result to memory if available
                if self.memory:
                    await self.memory.add(AssistantMessage(message))
                
                return TranslationRunOutput(
                    message=message,
                    state=state,
                    success=True
                )
                
            except Exception as e:
                error_msg = f"Translation failed: {str(e)}"
                
                # Add error to memory if available  
                if self.memory:
                    await self.memory.add(AssistantMessage(error_msg))
                
                return TranslationRunOutput(
                    message=error_msg,
                    state=TranslationState(),
                    success=False
                )

        return self._to_run(
            handler, 
            signal=options.signal if options else None, 
            run_params={"input": run_input, "options": options}
        )

    @property
    def meta(self) -> AgentMeta:
        """Return agent metadata"""
        if not BEEAI_AVAILABLE:
            raise ImportError("beeai_framework is required for meta functionality")
            
        return AgentMeta(
            name="IterativeTranslationAgent",
            description="AI Agent for Iterative Contextual Translation with MCP integration",
            tools=[],  # Tools are handled internally by the IterativeTranslationAgent
            extra_description="Provides iterative translation with context awareness, confidence scoring, and user feedback integration"
        )


# Factory function for creating the agent
def create_translation_agent(config: Dict[str, Any]) -> IterativeTranslationBeeAIAgent:
    """Factory function to create a beeai_framework compatible translation agent"""
    return IterativeTranslationBeeAIAgent(config)


# Legacy compatibility wrapper for the old interface
class BeeAITranslationAgent:
    """
    Legacy compatibility wrapper - DEPRECATED
    
    Use IterativeTranslationBeeAIAgent directly for proper beeai_framework integration.
    This wrapper is maintained for backward compatibility only.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        import warnings
        warnings.warn(
            "BeeAITranslationAgent is deprecated. Use IterativeTranslationBeeAIAgent for proper beeai_framework integration.",
            DeprecationWarning,
            stacklevel=2
        )
        self.agent = IterativeTranslationBeeAIAgent(config)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy process method - converts to new interface"""
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
        """Handle PO file translation request via legacy interface"""
        try:
            po_file_path = Path(input_data["po_file_path"])
            model = input_data.get("model", "qwen/qwen-2.5-72b-instruct:free")
            params = input_data.get("parameters", {})
            
            results = self.agent.agent.process_po_file(
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
        """Handle single entry translation request via legacy interface"""
        try:
            import polib
            
            source_text = input_data["source_text"]
            model = input_data.get("model", "qwen/qwen-2.5-72b-instruct:free")
            
            # Create a temporary POEntry for processing
            entry = polib.POEntry(msgid=source_text)
            context = TranslationContext(source_text=source_text)
            
            translation, confidence = self.agent.agent.generate_translation(
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
        """Handle translation suggestions request via legacy interface"""
        try:
            source_text = input_data["source_text"]
            suggestions = self.agent.agent.mcp_tool.get_translation_suggestions(source_text)
            
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


# Factory function for legacy compatibility
def create_agent(config: Dict[str, Any]) -> BeeAITranslationAgent:
    """
    Factory function for legacy compatibility - DEPRECATED
    
    Use create_translation_agent() for proper beeai_framework integration.
    """
    import warnings
    warnings.warn(
        "create_agent() is deprecated. Use create_translation_agent() for proper beeai_framework integration.",
        DeprecationWarning,
        stacklevel=2
    )
    return BeeAITranslationAgent(config)


# Plugin metadata for beeai_framework discovery
PLUGIN_METADATA = {
    "name": "iterative_translation_agent",
    "version": "1.0.0",
    "description": "AI Agent for Iterative Contextual Translation with MCP integration",
    "author": "po-llm team",
    "framework": "beeai_framework",
    "framework_url": "https://github.com/i-am-bee/beeai-framework",
    "agent_class": "IterativeTranslationBeeAIAgent",
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
    "factory_function": "create_translation_agent",
    "input_schema": "TranslationRunInput",
    "output_schema": "TranslationRunOutput",
    "options_schema": "TranslationRunOptions"
}