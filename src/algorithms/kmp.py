from typing import List

class KMPMatcher:
    """Knuth-Morris-Pratt string matching algorithm"""
    
    def __init__(self):
        pass
    
    def search(self, text: str, pattern: str) -> List[int]:
        """Search for pattern in text using KMP algorithm"""
        if not pattern or not text:
            return []
        
        pattern = pattern.lower()
        text = text.lower()
        
        # Build failure function
        failure = self._build_failure_function(pattern)
        
        matches = []
        i = 0  # text index
        j = 0  # pattern index
        
        while i < len(text):
            if text[i] == pattern[j]:
                i += 1
                j += 1
                
                if j == len(pattern):
                    matches.append(i - j)
                    j = failure[j - 1]
            else:
                if j != 0:
                    j = failure[j - 1]
                else:
                    i += 1
        
        return matches
    
    def _build_failure_function(self, pattern: str) -> List[int]:
        """Build the failure function for KMP"""
        failure = [0] * len(pattern)
        j = 0
        
        for i in range(1, len(pattern)):
            while j > 0 and pattern[i] != pattern[j]:
                j = failure[j - 1]
            
            if pattern[i] == pattern[j]:
                j += 1
            
            failure[i] = j
        
        return failure
