from collections import deque
from typing import Dict, List

class TrieNode:
    def __init__(self):
        self.children = {}
        self.failure = None
        self.output = []

class AhoCorasickMatcher:
    def __init__(self, patterns: List[str] = None):
        self.root = TrieNode()
        if patterns is not None:
            self.build_automaton(patterns)

    def __call__(self, patterns: List[str]):
        return AhoCorasickMatcher(patterns)
    
    def build_automaton(self, patterns: List[str]):
        for pattern in patterns:
            self._insert_pattern(pattern.lower())
        self._build_failure_links()
    
    def _insert_pattern(self, pattern: str):
        node = self.root
        for char in pattern:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.output.append(pattern)
    
    def _build_failure_links(self):
        queue = deque()
        self.root.failure = self.root
        
        for child in self.root.children.values():
            child.failure = self.root
            queue.append(child)
        
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                failure = current.failure
                while failure is not self.root and char not in failure.children:
                    failure = failure.failure
                
                if char in failure.children:
                    child.failure = failure.children[char]
                else:
                    child.failure = self.root
                
                child.output += child.failure.output
    
    def search(self, text: str) -> Dict[str, List[int]]:
        text = text.lower()
        matches = {}
        node = self.root
        
        for i, char in enumerate(text):
            while node is not self.root and char not in node.children:
                node = node.failure
            
            if char in node.children:
                node = node.children[char]
            
            for pattern in node.output:
                start_index = i - len(pattern) + 1
                if pattern not in matches:
                    matches[pattern] = []
                matches[pattern].append(start_index)
        
        return matches