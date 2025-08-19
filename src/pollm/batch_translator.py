"""
Batch translation module for optimized token usage in PO file translation.

This module implements batch processing to significantly reduce token usage
by processing multiple entries in a single API call with optimized prompts.
"""
import json
import re
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import hashlib

import polib


class TranslationCache:
    """In-memory translation cache with optional persistence."""
    
    def __init__(self):
        self.cache: Dict[str, str] = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def normalize_msgid(self, msgid: str) -> str:
        """Normalize msgid for cache key generation."""
        # Remove leading/trailing whitespace
        normalized = msgid.strip()
        # Normalize whitespace sequences to single spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        # Simple HTML entity normalization (can be extended)
        normalized = normalized.replace('&nbsp;', ' ')
        return normalized
    
    def get_cache_key(self, msgid: str) -> str:
        """Generate cache key from normalized msgid."""
        normalized = self.normalize_msgid(msgid)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def get(self, msgid: str) -> Optional[str]:
        """Get translation from cache."""
        key = self.get_cache_key(msgid)
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        self.miss_count += 1
        return None
    
    def set(self, msgid: str, msgstr: str):
        """Store translation in cache."""
        key = self.get_cache_key(msgid)
        self.cache[key] = msgstr
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        return {
            'hits': self.hit_count,
            'misses': self.miss_count,
            'total': total,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache)
        }


class GlossaryManager:
    """Manages glossary subset generation for batches."""
    
    def __init__(self, search_glossary_func):
        self.search_glossary = search_glossary_func
    
    def get_batch_glossary(self, entries: List[polib.POEntry], max_terms: int = 100) -> List[Dict]:
        """Get relevant glossary terms for a batch of entries."""
        # Collect all unique terms from all entries in batch
        all_terms = []
        seen_terms = set()
        
        for entry in entries:
            entry_terms = self.search_glossary(entry.msgid)
            for term in entry_terms:
                term_key = term.get('原文', '').lower()
                if term_key and term_key not in seen_terms:
                    all_terms.append(term)
                    seen_terms.add(term_key)
        
        # Sort by term length (longer terms first) and limit
        all_terms.sort(key=lambda x: len(x.get('原文', '')), reverse=True)
        return all_terms[:max_terms]


class ContextManager:
    """Manages translation context using recent translation pairs."""
    
    def __init__(self, max_context_pairs: int = 20):
        self.max_context_pairs = max_context_pairs
        self.recent_pairs: List[Tuple[str, str]] = []
    
    def add_translation_pair(self, msgid: str, msgstr: str):
        """Add a translation pair to context."""
        self.recent_pairs.append((msgid, msgstr))
        # Keep only the most recent pairs
        if len(self.recent_pairs) > self.max_context_pairs:
            self.recent_pairs = self.recent_pairs[-self.max_context_pairs:]
    
    def get_context_text(self) -> str:
        """Get formatted context text for prompts."""
        if not self.recent_pairs:
            return ""
        
        context_lines = []
        for msgid, msgstr in self.recent_pairs[-10:]:  # Use last 10 pairs
            # Truncate long entries
            msgid_short = (msgid[:100] + "...") if len(msgid) > 100 else msgid
            msgstr_short = (msgstr[:100] + "...") if len(msgstr) > 100 else msgstr
            context_lines.append(f"EN: {msgid_short}")
            context_lines.append(f"ZH: {msgstr_short}")
        
        return "\n".join(context_lines)


class BatchTranslator:
    """Main batch translator class."""
    
    def __init__(self, client, model: str = "qwen/qwen-2.5-72b-instruct:free", 
                 temperature: float = 0.1, max_context_pairs: int = 20):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.cache = TranslationCache()
        self.glossary_manager = None  # Will be set when search_glossary is available
        self.context_manager = ContextManager(max_context_pairs)
        
    def set_glossary_function(self, search_glossary_func):
        """Set the glossary search function."""
        self.glossary_manager = GlossaryManager(search_glossary_func)
    
    def create_batch_prompt(self, entries: List[polib.POEntry], prompt_type: str = "translate") -> str:
        """Create optimized batch prompt."""
        # Get glossary subset for this batch
        glossary_terms = []
        if self.glossary_manager:
            glossary_terms = self.glossary_manager.get_batch_glossary(entries)
        
        # Format glossary
        glossary_text = ""
        if glossary_terms:
            glossary_lines = []
            for term in glossary_terms:
                original = term.get('原文', '')
                translation = term.get('翻譯', '')
                if original and translation:
                    glossary_lines.append(f"{original} -> {translation}")
            if glossary_lines:
                glossary_text = f"優先詞彙對照:\n" + "\n".join(glossary_lines[:50])  # Limit to 50 terms
        
        # Get recent context
        context_text = self.context_manager.get_context_text()
        context_section = f"\n\n最近翻譯參考:\n{context_text}" if context_text else ""
        
        # Create entries JSON for the batch
        entries_data = []
        for i, entry in enumerate(entries):
            entries_data.append({
                "id": i,
                "msgid": entry.msgid
            })
        
        entries_json = json.dumps(entries_data, ensure_ascii=False, indent=2)
        
        # Create the batch prompt
        batch_prompt = f"""你是專業翻譯助理。請將以下英文內容翻譯成符合臺灣人習慣的繁體中文。

規則:
1. 保持RST格式完整 
2. 保留程式碼和專有名詞不變
3. 按照原文語序翻譯，保持自然流暢
4. 優先使用提供的詞彙對照

{glossary_text}{context_section}

請翻譯以下內容，以JSON格式回傳: {{"id": "翻譯結果", ...}}

待翻譯內容:
{entries_json}

回傳格式範例:
{{"0": "翻譯結果1", "1": "翻譯結果2"}}
"""
        return batch_prompt
    
    def parse_json_response(self, response_text: str) -> Dict[str, str]:
        """Parse JSON response from the model, handling various formats."""
        # Remove code fences if present
        cleaned = re.sub(r'```(?:json)?\s*\n?', '', response_text.strip())
        cleaned = re.sub(r'\n?```\s*$', '', cleaned)
        
        try:
            result = json.loads(cleaned)
            # Convert all keys to strings and values to strings
            return {str(k): str(v) for k, v in result.items()}
        except json.JSONDecodeError as e:
            # Try to extract JSON from text
            json_match = re.search(r'\{[^}]*\}', cleaned, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return {str(k): str(v) for k, v in result.items()}
                except json.JSONDecodeError:
                    pass
            
            # Fallback: return empty dict and log error
            print(f"Failed to parse JSON response: {e}")
            print(f"Response text: {response_text[:500]}...")
            return {}
    
    def translate_batch(self, entries: List[polib.POEntry], prompt_type: str = "translate") -> Dict[int, str]:
        """Translate a batch of entries."""
        # Check cache first
        cache_results = {}
        uncached_entries = []
        uncached_indices = []
        
        for i, entry in enumerate(entries):
            cached = self.cache.get(entry.msgid)
            if cached:
                cache_results[i] = cached
            else:
                uncached_entries.append(entry)
                uncached_indices.append(i)
        
        results = cache_results.copy()
        
        # Process uncached entries if any
        if uncached_entries:
            batch_prompt = self.create_batch_prompt(uncached_entries, prompt_type)
            
            try:
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": batch_prompt}],
                    model=self.model,
                    temperature=self.temperature,
                )
                
                response_text = response.choices[0].message.content
                parsed_results = self.parse_json_response(response_text)
                
                # Map results back to original indices
                for local_idx, global_idx in enumerate(uncached_indices):
                    if str(local_idx) in parsed_results:
                        msgstr = parsed_results[str(local_idx)]
                        results[global_idx] = msgstr
                        # Cache the result
                        self.cache.set(uncached_entries[local_idx].msgid, msgstr)
                        # Add to context
                        self.context_manager.add_translation_pair(
                            uncached_entries[local_idx].msgid, msgstr
                        )
            
            except Exception as e:
                print(f"Error in batch translation: {e}")
                # Return empty results for failed entries
                for global_idx in uncached_indices:
                    if global_idx not in results:
                        results[global_idx] = ""
        
        return results