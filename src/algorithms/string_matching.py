from typing import List, Tuple, Dict
import time
from collections import defaultdict, deque

class KMPAlgorithm:
    """Knuth-Morris-Pratt string matching algorithm"""
    
    @staticmethod
    def compute_lps(pattern: str) -> List[int]:
        """Compute Longest Proper Prefix which is also Suffix array"""
        m = len(pattern)
        lps = [0] * m
        length = 0
        i = 1
        
        while i < m:
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1
        return lps
    
    @staticmethod
    def search(text: str, pattern: str) -> List[int]:
        """Find all occurrences of pattern in text using KMP"""
        if not pattern or not text:
            return []
        
        n = len(text)
        m = len(pattern)
        
        # Convert to lowercase for case-insensitive search
        text = text.lower()
        pattern = pattern.lower()
        
        lps = KMPAlgorithm.compute_lps(pattern)
        occurrences = []
        
        i = 0  # index for text
        j = 0  # index for pattern
        
        while i < n:
            if pattern[j] == text[i]:
                i += 1
                j += 1
            
            if j == m:
                occurrences.append(i - j)
                j = lps[j - 1]
            elif i < n and pattern[j] != text[i]:
                if j != 0:
                    j = lps[j - 1]
                else:
                    i += 1
        
        return occurrences


class BoyerMooreAlgorithm:
    """Boyer-Moore string matching algorithm"""
    
    @staticmethod
    def bad_character_table(pattern: str) -> Dict[str, int]:
        """Create bad character table for Boyer-Moore"""
        table = {}
        m = len(pattern)
        
        for i in range(m):
            table[pattern[i]] = i
        
        return table
    
    @staticmethod
    def good_suffix_table(pattern: str) -> List[int]:
        """Create good suffix table for Boyer-Moore"""
        m = len(pattern)
        good_suffix = [0] * m
        last_prefix_position = m
        
        # Fill good suffix array
        for i in range(m - 1, -1, -1):
            if BoyerMooreAlgorithm.is_prefix(pattern, i + 1):
                last_prefix_position = i + 1
            good_suffix[i] = last_prefix_position + (m - 1 - i)
        
        # Fill for suffixes
        for i in range(m - 1):
            suffix_length = BoyerMooreAlgorithm.suffix_length(pattern, i)
            good_suffix[m - 1 - suffix_length] = m - 1 - i + suffix_length
        
        return good_suffix
    
    @staticmethod
    def is_prefix(pattern: str, p: int) -> bool:
        """Check if pattern[p:] is a prefix of pattern"""
        j = 0
        for i in range(p, len(pattern)):
            if pattern[i] != pattern[j]:
                return False
            j += 1
        return True
    
    @staticmethod
    def suffix_length(pattern: str, p: int) -> int:
        """Length of the longest suffix of pattern ending at p"""
        length = 0
        i = p
        j = len(pattern) - 1
        
        while i >= 0 and pattern[i] == pattern[j]:
            length += 1
            i -= 1
            j -= 1
        
        return length
    
    @staticmethod
    def search(text: str, pattern: str) -> List[int]:
        """Find all occurrences of pattern in text using Boyer-Moore"""
        if not pattern or not text:
            return []
        
        n = len(text)
        m = len(pattern)
        
        # Convert to lowercase for case-insensitive search
        text = text.lower()
        pattern = pattern.lower()
        
        bad_char = BoyerMooreAlgorithm.bad_character_table(pattern)
        good_suffix = BoyerMooreAlgorithm.good_suffix_table(pattern)
        
        occurrences = []
        i = 0
        
        while i <= n - m:
            j = m - 1
            
            while j >= 0 and pattern[j] == text[i + j]:
                j -= 1
            
            if j < 0:
                occurrences.append(i)
                i += good_suffix[0]
            else:
                bad_char_shift = j - bad_char.get(text[i + j], -1)
                good_suffix_shift = good_suffix[j]
                i += max(bad_char_shift, good_suffix_shift)
        
        return occurrences

class AhoCorasickAlgorithm:
    """Aho-Corasick algorithm for multiple pattern matching (Bonus)"""
    
    class TrieNode:
        def __init__(self):
            self.children = {}
            self.failure = None
            self.output = []
    
    def __init__(self, patterns: List[str]):
        self.root = self.TrieNode()
        self.root.failure = self.root  # Root's failure points to itself
        self.patterns = list(dict.fromkeys(p.lower() for p in patterns if p))
        self.build_trie()
        self.build_failure_function()
    
    def build_trie(self):
        """Build trie from patterns"""
        for pattern in self.patterns:
            node = self.root
            for char in pattern:
                if char not in node.children:
                    node.children[char] = self.TrieNode()
                node = node.children[char]
            node.output.append(self.patterns.index(pattern))
    
    def build_failure_function(self):
        """Build failure function for Aho-Corasick"""
        queue = deque()
        
        # Initialize failure function for depth 1 nodes
        for child in self.root.children.values():
            child.failure = self.root
            queue.append(child)
        
        # Build failure function for remaining nodes
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find failure node
                failure_node = current.failure
                # Traverse failures until we find one with matching char or reach root
                while failure_node != self.root and char not in failure_node.children:
                    failure_node = failure_node.failure
                
                # Set failure link for child
                if char in failure_node.children:
                    child.failure = failure_node.children[char]
                else:
                    child.failure = self.root
                
                # Merge outputs from failure node
                child.output.extend(child.failure.output)
    
    def search(self, text: str) -> Dict[str, List[int]]:
        """Find all occurrences of patterns in text"""
        text = text.lower()
        from collections import defaultdict
        results = defaultdict(list)
        
        node = self.root
        
        for i, char in enumerate(text):
            # Traverse failure links until we find valid transition or reach root
            while node != self.root and char not in node.children:
                node = node.failure
            
            # Move to child node if valid transition exists
            if char in node.children:
                node = node.children[char]
            
            # Record matches for all output patterns at current node
            for pattern_idx in node.output:
                pattern = self.patterns[pattern_idx]
                start_pos = i - len(pattern) + 1
                results[pattern].append(start_pos)
        
        return dict(results)

class LevenshteinDistance:
    """Levenshtein Distance algorithm for fuzzy matching"""
    
    @staticmethod
    def calculate(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return LevenshteinDistance.calculate(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def similarity_ratio(s1: str, s2: str) -> float:
        """Calculate similarity ratio (0-1) between two strings"""
        distance = LevenshteinDistance.calculate(s1.lower(), s2.lower())
        max_len = max(len(s1), len(s2))
        
        if max_len == 0:
            return 1.0
        
        return 1.0 - (distance / max_len)
