"""
AI Agent for Iterative Contextual Translation

This module implements an iterative translation agent that enables:
- MCP-style tool integration for searching suitable translations
- Interactive confirmation and refinement of translation context
- Context-aware translation using LLM providers
- Iterative workflow for improved translation quality
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import polib
from openai import OpenAI

from pollm.glossary import search_glossary
from pollm.prompt_utils import PromptManager


@dataclass
class TranslationContext:
    """Manages context across translation iterations"""
    source_text: str
    target_text: str = ""
    confidence_score: float = 0.0
    iteration_count: int = 0
    user_feedback: List[str] = None
    glossary_matches: List[Dict] = None
    similar_translations: List[Dict] = None
    
    def __post_init__(self):
        if self.user_feedback is None:
            self.user_feedback = []
        if self.glossary_matches is None:
            self.glossary_matches = []
        if self.similar_translations is None:
            self.similar_translations = []


class MCPTranslationTool:
    """MCP-style tool for searching and suggesting translations"""
    
    def __init__(self, context_db: Optional[Dict] = None):
        self.context_db = context_db or {}
        
    def search_similar_translations(self, source_text: str, limit: int = 5) -> List[Dict]:
        """Search for similar translations in context database"""
        similar = []
        source_lower = source_text.lower()
        
        for src, translation_data in self.context_db.items():
            src_lower = src.lower()
            # Simple similarity check - could be enhanced with more sophisticated algorithms
            if any(word in src_lower for word in source_lower.split() if len(word) > 3):
                similar.append({
                    "source": src,
                    "target": translation_data.get("target", ""),
                    "confidence": translation_data.get("confidence", 0.0),
                    "context": translation_data.get("context", {})
                })
        
        return sorted(similar, key=lambda x: x["confidence"], reverse=True)[:limit]
    
    def get_translation_suggestions(self, source_text: str) -> Dict[str, Any]:
        """Get comprehensive translation suggestions"""
        return {
            "glossary_matches": search_glossary(source_text),
            "similar_translations": self.search_similar_translations(source_text),
            "context_hints": self._extract_context_hints(source_text)
        }
    
    def _extract_context_hints(self, source_text: str) -> List[str]:
        """Extract contextual hints from source text"""
        hints = []
        
        # Check for technical terms
        if any(term in source_text.lower() for term in ['api', 'function', 'method', 'class', 'object']):
            hints.append("technical_documentation")
        
        # Check for UI elements
        if any(term in source_text.lower() for term in ['button', 'menu', 'dialog', 'window', 'click']):
            hints.append("user_interface")
        
        # Check for error messages
        if any(term in source_text.lower() for term in ['error', 'exception', 'warning', 'failed']):
            hints.append("error_message")
            
        return hints


class IterativeTranslationAgent:
    """Main agent for iterative contextual translation"""
    
    def __init__(
        self,
        client: OpenAI,
        prompt_manager: PromptManager = None,
        mcp_tool: MCPTranslationTool = None,
        max_iterations: int = 3,
        confidence_threshold: float = 0.8
    ):
        self.client = client
        self.prompt_manager = prompt_manager or PromptManager()
        self.mcp_tool = mcp_tool or MCPTranslationTool()
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
        self.session_context = {}
        
    def generate_translation(
        self,
        entry: polib.POEntry,
        context: TranslationContext,
        model: str = "qwen/qwen-2.5-72b-instruct:free",
        temperature: float = 0.1
    ) -> Tuple[str, float]:
        """Generate translation using LLM with context"""
        
        # Prepare context-aware prompt
        suggestions = self.mcp_tool.get_translation_suggestions(entry.msgid)
        
        context_prompt = self._build_context_prompt(
            entry.msgid,
            suggestions,
            context
        )
        
        messages = [
            {
                "role": "system",
                "content": self.prompt_manager.get_prompt("agent_system_prompt.txt")
            },
            {
                "role": "user", 
                "content": context_prompt
            }
        ]
        
        # Add previous iterations context
        if context.iteration_count > 0:
            messages.append({
                "role": "assistant",
                "content": f"Previous translation attempt: {context.target_text}"
            })
            
            if context.user_feedback:
                messages.append({
                    "role": "user",
                    "content": f"User feedback: {'; '.join(context.user_feedback)}"
                })
        
        response = self.client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature
        )
        
        translation = response.choices[0].message.content.strip()
        
        # Calculate confidence score (simplified heuristic)
        confidence = self._calculate_confidence(translation, suggestions)
        
        return translation, confidence
    
    def _build_context_prompt(
        self,
        source_text: str,
        suggestions: Dict[str, Any],
        context: TranslationContext
    ) -> str:
        """Build context-aware prompt for translation"""
        
        prompt_parts = [
            f"Source text to translate: {source_text}",
            ""
        ]
        
        # Add glossary matches
        if suggestions["glossary_matches"]:
            prompt_parts.append("Relevant glossary terms:")
            for match in suggestions["glossary_matches"]:
                prompt_parts.append(f"- {match['原文']} → {match['翻譯']}")
            prompt_parts.append("")
        
        # Add similar translations
        if suggestions["similar_translations"]:
            prompt_parts.append("Similar translations for reference:")
            for similar in suggestions["similar_translations"]:
                prompt_parts.append(f"- \"{similar['source']}\" → \"{similar['target']}\"")
            prompt_parts.append("")
        
        # Add context hints
        if suggestions["context_hints"]:
            prompt_parts.append(f"Context type: {', '.join(suggestions['context_hints'])}")
            prompt_parts.append("")
        
        # Add iteration-specific guidance
        if context.iteration_count > 0:
            prompt_parts.append("This is a refinement iteration. Please consider:")
            prompt_parts.append("- Previous translation accuracy")
            prompt_parts.append("- User feedback provided")
            prompt_parts.append("- Consistency with established terminology")
            prompt_parts.append("")
        
        prompt_parts.append("Please provide a natural, accurate Traditional Chinese translation.")
        
        return "\n".join(prompt_parts)
    
    def _calculate_confidence(self, translation: str, suggestions: Dict[str, Any]) -> float:
        """Calculate confidence score for translation"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence if glossary terms are used correctly
        glossary_matches = suggestions.get("glossary_matches", [])
        if glossary_matches:
            for match in glossary_matches:
                if match["翻譯"] in translation:
                    confidence += 0.1
        
        # Boost confidence if similar translations exist
        if suggestions.get("similar_translations"):
            confidence += 0.1
            
        # Penalize very short or very long translations
        if len(translation) < 5 or len(translation) > 200:
            confidence -= 0.1
            
        return min(1.0, max(0.0, confidence))
    
    def confirm_translation(
        self,
        entry: polib.POEntry,
        translation: str,
        context: TranslationContext,
        auto_confirm: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Interactive confirmation of translation"""
        
        if auto_confirm and context.confidence_score >= self.confidence_threshold:
            return True, None
        
        print(f"\n{'='*60}")
        print(f"Source: {entry.msgid}")
        print(f"Translation: {translation}")
        print(f"Confidence: {context.confidence_score:.2f}")
        
        if context.glossary_matches:
            print(f"Glossary matches: {len(context.glossary_matches)}")
        
        if context.similar_translations:
            print(f"Similar translations found: {len(context.similar_translations)}")
        
        print(f"Iteration: {context.iteration_count + 1}/{self.max_iterations}")
        print(f"{'='*60}")
        
        while True:
            choice = input("Accept translation? (y/n/r/s): ").strip().lower()
            
            if choice == 'y':
                return True, None
            elif choice == 'n':
                feedback = input("What should be improved? ")
                return False, feedback
            elif choice == 'r':
                feedback = input("How should it be refined? ")
                return False, feedback
            elif choice == 's':
                print("Skipping this entry...")
                return True, "SKIP"
            else:
                print("Please enter 'y' (yes), 'n' (no), 'r' (refine), or 's' (skip)")
    
    def process_po_file(
        self,
        po_file_path: Path,
        model: str = "qwen/qwen-2.5-72b-instruct:free",
        temperature: float = 0.1,
        auto_confirm: bool = False,
        target_entries: str = "untranslated"  # "untranslated", "fuzzy", "all"
    ) -> Dict[str, Any]:
        """Process PO file with iterative translation"""
        
        po = polib.pofile(po_file_path)
        
        # Select entries to process
        if target_entries == "untranslated":
            entries = po.untranslated_entries()
        elif target_entries == "fuzzy":
            entries = po.fuzzy_entries()
        else:
            entries = po
        
        results = {
            "processed": 0,
            "accepted": 0,
            "skipped": 0,
            "failed": 0,
            "total_iterations": 0
        }
        
        print(f"Processing {len(entries)} entries with iterative translation agent...")
        
        for i, entry in enumerate(entries):
            print(f"\nEntry {i+1}/{len(entries)}")
            
            context = TranslationContext(source_text=entry.msgid)
            translation_accepted = False
            
            # Iterative refinement loop
            for iteration in range(self.max_iterations):
                context.iteration_count = iteration
                
                # Generate translation
                translation, confidence = self.generate_translation(
                    entry, context, model, temperature
                )
                
                context.target_text = translation
                context.confidence_score = confidence
                
                # Get confirmation
                accepted, feedback = self.confirm_translation(
                    entry, translation, context, auto_confirm
                )
                
                if feedback == "SKIP":
                    results["skipped"] += 1
                    translation_accepted = True
                    break
                elif accepted:
                    entry.msgstr = translation
                    if "fuzzy" in entry.flags:
                        entry.flags.remove("fuzzy")
                    
                    # Update session context for future translations
                    self.session_context[entry.msgid] = {
                        "target": translation,
                        "confidence": confidence,
                        "context": asdict(context)
                    }
                    
                    results["accepted"] += 1
                    translation_accepted = True
                    break
                else:
                    # Add feedback and continue iteration
                    if feedback:
                        context.user_feedback.append(feedback)
                    
                    results["total_iterations"] += 1
                    
                    if iteration == self.max_iterations - 1:
                        print(f"Max iterations reached for entry: {entry.msgid}")
                        results["failed"] += 1
            
            if translation_accepted:
                results["processed"] += 1
                
                # Update MCP tool context database
                self.mcp_tool.context_db.update(self.session_context)
        
        # Save the updated PO file
        po.save()
        
        return results
    
    def save_session_context(self, output_path: Path):
        """Save session context for future use"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.session_context, f, ensure_ascii=False, indent=2)
    
    def load_session_context(self, input_path: Path):
        """Load previous session context"""
        if input_path.exists():
            with open(input_path, 'r', encoding='utf-8') as f:
                self.session_context = json.load(f)
                self.mcp_tool.context_db.update(self.session_context)