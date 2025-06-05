from typing import List, Dict

class BoyerMooreMatcher:
    """Boyer-Moore string matching algorithm"""
    
    def __init__(self):
        pass
    
    def search(self, text: str, pattern: str) -> List[int]:
        """Search for pattern in text using Boyer-Moore algorithm"""
        if not pattern or not text:
            return []
        
        pattern = pattern.lower()
        text = text.lower()
        
        # Build bad character table
        bad_char = self._build_bad_char_table(pattern)
        
        matches = []
        shift = 0
        
        while shift <= len(text) - len(pattern):
            j = len(pattern) - 1
            
            # Keep reducing j while characters match
            while j >= 0 and pattern[j] == text[shift + j]:
                j -= 1
            
            if j < 0:
                # Pattern found
                matches.append(shift)
                
                # Shift pattern to align with next character
                if shift + len(pattern) < len(text):
                    shift += len(pattern) - bad_char.get(text[shift + len(pattern)], -1)
                else:
                    shift += 1
            else:
                # Shift pattern based on bad character rule
                shift += max(1, j - bad_char.get(text[shift + j], -1))
        
        return matches
    
    def _build_bad_char_table(self, pattern: str) -> Dict[str, int]:
        """Build bad character table for Boyer-Moore"""
        bad_char = {}
        
        for i in range(len(pattern)):
            bad_char[pattern[i]] = i
        
        return bad_char
