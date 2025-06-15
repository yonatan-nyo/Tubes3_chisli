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
                # Sort by similarity (descending) and limit results
                matches.append((candidate, similarity))
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:max_results]

    def substring_similarity(self, query: str, text: str) -> float:
        """
        Calculate similarity using sliding window approach for better phrase matching.
        This is more forgiving for cases where the query is a near-match of part of the text.
        """
        if not query or not text:
            return 0.0

        query = query.lower().strip()
        text = text.lower().strip()

        if query == text:
            return 1.0

        # If query is a substring of text, give high similarity
        if query in text:
            return 0.9

        # If text is a substring of query, also give high similarity
        if text in query:
            return 0.85

        # For long phrases, use sliding window approach
        query_words = query.split()
        text_words = text.split()

        if len(query_words) > 1:
            return self._sliding_window_similarity(query, text, query_words, text_words)
        else:
            # For single words, use regular similarity with some leniency
            base_similarity = self.similarity_ratio(query, text)
            # Be more forgiving for longer words
            if len(query) > 8 and base_similarity > 0.75:
                return min(0.85, base_similarity + 0.1)
            return base_similarity

    def _sliding_window_similarity(self, query: str, text: str, query_words: list, text_words: list) -> float:
        """
        Use sliding window approach to find the best matching substring in the text.
        """
        best_similarity = 0.0
        query_len = len(query_words)

        # Try different window sizes around the query length
        for window_size in range(max(1, query_len - 2), min(len(text_words) + 1, query_len + 3)):
            for i in range(len(text_words) - window_size + 1):
                window_text = ' '.join(text_words[i:i + window_size])

                # Calculate similarity between query and this window
                similarity = self._phrase_similarity(query, window_text)
                best_similarity = max(best_similarity, similarity)

                # Early exit if we find a very good match
                if similarity > 0.95:
                    return similarity

        return best_similarity

    def _phrase_similarity(self, phrase1: str, phrase2: str) -> float:
        """
        Calculate similarity between two phrases with special handling for common typos.
        """
        if phrase1 == phrase2:
            return 1.0

        # Basic edit distance similarity
        base_similarity = self.similarity_ratio(phrase1, phrase2)

        # Special handling for long phrases with small differences
        if len(phrase1) > 50 or len(phrase2) > 50:
            edit_dist = self._edit_distance(phrase1, phrase2)
            max_len = max(len(phrase1), len(phrase2))

            # If only 1-3 characters different in a long phrase, boost similarity
            if edit_dist <= 1:
                return max(base_similarity, 0.95)
            elif edit_dist <= 2:
                return max(base_similarity, 0.90)
            elif edit_dist <= 3:
                return max(base_similarity, 0.85)

        # Word-level analysis for better typo handling
        words1 = phrase1.split()
        words2 = phrase2.split()

        if len(words1) == len(words2):
            word_similarities = []
            for w1, w2 in zip(words1, words2):
                if w1 == w2:
                    word_similarities.append(1.0)
                else:
                    # More lenient similarity for individual words
                    word_sim = self.similarity_ratio(w1, w2)
                    # Boost similarity for common typo patterns
                    if len(w1) > 5 and len(w2) > 5:
                        # Check for common typos: extra/missing letters at end
                        if w1[:-1] == w2[:-1] or w1[:-2] == w2[:-2]:
                            word_sim = max(word_sim, 0.9)
                        elif w1.startswith(w2) or w2.startswith(w1):
                            word_sim = max(word_sim, 0.85)
                    word_similarities.append(word_sim)

            # Average word similarities, but be more forgiving
            avg_similarity = sum(word_similarities) / len(word_similarities)
            # If most words match well, boost overall similarity
            if avg_similarity > 0.8:
                return max(base_similarity, avg_similarity)

        return base_similarity
