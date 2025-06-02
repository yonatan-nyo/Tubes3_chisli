from typing import List, Dict, Set
from collections import defaultdict, deque

class TrieNode:
    def __init__(self):
        self.children = {}
        self.failure = None
        self.output = []

class AhoCorasickMatcher:
    """Aho-Corasick multi-pattern string matching algorithm"""
    
    def __init__(self, patterns: List[str] = None):
        self.root = TrieNode()
        if patterns:
            self.build_automaton(patterns)
    
    def __call__(self, patterns: List[str]):
        """Make the matcher callable for compatibility"""
        return AhoCorasickMatcher(patterns)
    
    def build_automaton(self, patterns: List[str]):
        """Build the Aho-Corasick automaton"""
        # Build trie
        for pattern in patterns:
            self._insert_pattern(pattern.lower())
        
        # Build failure links
        self._build_failure_links()
    
    def _insert_pattern(self, pattern: str):
        """Insert a pattern into the trie"""
        node = self.root
        for char in pattern:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.output.append(pattern)
    
    def _build_failure_links(self):
        """Build failure links for the automaton"""
        queue = deque()
        
        # Initialize failure links for depth 1
        for child in self.root.children.values():
            child.failure = self.root
            queue.append(child)
        
        # Build failure links for deeper levels
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find failure link
                failure = current.failure
                while failure and char not in failure.children:
                    failure = failure.failure
                
                if failure:
                    child.failure = failure.children[char]
                else:
                    child.failure = self.root
                
                # Copy output from failure state
                child.output.extend(child.failure.output)
    
    def search(self, text: str) -> Dict[str, List[int]]:
        """Search for all patterns in text"""
        text = text.lower()
        matches = defaultdict(list)
        
        node = self.root
        for i, char in enumerate(text):
            # Follow failure links until we find a match or reach root
            while node and char not in node.children:
                node = node.failure
            
            if node:
                node = node.children[char]
            else:
                node = self.root
            
            # Record all matches at this position
            for pattern in node.output:
                start_pos = i - len(pattern) + 1
                matches[pattern].append(start_pos)
        
        return dict(matches)
