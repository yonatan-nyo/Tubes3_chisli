from typing import List, Tuple

class FuzzyMatcher:
    """Fuzzy string matching using edit distance"""
    
    def __init__(self):
        pass
    
    def similarity_ratio(self, s1: str, s2: str) -> float:
        """Calculate similarity ratio between two strings (0.0 to 1.0)"""
        if not s1 or not s2:
            return 0.0
        
        s1, s2 = s1.lower(), s2.lower()
        
        if s1 == s2:
            return 1.0
        
        # Use normalized edit distance
        distance = self._edit_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        
        if max_len == 0:
            return 1.0
        
        return 1.0 - (distance / max_len)
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate edit distance (Levenshtein distance) between two strings"""
        m, n = len(s1), len(s2)
        
        # Create DP table
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize base cases
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
              dp[0][j] = j
        
        # Fill DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],      # deletion
                        dp[i][j - 1],      # insertion
                        dp[i - 1][j - 1]   # substitution
                    )
        
        return dp[m][n]
    
    def find_best_matches(self, query: str, candidates: List[str], 
                         threshold: float = 0.6, max_results: int = 5) -> List[Tuple[str, float]]:
        """Find best fuzzy matches for query in candidates"""
        matches = []
        
        for candidate in candidates:
            similarity = self.similarity_ratio(query, candidate)
            if similarity >= threshold:
                matches.append((candidate, similarity))
        
        # Sort by similarity (descending) and limit results
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_results]
