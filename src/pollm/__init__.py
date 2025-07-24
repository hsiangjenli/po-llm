def hello() -> str:
    return "Hello from python-package-template!"


# Re-export main agent classes for convenience
try:
    from .agent import IterativeTranslationAgent, MCPTranslationTool, TranslationContext
    from .beeai_framework import BeeAITranslationAgent, create_agent
    
    __all__ = [
        "hello",
        "IterativeTranslationAgent", 
        "MCPTranslationTool",
        "TranslationContext",
        "BeeAITranslationAgent",
        "create_agent"
    ]
except ImportError:
    # Graceful degradation if dependencies are missing
    __all__ = ["hello"]
