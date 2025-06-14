from typing import List, Dict


class BoyerMooreMatcher:
    """Boyer-Moore string matching algorithm"""

    def __init__(self):
        pass

    def search(self, text: str, pattern: str) -> List[int]:
        """Search for pattern in text using Boyer-Moore algorithm with last occurrence table"""
        if not pattern or not text:
            return []

        pattern = pattern.lower()
        text = text.lower()

        # Build last occurrence table
        last_occurrence = self._build_last_occurrence_table(pattern)

        matches = []
        shift = 0

        while shift <= len(text) - len(pattern):
            j = len(pattern) - 1

            # Keep reducing j while characters match (right to left)
            while j >= 0 and pattern[j] == text[shift + j]:
                j -= 1

            if j < 0:
                # Pattern found
                matches.append(shift)
                shift += 1  # Move to next position
            else:
                # Calculate shift using last occurrence rule
                mismatched_char = text[shift + j]
                last_pos = last_occurrence.get(mismatched_char, -1)

                # Boyer-Moore bad character shift
                shift += max(1, j - last_pos)

        return matches

    def _build_last_occurrence_table(self, pattern: str) -> Dict[str, int]:
        """Build last occurrence table for Boyer-Moore bad character rule"""
        last_occurrence = {}

        # Record the last occurrence of each character in the pattern
        for i in range(len(pattern)):
            last_occurrence[pattern[i]] = i

        return last_occurrence
