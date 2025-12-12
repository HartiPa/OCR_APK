"""
Inference Engine - Probabilistic extraction logic acting as a lightweight AI assistant.
Uses heuristic scoring to select the best candidates for extraction.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Candidate:
    value: str
    original_text: str
    start: int
    end: int
    score: int
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    debug_info: List[str]

class InferenceEngine:
    """
    intelligent extraction engine using scoring heuristics.
    """
    
    def __init__(self):
        # Common patterns
        self.patterns = {
            'ico': r'\b\d{8}\b',
            'dic': r'\bCZ\d{8,10}\b',
            'date': r'\b\d{1,2}\.\s?\d{1,2}\.\s?\d{4}\b',
            'doc_number': r'\b\d{6,12}\b', # Usually 6-12 digits for doc numbers
            'zip': r'\b\d{3}\s?\d{2}\b',
            'price': r'\d+(?:[.,]\d{2})?\s*(?:Kč|CZK|EUR|€)'
        }
    
    def analyze(self, text: str, field_type: str, keywords: List[str] = None, preferred_section: str = None) -> List[Dict[str, Any]]:
        """
        Analyze text and return ranked candidates for the given field type.
        
        Args:
            text: Full text to search.
            field_type: Type of field ('ico', 'dic', 'date', 'doc_number', 'general').
            keywords: List of context keywords to look for (e.g. ['Datum', 'Vystaveno']).
            preferred_section: 'supplier' (before Odběratel) or 'customer' (after Odběratel).
            
        Returns:
            List of ranked candidates (best first).
        """
        candidates = []
        
        # Determine section boundary if needed
        section_boundary = -1
        if preferred_section:
            match = re.search(r'Odb[ěe]ratel', text, re.IGNORECASE)
            if match:
                section_boundary = match.start()
        
        # 1. Generate Candidates
        raw_matches = self._find_candidates(text, field_type)
        
        # 2. Score Candidates
        for match in raw_matches:
            score, debug = self._score_candidate(match, text, field_type, keywords)
            
            # Apply Section Logic
            if preferred_section == 'supplier' and section_boundary != -1:
                if match['start'] > section_boundary:
                    score -= 50
                    debug.append(f"Wrong section (Supplier expected, found in Customer) (-50)")
                else:
                    score += 20
                    debug.append(f"Correct section (Supplier) (+20)")
                    
            elif preferred_section == 'customer' and section_boundary != -1:
                if match['start'] < section_boundary:
                    score -= 50
                    debug.append(f"Wrong section (Customer expected, found in Supplier) (-50)")
                else:
                    score += 20
                    debug.append(f"Correct section (Customer) (+20)")
            
            # Determine confidence
            confidence = "LOW"
            if score >= 80: confidence = "HIGH"
            elif score >= 50: confidence = "MEDIUM"
            
            candidates.append({
                'value': match['value'],
                'score': score,
                'confidence': confidence,
                'debug': debug,
                'span': (match['start'], match['end'])
            })
        
        # 3. Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates

    def _find_candidates(self, text: str, field_type: str) -> List[Dict[str, Any]]:
        """Find all potential regex matches."""
        matches = []
        pattern = self.patterns.get(field_type)
        
        if not pattern:
            # Fallback for general text finding (simplistic)
            return []
            
        for m in re.finditer(pattern, text, re.IGNORECASE):
            matches.append({
                'value': m.group(),
                'start': m.start(),
                'end': m.end()
            })
        return matches

    def _score_candidate(self, match: Dict, text: str, field_type: str, keywords: List[str]) -> Tuple[int, List[str]]:
        """Calculate score for a single candidate."""
        score = 0
        debug = []
        
        start, end = match['start'], match['end']
        value = match['value']
        
        # Base score for valid format (implied by regex match, but can be refined)
        score += 30
        debug.append("Base format match (+30)")
        
        # Context Analysis (Look at text BEFORE the match)
        context_window = 50
        context_start = max(0, start - context_window)
        context_before = text[context_start:start]
        
        # Keyword proximity
        if keywords:
            for kw in keywords:
                # Regex looking for Keyword followed by optional separator near the match
                # e.g. "IČ:" ... match
                if re.search(rf'{re.escape(kw)}[:=]?\s*$', context_before, re.IGNORECASE):
                    score += 50
                    debug.append(f"Direct label match '{kw}' (+50)")
                    break
                elif kw in context_before: # Simple substring check
                    score += 10 # Lower score for simple presence without adjacency
                    debug.append(f"Nearby keyword '{kw}' (+10)")
        
        # Negative Rules (Exclusions)
        
        # Rule: IČ shouldn't be valid date
        if field_type == 'ico':
            # Check if it looks like a date part (e.g. 20250912)
            if value.startswith("20") and len(value) == 8:
                score -= 10
                debug.append("Looks like YYYYMMDD date (-10)")
                
        # Rule: Document number shouldn't be IČ
        if field_type == 'doc_number':
            # If it matches strict IČ pattern/checksum (simplified here)
            if len(value) == 8:
                 # Check if 'IČ' is right before it
                 if "IČ" in context_before:
                     score -= 50
                     debug.append("Preceded by 'IČ' label (-50)")
        
        # Position Logic (Generic)
        if start < 500:
            score += 10
            debug.append("Header position (+10)")
            
        return score, debug

    def find_best(self, text: str, field_type: str, keywords: List[str] = None, preferred_section: str = None) -> Optional[Dict[str, Any]]:
        """Convenience method to get the single best result."""
        results = self.analyze(text, field_type, keywords, preferred_section)
        if results:
            return results[0]
        return None
