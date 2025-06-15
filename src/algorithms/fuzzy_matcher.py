from typing import List, Tuple


class FuzzyMatcher:
    """Fuzzy string matching using edit distance with enhanced phrase matching"""

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
        """Calculate Levenshtein distance between two strings"""
        m, n = len(s1), len(s2)

        # Optimization: use single dimension array
        if m < n:
            return self._edit_distance(s2, s1)

        # Previous row of distances
        previous = list(range(n + 1))

        for i, ch1 in enumerate(s1):
            current = [i + 1]
            for j, ch2 in enumerate(s2):
                insertions = previous[j + 1] + 1
                deletions = current[j] + 1
                substitutions = previous[j] + (ch1 != ch2)
                current.append(min(insertions, deletions, substitutions))
            previous = current

        return previous[n]

    def substring_similarity(self, query: str, text: str, text_words: List[str] = None) -> Tuple[float, str]:
        """
        Calculate similarity and return matched substring.
        Returns: (similarity_score, matched_substring)
        """
        if not query or not text:
            return 0.0, ""

        query = query.lower().strip()
        text = text.lower().strip()

        # Handle exact matches quickly
        if query == text:
            return 1.0, text

        # Precompute words if not provided
        if text_words is None:
            text_words = text.split()

        query_words = query.split()
        is_single_word = len(query_words) == 1

        if is_single_word:
            # Single word matching
            best_similarity = 0.0
            best_word = ""
            for word in text_words:
                similarity = self.similarity_ratio(query, word)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_word = word

            # Apply leniency for longer words
            if len(query) > 8 and best_similarity > 0.75:
                best_similarity = min(0.85, best_similarity + 0.1)

            return best_similarity, best_word

        else:
            # Phrase matching
            return self._sliding_window_similarity(query, text, query_words, text_words)

    def _sliding_window_similarity(self, query: str, text: str,
                                   query_words: List[str], text_words: List[str]) -> Tuple[float, str]:
        """Find best matching phrase using sliding window approach"""
        best_similarity = 0.0
        best_phrase = ""
        query_len = len(query_words)

        # Search window sizes: from query_len-2 to query_len+2
        window_sizes = sorted(set([
            query_len - 2,
            query_len - 1,
            query_len,
            query_len + 1,
            query_len + 2
        ]))

        # Filter valid window sizes
        window_sizes = [ws for ws in window_sizes if 1 <=
                        ws <= len(text_words)]

        for window_size in window_sizes:
            for start_idx in range(len(text_words) - window_size + 1):
                phrase = " ".join(text_words[start_idx:start_idx+window_size])
                similarity = self._phrase_similarity(query, phrase)

                # Update best match if found better
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_phrase = phrase

                # Early exit for high confidence match
                if similarity > 0.95:
                    return similarity, phrase

        return best_similarity, best_phrase

    def _phrase_similarity(self, phrase1: str, phrase2: str) -> float:
        """Calculate similarity between two phrases"""
        if phrase1 == phrase2:
            return 1.0

        # Basic similarity
        base_similarity = self.similarity_ratio(phrase1, phrase2)

        # Special handling for long phrases
        if len(phrase1) > 50 or len(phrase2) > 50:
            edit_dist = self._edit_distance(phrase1, phrase2)
            if edit_dist <= 1:
                return max(base_similarity, 0.95)
            elif edit_dist <= 2:
                return max(base_similarity, 0.90)
            elif edit_dist <= 3:
                return max(base_similarity, 0.85)

        return base_similarity
