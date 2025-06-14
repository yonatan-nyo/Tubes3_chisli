import time
from typing import List, Dict, Optional, Any
from database.models.applicant import ApplicantDetail
from database.models.database import SessionLocal
from algorithms.kmp import KMPMatcher
from algorithms.boyer_moore import BoyerMooreMatcher
from algorithms.aho_corasick import AhoCorasickMatcher
from algorithms.fuzzy_matcher import FuzzyMatcher
from utils.type_safety import (
    safe_get_str,
    safe_get_list,
    safe_get_dict,
    safe_get_int,
    is_dict,
    ensure_string,
    ensure_list,
)


class SearchEngine:
    """Main search engine for CV matching with type safety"""

    def __init__(self):
        # Initialize algorithm matchers
        self.kmp_matcher: KMPMatcher = KMPMatcher()
        self.boyer_moore_matcher: BoyerMooreMatcher = BoyerMooreMatcher()
        self.aho_corasick_matcher: AhoCorasickMatcher = AhoCorasickMatcher()
        self.fuzzy_matcher: FuzzyMatcher = FuzzyMatcher()

    def search(self, keywords: List[str], algorithm: str = "KMP",
               max_results: int = 10, fuzzy_threshold: float = 0.7) -> Dict[str, Any]:
        """Perform CV search with specified algorithm using type safety"""

        start_time = time.time()

        try:
            # Validate inputs
            keywords = ensure_list(keywords)
            algorithm = ensure_string(algorithm, "KMP")
            max_results = max(1, int(max_results))
            # Get all applicant details from database (iterate over applications as requested)
            fuzzy_threshold = max(0.0, min(1.0, float(fuzzy_threshold)))
            db = SessionLocal()
            try:
                from sqlalchemy.orm import joinedload
                applicant_details = db.query(ApplicantDetail).options(
                    joinedload(ApplicantDetail.profile)).all()

                applicant_dicts = []
                for detail in applicant_details:
                    detail_dict = detail.to_dict()
                    if detail.profile:
                        profile_dict = detail.profile.to_dict()
                        detail_dict['profile'] = profile_dict
                        # Add computed name field for display
                        first_name = safe_get_str(
                            profile_dict, 'first_name', '')
                        last_name = safe_get_str(profile_dict, 'last_name', '')
                        detail_dict['name'] = f"{first_name} {last_name}".strip(
                        ) or "Unknown"
                    else:
                        detail_dict['name'] = "Unknown"
                    applicant_dicts.append(detail_dict)
            finally:
                db.close()

            if not applicant_dicts:
                return {
                    'results': [],
                    'exact_match_time': 0.0,
                    'fuzzy_match_time': 0.0,
                    'total_time': 0.0,
                    'algorithm_used': algorithm,
                    'keywords_searched': keywords
                }

            # Perform exact matching
            exact_start = time.time()
            exact_results = self._perform_exact_matching(
                applicant_dicts, keywords, algorithm)
            exact_time = time.time() - exact_start

            # Perform fuzzy matching - pass exact_results as parameter
            fuzzy_start = time.time()
            fuzzy_results = self._perform_fuzzy_matching(
                applicant_dicts, keywords, fuzzy_threshold, exact_results)
            fuzzy_time = time.time() - fuzzy_start

            # Combine and rank results
            combined_results = self._combine_and_rank_results(
                exact_results, fuzzy_results)

            # Limit results
            final_results = combined_results[:max_results]

            total_time = time.time() - start_time

            return {
                'results': final_results,
                'exact_match_time': exact_time,
                'fuzzy_match_time': fuzzy_time,
                'total_time': total_time,
                'algorithm_used': algorithm,
                'keywords_searched': keywords
            }

        except Exception as e:
            print(f"Error in search: {e}")
            total_time = time.time() - start_time
            return {
                'results': [],
                'exact_match_time': 0.0,
                'fuzzy_match_time': 0.0,
                'total_time': total_time,
                'algorithm_used': algorithm,
                'keywords_searched': keywords,
                'error': str(e)
            }

    def _perform_exact_matching(self, applicant_dicts: List[Dict],
                                keywords: List[str], algorithm: str) -> Dict[int, Dict]:
        """Perform exact matching using specified algorithm with type safety"""
        results = {}

        if algorithm == "AC":  # Aho-Corasick
            return self._aho_corasick_search(applicant_dicts, keywords)

        # For KMP and BM, search each keyword individually
        for applicant in applicant_dicts:
            # Use detail_id as the unique identifier for applications
            applicant_id = safe_get_int(applicant, 'detail_id', 0)
            if applicant_id == 0:
                print(
                    f"Warning: Applicant missing detail_id, skipping: {applicant}")
                continue

            # Combine all searchable text
            searchable_text = self._get_searchable_text(applicant).lower()

            matches = {}
            total_matches = 0

            for keyword in keywords:
                if algorithm == "KMP":
                    occurrences = self.kmp_matcher.search(
                        searchable_text, keyword)
                elif algorithm == "BM":
                    occurrences = self.boyer_moore_matcher.search(
                        searchable_text, keyword)
                else:
                    # Default to KMP
                    occurrences = self.kmp_matcher.search(
                        searchable_text, keyword)

                if occurrences:
                    matches[keyword] = len(occurrences)
                    total_matches += len(occurrences)

            if matches:
                results[applicant_id] = {
                    'applicant': applicant,
                    'exact_matches': matches,
                    'total_exact_matches': total_matches,
                    'fuzzy_matches': {},
                    'total_fuzzy_matches': 0,
                    'overall_score': total_matches
                }

        return results

    def _aho_corasick_search(self, applicant_dicts: List[Dict], keywords: List[str]) -> Dict[int, Dict]:
        """Perform multi-pattern search using Aho-Corasick with type safety"""
        results = {}

        if not keywords:
            return results

        # Create Aho-Corasick automaton
        ac = self.aho_corasick_matcher(keywords)

        for applicant in applicant_dicts:
            # Use detail_id as the unique identifier for applications
            applicant_id = safe_get_int(applicant, 'detail_id', 0)
            if applicant_id == 0:
                print(
                    f"Warning: Applicant missing detail_id, skipping: {applicant}")
                continue

            searchable_text = self._get_searchable_text(applicant)

            # Search all patterns at once
            pattern_matches = ac.search(searchable_text)

            matches = {}
            total_matches = 0

            for keyword in keywords:
                if keyword in pattern_matches and pattern_matches[keyword]:
                    matches[keyword] = len(pattern_matches[keyword])
                    total_matches += len(pattern_matches[keyword])

            if matches:
                results[applicant_id] = {'applicant': applicant,
                                         'exact_matches': matches,
                                         'total_exact_matches': total_matches,
                                         'fuzzy_matches': {},
                                         'total_fuzzy_matches': 0,
                                         'overall_score': total_matches
                                         }

        return results

    def _perform_fuzzy_matching(self, applicant_dicts: List[Dict], keywords: List[str],
                                threshold: float, exact_results: Dict[int, Dict]) -> Dict[int, Dict]:
        """Perform fuzzy matching for keywords without exact matches with type safety"""
        fuzzy_results = {}

        # Find keywords that had no exact matches
        keywords_with_exact_matches = set()
        for result in exact_results.values():
            exact_matches = safe_get_dict(result, 'exact_matches', {})
            keywords_with_exact_matches.update(exact_matches.keys())

        keywords_for_fuzzy = [
            kw for kw in keywords if kw not in keywords_with_exact_matches]

        if not keywords_for_fuzzy:
            return fuzzy_results

        for applicant in applicant_dicts:
            # Use detail_id as the unique identifier for applications
            applicant_id = safe_get_int(applicant, 'detail_id', 0)
            if applicant_id == 0:
                print(
                    f"Warning: Applicant missing detail_id, skipping: {applicant}")
                continue

            searchable_text = self._get_searchable_text(applicant)

            # Extract words from searchable text
            words = set(searchable_text.lower().split())

            fuzzy_matches = {}
            total_fuzzy_score = 0

            for keyword in keywords_for_fuzzy:
                best_match = None
                best_similarity = 0

                for word in words:
                    similarity = self.fuzzy_matcher.similarity_ratio(
                        keyword, word)
                    if similarity >= threshold and similarity > best_similarity:
                        best_similarity = similarity
                        best_match = word

                if best_match:
                    fuzzy_matches[keyword] = {
                        'matched_word': best_match,
                        'similarity': best_similarity
                    }
                    total_fuzzy_score += best_similarity

            if fuzzy_matches:
                if applicant_id in exact_results:
                    # Add fuzzy matches to existing exact results
                    exact_results[applicant_id]['fuzzy_matches'] = fuzzy_matches
                    exact_results[applicant_id]['total_fuzzy_matches'] = len(
                        fuzzy_matches)
                    exact_results[applicant_id]['overall_score'] += total_fuzzy_score
                else:
                    # Create new result entry for fuzzy-only matches
                    fuzzy_results[applicant_id] = {
                        'applicant': applicant,
                        'exact_matches': {},
                        'total_exact_matches': 0,
                        'fuzzy_matches': fuzzy_matches,
                        'total_fuzzy_matches': len(fuzzy_matches),
                        'overall_score': total_fuzzy_score
                    }

        return fuzzy_results

    def _get_searchable_text(self, applicant: Dict) -> str:
        """Combine all searchable text from applicant data with type safety"""
        text_parts = []

        try:
            # Basic info from ApplicantProfile (through the relationship)
            profile = safe_get_dict(applicant, 'profile', {})
            first_name = safe_get_str(profile, 'first_name', '')
            last_name = safe_get_str(profile, 'last_name', '')
            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                text_parts.append(full_name)

            text_parts.append(safe_get_str(applicant, 'applicant_role', ''))
            text_parts.append(safe_get_str(applicant, 'summary', ''))

            # Skills
            skills = safe_get_list(applicant, 'skills', [])
            for skill in skills:
                if isinstance(skill, str):
                    text_parts.append(skill)
                elif isinstance(skill, dict):
                    text_parts.append(safe_get_str(skill, 'name', ''))

            # Work experience
            work_experience = safe_get_list(applicant, 'work_experience', [])
            for exp in work_experience:
                if is_dict(exp):
                    text_parts.append(safe_get_str(exp, 'position', ''))
                    text_parts.append(safe_get_str(exp, 'company', ''))
                    text_parts.append(safe_get_str(exp, 'description', ''))

            # Education
            education = safe_get_list(applicant, 'education', [])
            for edu in education:
                if is_dict(edu):
                    text_parts.append(safe_get_str(edu, 'degree', ''))
                    text_parts.append(safe_get_str(edu, 'institution', ''))

            # Full extracted text as fallback
            text_parts.append(safe_get_str(applicant, 'extracted_text', ''))

            # Filter out empty strings and join
            filtered_parts = [part.strip()
                              for part in text_parts if part and part.strip()]
            return ' '.join(filtered_parts)

        except Exception as e:
            print(
                f"Warning: Error getting searchable text from applicant data: {e}")
            # Return extracted text as fallback
            return safe_get_str(applicant, 'extracted_text', '')

    def _combine_and_rank_results(self, exact_results: Dict,
                                  fuzzy_results: Dict) -> List[Dict]:
        """Combine and rank all search results"""
        all_results = {}

        # Add exact results
        all_results.update(exact_results)

        # Add fuzzy-only results
        for applicant_id, result in fuzzy_results.items():
            if applicant_id not in all_results:
                all_results[applicant_id] = result

        # Convert to list and sort by overall score (descending)
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x['overall_score'],
            reverse=True
        )

        return sorted_results

    def get_applicant_details(self, detail_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information for specific applicant detail (application) with type safety"""
        try:
            detail_id = int(detail_id)
            db = SessionLocal()
            try:
                applicant_detail = db.query(ApplicantDetail).filter(
                    ApplicantDetail.detail_id == detail_id).first()
                if applicant_detail:
                    return applicant_detail.to_dict()
            finally:
                db.close()
        except Exception as e:
            print(f"Error getting applicant details: {e}")
        return None
