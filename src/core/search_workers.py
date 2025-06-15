"""
Worker functions for multiprocessing in the search engine.
These functions must be at module level to be picklable for multiprocessing.
"""

from typing import List, Dict
from algorithms.kmp import KMPMatcher
from algorithms.boyer_moore import BoyerMooreMatcher
from algorithms.aho_corasick import AhoCorasickMatcher
from algorithms.fuzzy_matcher import FuzzyMatcher
from core.cv_processor import CVProcessor
from utils.type_safety import (
    safe_get_str,
    safe_get_list,
    safe_get_dict,
    safe_get_int,
    is_dict,
)


def _process_chunk_exact(applicant_chunk: List[Dict], keywords: List[str], algorithm: str) -> Dict[int, Dict]:
    """Process a chunk of applicants for exact matching (multiprocessing worker)"""
    results = {}

    try:
        # Initialize matchers in worker process
        if algorithm == "KMP":
            matcher = KMPMatcher()
        elif algorithm == "BM":
            matcher = BoyerMooreMatcher()
        elif algorithm == "AC":
            matcher = AhoCorasickMatcher()
        else:
            matcher = KMPMatcher()  # Default

        cv_processor = CVProcessor()

        # Process Aho-Corasick differently (multi-pattern search)
        if algorithm == "AC":
            ac = matcher(keywords)  # Create automaton

            for applicant in applicant_chunk:
                applicant_id = safe_get_int(applicant, 'detail_id', 0)
                if applicant_id == 0:
                    continue

                searchable_text = _get_searchable_text_worker(
                    applicant, cv_processor)
                pattern_matches = ac.search(searchable_text)

                matches = {}
                total_matches = 0

                for keyword in keywords:
                    if keyword in pattern_matches and pattern_matches[keyword]:
                        matches[keyword] = len(pattern_matches[keyword])
                        total_matches += len(pattern_matches[keyword])

                if matches:
                    results[applicant_id] = {
                        'applicant': applicant,
                        'exact_matches': matches,
                        'total_exact_matches': total_matches,
                        'fuzzy_matches': {},
                        'total_fuzzy_matches': 0,
                        'overall_score': total_matches
                    }
        else:
            # KMP or Boyer-Moore (single pattern search)
            for applicant in applicant_chunk:
                applicant_id = safe_get_int(applicant, 'detail_id', 0)
                if applicant_id == 0:
                    continue

                searchable_text = _get_searchable_text_worker(
                    applicant, cv_processor).lower()

                matches = {}
                total_matches = 0

                for keyword in keywords:
                    occurrences = matcher.search(searchable_text, keyword)
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

        print(
            f"Worker processed {len(applicant_chunk)} applicants, found {len(results)} matches")
        return results

    except Exception as e:
        print(f"Error in worker process: {e}")
        return {}


def _get_searchable_text_worker(applicant: Dict, cv_processor: CVProcessor) -> str:
    """Get searchable text for worker process (simplified version without database dependencies)"""
    text_parts = []

    try:
        # Basic info from ApplicantProfile (through the relationship)
        profile = safe_get_dict(applicant, 'profile', {})
        first_name = safe_get_str(profile, 'first_name', '')
        last_name = safe_get_str(profile, 'last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            text_parts.append(full_name)

        # Add applicant role from the detail
        text_parts.append(safe_get_str(applicant, 'application_role', ''))

        # Use pre-computed CV fields if available, otherwise compute on demand
        cv_path = safe_get_str(applicant, 'cv_path', '')
        if cv_path:
            # Check if fields are already computed
            if 'summary' in applicant or 'skills' in applicant:
                # Use pre-computed fields
                text_parts.append(safe_get_str(applicant, 'summary', ''))

                skills = safe_get_list(applicant, 'skills', [])
                for skill in skills:
                    if isinstance(skill, str):
                        text_parts.append(skill)

                work_experience = safe_get_list(
                    applicant, 'work_experience', [])
                for exp in work_experience:
                    if is_dict(exp):
                        text_parts.append(safe_get_str(exp, 'position', ''))
                        text_parts.append(safe_get_str(exp, 'company', ''))
                        text_parts.append(safe_get_str(exp, 'description', ''))

                education = safe_get_list(applicant, 'education', [])
                for edu in education:
                    if is_dict(edu):
                        text_parts.append(safe_get_str(edu, 'degree', ''))
                        text_parts.append(safe_get_str(edu, 'institution', ''))

                text_parts.append(safe_get_str(
                    applicant, 'extracted_text', ''))
            else:
                # Compute fields on demand
                computed_fields = cv_processor.compute_cv_fields(cv_path)
                text_parts.append(safe_get_str(computed_fields, 'summary', ''))

                skills = safe_get_list(computed_fields, 'skills', [])
                for skill in skills:
                    if isinstance(skill, str):
                        text_parts.append(skill)

                work_experience = safe_get_list(
                    computed_fields, 'work_experience', [])
                for exp in work_experience:
                    if is_dict(exp):
                        text_parts.append(safe_get_str(exp, 'position', ''))
                        text_parts.append(safe_get_str(exp, 'company', ''))
                        text_parts.append(safe_get_str(exp, 'description', ''))

                education = safe_get_list(computed_fields, 'education', [])
                for edu in education:
                    if is_dict(edu):
                        text_parts.append(safe_get_str(edu, 'degree', ''))
                        text_parts.append(safe_get_str(edu, 'institution', ''))

                text_parts.append(safe_get_str(
                    computed_fields, 'extracted_text', ''))

        # Filter out empty strings and join
        filtered_parts = [part.strip()
                          for part in text_parts if part and part.strip()]
        return ' '.join(filtered_parts)

    except Exception as e:
        print(f"Warning: Error getting searchable text in worker: {e}")
        # Return applicant role as fallback
        return safe_get_str(applicant, 'application_role', '')


def _process_chunk_fuzzy(applicant_chunk: List[Dict], keywords: List[str],
                         threshold: float) -> Dict[int, Dict]:
    """Worker function for parallel fuzzy matching"""
    results = {}

    try:
        fuzzy_matcher = FuzzyMatcher()
        cv_processor = CVProcessor()

        for applicant in applicant_chunk:
            applicant_id = safe_get_int(applicant, 'detail_id', 0)
            if applicant_id == 0:
                continue

            searchable_text = _get_searchable_text_worker(
                applicant, cv_processor)
            words = set(searchable_text.lower().split())

            fuzzy_matches = {}
            total_fuzzy_score = 0

            for keyword in keywords:
                best_match = None
                best_similarity = 0

                for word in words:
                    similarity = fuzzy_matcher.similarity_ratio(keyword, word)
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
                results[applicant_id] = {
                    'applicant': applicant,
                    'exact_matches': {},
                    'total_exact_matches': 0,
                    'fuzzy_matches': fuzzy_matches,
                    'total_fuzzy_matches': len(fuzzy_matches),
                    'overall_score': total_fuzzy_score
                }

        print(
            f"Fuzzy worker processed {len(applicant_chunk)} applicants, found {len(results)} matches")
        return results

    except Exception as e:
        print(f"Error in fuzzy worker process: {e}")
        return {}


def _process_applicant_chunk(applicant_chunk: List[Dict]) -> List[Dict]:
    """Worker function for parallel applicant processing"""
    try:
        cv_processor = CVProcessor()
        results = []

        for detail_dict in applicant_chunk:
            processed = _process_single_applicant_dict(
                detail_dict, cv_processor)
            results.append(processed)

        print(
            f"Applicant chunk worker processed {len(applicant_chunk)} applicants")
        return results

    except Exception as e:
        print(f"Error in applicant chunk worker: {e}")
        return []


def _process_single_applicant_dict(detail_dict: Dict, cv_processor: CVProcessor) -> Dict:
    """Process a single applicant detail dictionary"""
    profile = safe_get_dict(detail_dict, 'profile', {})

    if profile:
        # Add computed name field for display
        first_name = safe_get_str(profile, 'first_name', '')
        last_name = safe_get_str(profile, 'last_name', '')
        detail_dict['name'] = f"{first_name} {last_name}".strip() or "Unknown"

        # Flatten profile fields for easier access in detail view
        detail_dict['phone'] = safe_get_str(profile, 'phone_number', '')
        detail_dict['address'] = safe_get_str(profile, 'address', '')
        detail_dict['date_of_birth'] = safe_get_str(
            profile, 'date_of_birth', '')
    else:
        detail_dict['name'] = "Unknown"
        detail_dict['phone'] = ''
        detail_dict['address'] = ''
        detail_dict['date_of_birth'] = ''

    # Compute CV fields on demand for search
    cv_path = safe_get_str(detail_dict, 'cv_path', '')
    if cv_path:
        computed_fields = cv_processor.compute_cv_fields(cv_path)
        detail_dict.update(computed_fields)

    return detail_dict
