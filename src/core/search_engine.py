"""
Main search engine for CV matching with multiprocessing support.
Refactored to be cleaner and more maintainable.
"""

from database.models.applicant import ApplicantDetail
from utils.type_safety import (
    safe_get_str,
    safe_get_dict,
    safe_get_int
)
from core.search_utils import (
    get_searchable_text,
    combine_and_rank_results,
    validate_search_params,
    calculate_optimal_chunk_size,
    should_use_multiprocessing
)
from core.search_workers import (
    _process_chunk_exact,
    _process_chunk_fuzzy_dynamic,
    _process_applicant_chunk
)
from core.cv_processor import CVProcessor
from algorithms.fuzzy_matcher import FuzzyMatcher
from algorithms.aho_corasick import AhoCorasickMatcher
from algorithms.boyer_moore import BoyerMooreMatcher
from algorithms.kmp import KMPMatcher
from database.models.database import SessionLocal
import time
import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Optional, Any

# Fix Windows multiprocessing issues
if __name__ != '__main__':
    # Set multiprocessing start method to 'spawn' on Windows to avoid permission issues
    if sys.platform.startswith('win') and multiprocessing.get_start_method(allow_none=True) != 'spawn':
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            # Already set, ignore
            pass


def _test_multiprocessing_worker():
    """Simple test function for multiprocessing - must be at module level"""
    return True


def calculate_dynamic_threshold(search_term: str) -> float:
    """
    Calculate dynamic fuzzy threshold based on search term length.
    Longer terms allow for more typos, shorter terms require stricter matching.
    Uses stricter thresholds (0.7-1.0 range) for better precision.

    Args:
        search_term: The search keyword

    Returns:
        float: Dynamic threshold between 0.7 and 1.0
    """
    term_length = len(search_term.strip())

    if term_length <= 3:
        # Very short terms: exact match
        return 1.0
    elif term_length <= 5:
        # Short terms: very strict (0.95)
        return 0.95
    elif term_length <= 8:
        # Medium terms: strict (0.85)
        return 0.85
    elif term_length <= 12:
        # Long terms: moderately strict (0.8)
        return 0.8
    else:
        # Very long terms: still strict but most tolerant (0.7)
        return 0.7


class SearchEngine:
    """Main search engine for CV matching with type safety and multiprocessing support"""

    def __init__(self):
        # Initialize algorithm matchers
        self.kmp_matcher: KMPMatcher = KMPMatcher()
        self.boyer_moore_matcher: BoyerMooreMatcher = BoyerMooreMatcher()
        self.aho_corasick_matcher: AhoCorasickMatcher = AhoCorasickMatcher()
        self.fuzzy_matcher: FuzzyMatcher = FuzzyMatcher()
        # Initialize CV processor for computing fields on demand
        self.cv_processor: CVProcessor = CVProcessor()

    def search(self, keywords: List[str], algorithm: str = "KMP",
               max_results: int = 10, fuzzy_threshold: float = None,
               progress_callback: Optional[callable] = None,
               use_multiprocessing: bool = False) -> Dict[str, Any]:
        """Perform CV search with specified algorithm using type safety and real progress tracking"""

        start_time = time.time()

        def update_progress(progress: float, message: str):
            """Helper function to update progress if callback is provided"""
            if progress_callback:
                progress_callback(progress, message)
                print(f"SearchEngine: {message} ({progress:.0f}%)")

        try:
            # Validate and sanitize inputs (without fuzzy_threshold for now)
            keywords, algorithm, max_results, _ = validate_search_params(
                keywords, algorithm, max_results, 0.7)  # Temporary value for validation

            # Calculate dynamic thresholds for each keyword
            dynamic_thresholds = {}
            for keyword in keywords:
                dynamic_thresholds[keyword] = calculate_dynamic_threshold(
                    keyword)

            print(f"🎯 Dynamic thresholds calculated:")
            for keyword, threshold in dynamic_thresholds.items():
                print(
                    f"   '{keyword}' (len={len(keyword)}) -> threshold={threshold:.2f}")

            if not keywords:
                update_progress(100, "No valid keywords provided")
                return self._empty_result(algorithm, keywords, start_time)

            update_progress(5, "Initializing search engine...")
            # Load applicant data from database (with multiprocessing if enabled)
            update_progress(10, "Connecting to database...")
            applicant_dicts = self._load_applicant_data(
                update_progress, use_multiprocessing)

            if not applicant_dicts:
                update_progress(100, "No applicants found in database")
                return self._empty_result(algorithm, keywords, start_time)

            # Choose search strategy based on multiprocessing preference and data size
            use_mp = should_use_multiprocessing(
                len(applicant_dicts), use_multiprocessing)

            if use_mp:
                update_progress(
                    60, f"Starting optimized multiprocessing {algorithm} search on {len(applicant_dicts)} applicants...")
                return self._multiprocessing_search(
                    applicant_dicts, keywords, algorithm, max_results,
                    dynamic_thresholds, progress_callback, start_time)
            else:
                update_progress(
                    60, f"Starting {algorithm} single-threaded search on {len(applicant_dicts)} applicants...")
                return self._single_threaded_search(
                    applicant_dicts, keywords, algorithm, max_results,
                    dynamic_thresholds, progress_callback, start_time)

        except Exception as e:
            print(f"Error in search: {e}")
            return self._error_result(algorithm, keywords, start_time, str(e))

    def _load_applicant_data(self, update_progress, use_multiprocessing=False) -> List[Dict]:
        """Load and process applicant data from database"""
        db = SessionLocal()
        try:
            from sqlalchemy.orm import joinedload
            update_progress(15, "Loading applicant data...")

            applicant_details = db.query(ApplicantDetail).options(
                joinedload(ApplicantDetail.profile)).all()

            update_progress(
                # Use multiprocessing for data processing if enabled and we have enough data
                25, f"Processing {len(applicant_details)} applicant profiles...")
            if use_multiprocessing and len(applicant_details) > 10:
                update_progress(
                    27, "Using multiprocessing for applicant data processing...")
                applicant_dicts = self._parallel_process_applicants(
                    applicant_details, update_progress)
            else:
                # Sequential processing
                applicant_dicts = []
                for i, detail in enumerate(applicant_details):
                    # Update progress for every 10% of applicants processed
                    if len(applicant_details) > 0:
                        progress = 25 + \
                            (i / len(applicant_details)) * 30  # 25% to 55%
                        if i % max(1, len(applicant_details) // 10) == 0:
                            update_progress(
                                progress, f"Processing applicant {i+1}/{len(applicant_details)}...")

                    detail_dict = self._process_single_applicant(detail)
                    applicant_dicts.append(detail_dict)

            update_progress(
                55, f"Completed processing {len(applicant_dicts)} applicants")
            return applicant_dicts

        finally:
            db.close()

    def _parallel_process_applicants(self, applicant_details: List,
                                     progress_callback: Optional[callable]) -> List[Dict]:
        """Process applicant details in parallel for better performance"""
        import multiprocessing

        def update_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress, message)
                print(
                    f"SearchEngine Parallel Processing: {message} ({progress:.0f}%)")

        update_progress(
            27, f"Starting parallel processing of {len(applicant_details)} applicants...")

        # Convert SQLAlchemy objects to dictionaries first (can't pickle SQLAlchemy objects)
        applicant_data = []
        for detail in applicant_details:
            detail_dict = detail.to_dict()
            if detail.profile:
                profile_dict = detail.profile.to_dict()
                detail_dict['profile'] = profile_dict
            applicant_data.append(detail_dict)
          # Process in parallel chunks
        num_workers = min(multiprocessing.cpu_count(),
                          4, len(applicant_data) // 10)
        if num_workers < 1:
            num_workers = 1
        chunk_size = max(5, len(applicant_data) // num_workers)

        chunks = []
        for i in range(0, len(applicant_data), chunk_size):
            chunks.append(applicant_data[i:i + chunk_size])

        results = []
        completed = 0

        try:
            # Check if multiprocessing is available before trying to use it
            if not self._can_use_multiprocessing():
                print(
                    "⚠️  Multiprocessing not available for applicant processing, using single-threaded...")
                results = []
                for i, detail_dict in enumerate(applicant_data):
                    processed = self._process_single_applicant_dict(
                        detail_dict)
                    results.append(processed)

                    if i % max(1, len(applicant_data) // 10) == 0:
                        progress = 30 + (i / len(applicant_data)
                                         ) * 25  # 30% to 55%
                        update_progress(
                            progress, f"Processing applicant {i+1}/{len(applicant_data)}...")
                update_progress(
                    55, f"Completed processing {len(results)} applicants")
                return results

            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                future_to_chunk = {
                    executor.submit(_process_applicant_chunk, chunk): i
                    for i, chunk in enumerate(chunks)
                }

                for future in as_completed(future_to_chunk):
                    chunk_idx = future_to_chunk[future]
                    try:
                        chunk_results = future.result()
                        results.extend(chunk_results)

                        completed += 1
                        progress = 27 + (completed / len(chunks)
                                         ) * 28  # 27% to 55%
                        update_progress(
                            progress, f"Processed chunk {completed}/{len(chunks)}")

                    except Exception as e:
                        print(
                            f"Error processing applicant chunk {chunk_idx}: {e}")

        except (PermissionError, OSError, RuntimeError) as e:
            print(f"⚠️  Multiprocessing permission error: {e}")
            print("   This is likely due to Windows security restrictions.")
            print("   Falling back to single-threaded processing...")
            # Fallback to single-threaded
            update_progress(
                30, "Multiprocessing blocked by system, using single-threaded...")
            results = []
            for i, detail_dict in enumerate(applicant_data):
                processed = self._process_single_applicant_dict(detail_dict)
                results.append(processed)

                if i % max(1, len(applicant_data) // 10) == 0:
                    progress = 30 + (i / len(applicant_data)
                                     ) * 25  # 30% to 55%
                    update_progress(
                        progress, f"Processing applicant {i+1}/{len(applicant_data)}...")

        except Exception as e:
            print(f"Error in parallel applicant processing: {e}")
            # Fallback to single-threaded
            update_progress(
                30, "Parallel processing failed, falling back to single-threaded...")
            results = []
            for i, detail_dict in enumerate(applicant_data):
                processed = self._process_single_applicant_dict(detail_dict)
                results.append(processed)

                if i % max(1, len(applicant_data) // 10) == 0:
                    progress = 30 + (i / len(applicant_data)
                                     ) * 25  # 30% to 55%
                    update_progress(
                        progress, f"Processing applicant {i+1}/{len(applicant_data)}...")

        update_progress(55, f"Completed processing {len(results)} applicants")
        return results

    def _process_single_applicant_dict(self, detail_dict: Dict) -> Dict:
        """Process a single applicant detail dictionary"""
        profile = safe_get_dict(detail_dict, 'profile', {})

        if profile:
            # Add computed name field for display
            first_name = safe_get_str(profile, 'first_name', '')
            last_name = safe_get_str(profile, 'last_name', '')
            detail_dict['name'] = f"{first_name} {last_name}".strip(
            ) or "Unknown"            # Flatten profile fields for easier access in detail view
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
            computed_fields = self.cv_processor.compute_cv_fields(cv_path)
            detail_dict.update(computed_fields)

            # Flatten personal_info structure for UI compatibility
            personal_info = computed_fields.get('personal_info', {})
            if personal_info:
                # Override with extracted personal info if available
                if personal_info.get('email'):
                    detail_dict['email'] = personal_info['email']
                if personal_info.get('phone'):
                    detail_dict['phone'] = personal_info['phone']
                if personal_info.get('linkedin'):
                    detail_dict['linkedin'] = personal_info['linkedin']
                if personal_info.get('name') and personal_info['name'] != 'Not specified':
                    detail_dict['name'] = personal_info['name']

        return detail_dict

    def _process_single_applicant(self, detail) -> Dict:
        """Process a single applicant detail from SQLAlchemy object"""
        detail_dict = detail.to_dict()
        if detail.profile:
            profile_dict = detail.profile.to_dict()
            detail_dict['profile'] = profile_dict

            # Add computed name field for display
            first_name = safe_get_str(profile_dict, 'first_name', '')
            last_name = safe_get_str(profile_dict, 'last_name', '')
            detail_dict['name'] = f"{first_name} {last_name}".strip(
            ) or "Unknown"            # Flatten profile fields for easier access in detail view
            detail_dict['phone'] = safe_get_str(
                profile_dict, 'phone_number', '')
            detail_dict['address'] = safe_get_str(profile_dict, 'address', '')
            detail_dict['date_of_birth'] = safe_get_str(
                profile_dict, 'date_of_birth', '')
        else:
            detail_dict['name'] = "Unknown"
            detail_dict['phone'] = ''
            detail_dict['address'] = ''
            detail_dict['date_of_birth'] = ''

        # Compute CV fields on demand for search
        cv_path = safe_get_str(detail_dict, 'cv_path', '')
        if cv_path:
            computed_fields = self.cv_processor.compute_cv_fields(cv_path)
            # Flatten personal_info structure for UI compatibility
            detail_dict.update(computed_fields)
            personal_info = computed_fields.get('personal_info', {})
            if personal_info:
                # Override with extracted personal info if available
                if personal_info.get('email'):
                    detail_dict['email'] = personal_info['email']
                if personal_info.get('phone'):
                    detail_dict['phone'] = personal_info['phone']
                if personal_info.get('linkedin'):
                    detail_dict['linkedin'] = personal_info['linkedin']
                if personal_info.get('name') and personal_info['name'] != 'Not specified':
                    detail_dict['name'] = personal_info['name']

        return detail_dict

    def _multiprocessing_search(self, applicant_dicts: List[Dict], keywords: List[str],
                                algorithm: str, max_results: int, dynamic_thresholds: Dict[str, float],
                                progress_callback: Optional[callable], start_time: float) -> Dict[str, Any]:
        """Perform search using optimized multiprocessing"""

        def update_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress, message)
                print(f"SearchEngine MP: {message} ({progress:.0f}%)")

        # Calculate optimal processing parameters
        num_workers = min(multiprocessing.cpu_count(),
                          8, len(applicant_dicts) // 5)
        chunk_size = calculate_optimal_chunk_size(
            len(applicant_dicts), num_workers)

        update_progress(
            65, f"Starting multiprocessing with {num_workers} workers, chunk size {chunk_size}...")

        # Split applicants into chunks
        chunks = []
        for i in range(0, len(applicant_dicts), chunk_size):
            chunks.append(applicant_dicts[i:i + chunk_size])

        # Use separate exact and fuzzy matching for proper timing
        print(f"Created {len(chunks)} chunks for processing")
        exact_start = time.time()
        exact_results = {}

        try:
            # Check if multiprocessing is actually available
            if not self._can_use_multiprocessing():
                print(
                    "⚠️  Multiprocessing not available, falling back to single-threaded...")
                return self._single_threaded_search(
                    applicant_dicts, keywords, algorithm, max_results,
                    dynamic_thresholds, progress_callback, start_time)

            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                # First do exact matching
                future_to_chunk = {
                    executor.submit(_process_chunk_exact, chunk, keywords, algorithm): i
                    for i, chunk in enumerate(chunks)
                }

                completed_chunks = 0
                for future in as_completed(future_to_chunk):
                    chunk_idx = future_to_chunk[future]
                    try:
                        chunk_results = future.result()
                        exact_results.update(chunk_results)

                        completed_chunks += 1
                        progress = 65 + (completed_chunks /
                                         len(chunks)) * 15  # 65% to 80%
                        update_progress(
                            progress, f"Exact matching chunk {completed_chunks}/{len(chunks)} - found {len(exact_results)} matches")

                        # Early stopping if we have enough results
                        if len(exact_results) >= max_results * 3:  # Get extra for better ranking
                            print(
                                f"Early stopping in exact matching: Found {len(exact_results)} matches")
                            for remaining_future in future_to_chunk:
                                if not remaining_future.done():
                                    remaining_future.cancel()
                            break

                    except Exception as e:
                        print(f"Error processing exact chunk {chunk_idx}: {e}")

        except Exception as e:
            print(f"Error in exact multiprocessing: {e}")
            # Fallback to single-threaded processing
            update_progress(
                70, "Exact multiprocessing failed, falling back to single-threaded...")
            return self._single_threaded_search(
                applicant_dicts, keywords, algorithm, max_results,
                dynamic_thresholds, progress_callback, start_time)

        exact_time = time.time() - exact_start
        update_progress(
            80, f"Exact matching completed. Found {len(exact_results)} matches.")

        # Now do fuzzy matching in parallel
        update_progress(82, "Starting fuzzy matching...")
        fuzzy_start = time.time()
        fuzzy_results = {}        # Find keywords that had no exact matches for fuzzy matching
        keywords_with_exact_matches = set()
        for result in exact_results.values():
            keywords_with_exact_matches.update(
                result.get('exact_matches', {}).keys())

        keywords_for_fuzzy = [
            kw for kw in keywords if kw not in keywords_with_exact_matches]

        if keywords_for_fuzzy:
            # Use dynamic thresholds for fuzzy matching
            try:
                with ProcessPoolExecutor(max_workers=num_workers) as executor:
                    future_to_chunk = {
                        executor.submit(_process_chunk_fuzzy_dynamic, chunk, keywords_for_fuzzy, dynamic_thresholds): i
                        for i, chunk in enumerate(chunks)
                    }

                    completed_chunks = 0
                    for future in as_completed(future_to_chunk):
                        chunk_idx = future_to_chunk[future]
                        try:
                            chunk_results = future.result()
                            fuzzy_results.update(chunk_results)

                            completed_chunks += 1
                            progress = 82 + \
                                (completed_chunks / len(chunks)) * 8  # 82% to 90%
                            update_progress(
                                progress, f"Fuzzy matching chunk {completed_chunks}/{len(chunks)} - found {len(fuzzy_results)} additional matches")

                        except Exception as e:
                            print(
                                f"Error processing fuzzy chunk {chunk_idx}: {e}")

            except Exception as e:
                print(f"Error in fuzzy multiprocessing: {e}")
                update_progress(
                    85, "Fuzzy multiprocessing failed, skipping fuzzy matching...")

        fuzzy_time = time.time() - fuzzy_start
        # Combine and rank results
        update_progress(
            90, f"Fuzzy matching completed. Found {len(fuzzy_results)} additional matches.")
        update_progress(95, "Combining and ranking results...")
        combined_results = combine_and_rank_results(
            exact_results, fuzzy_results)

        # Limit results
        final_results = combined_results[:max_results]
        update_progress(
            100, f"Search completed! Found {len(final_results)} total matches.")

        total_time = time.time() - start_time

        return {
            'results': final_results,
            'exact_match_time': exact_time,
            'fuzzy_match_time': fuzzy_time,  # Now properly tracked
            'total_time': total_time,
            'algorithm_used': algorithm,
            'keywords_searched': keywords,
            'multiprocessing_used': True,
            'num_workers': num_workers,
            'chunks_processed': len(chunks)}

    def _single_threaded_search(self, applicant_dicts: List[Dict], keywords: List[str],
                                algorithm: str, max_results: int, dynamic_thresholds: Dict[str, float],
                                progress_callback: Optional[callable], start_time: float) -> Dict[str, Any]:
        """Perform single-threaded search"""

        def update_progress(progress: float, message: str):
            if progress_callback:
                progress_callback(progress, message)
                print(f"SearchEngine ST: {message} ({progress:.0f}%)")

        # Perform exact matching
        exact_start = time.time()
        exact_results = self._perform_exact_matching(
            applicant_dicts, keywords, algorithm, update_progress)
        exact_time = time.time() - exact_start
        update_progress(
            75, f"Exact matching completed. Found {len(exact_results)} matches.")

        # Perform fuzzy matching        update_progress(80, "Starting fuzzy matching...")
        fuzzy_start = time.time()
        fuzzy_results = self._perform_fuzzy_matching(
            applicant_dicts, keywords, dynamic_thresholds, exact_results, update_progress)
        fuzzy_time = time.time() - fuzzy_start
        update_progress(
            90, f"Fuzzy matching completed. Found {len(fuzzy_results)} additional matches.")

        # Combine and rank results
        update_progress(95, "Combining and ranking results...")
        combined_results = combine_and_rank_results(
            exact_results, fuzzy_results)

        # Limit results
        final_results = combined_results[:max_results]
        update_progress(
            100, f"Search completed! Found {len(final_results)} total matches.")

        total_time = time.time() - start_time

        return {
            'results': final_results,
            'exact_match_time': exact_time,
            'fuzzy_match_time': fuzzy_time,
            'total_time': total_time,
            'algorithm_used': algorithm,
            'keywords_searched': keywords,
            'multiprocessing_used': False
        }

    def _perform_exact_matching(self, applicant_dicts: List[Dict], keywords: List[str],
                                algorithm: str, update_progress) -> Dict[int, Dict]:
        """Perform exact matching using specified algorithm"""
        results = {}

        if algorithm == "AC":  # Aho-Corasick
            return self._aho_corasick_search(applicant_dicts, keywords)

        # For KMP and BM, search each keyword individually
        for i, applicant in enumerate(applicant_dicts):
            if i % max(1, len(applicant_dicts) // 10) == 0:
                progress = 60 + (i / len(applicant_dicts)) * 15  # 60% to 75%
                update_progress(
                    progress, f"Exact matching {i+1}/{len(applicant_dicts)}...")

            applicant_id = safe_get_int(applicant, 'detail_id', 0)
            if applicant_id == 0:
                continue

            # Combine all searchable text
            searchable_text = get_searchable_text(applicant).lower()

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
        """Perform multi-pattern search using Aho-Corasick"""
        results = {}

        if not keywords:
            return results

        # Create Aho-Corasick automaton
        ac = self.aho_corasick_matcher(keywords)

        for applicant in applicant_dicts:
            applicant_id = safe_get_int(applicant, 'detail_id', 0)
            if applicant_id == 0:
                continue

            searchable_text = get_searchable_text(applicant)

            # Search all patterns at once
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

        return results

    def _perform_fuzzy_matching(self, applicant_dicts: List[Dict], keywords: List[str],
                                dynamic_thresholds: Dict[str, float], exact_results: Dict[int, Dict],
                                update_progress) -> Dict[int, Dict]:
        """Perform fuzzy matching for keywords without exact matches"""
        fuzzy_results = {}

        # Find keywords that had no exact matches
        keywords_with_exact_matches = set()
        for result in exact_results.values():
            keywords_with_exact_matches.update(
                result.get('exact_matches', {}).keys())

        keywords_for_fuzzy = [
            kw for kw in keywords if kw not in keywords_with_exact_matches]

        if not keywords_for_fuzzy:
            return fuzzy_results

        # Perform fuzzy matching
        for i, applicant in enumerate(applicant_dicts):
            if i % max(1, len(applicant_dicts) // 10) == 0:
                progress = 80 + (i / len(applicant_dicts)) * 10  # 80% to 90%
                update_progress(
                    progress, f"Fuzzy matching {i+1}/{len(applicant_dicts)}...")

            applicant_id = safe_get_int(applicant, 'detail_id', 0)
            if applicant_id == 0 or applicant_id in exact_results:
                continue  # Skip if already has exact match

            searchable_text = get_searchable_text(applicant)
            words = set(searchable_text.lower().split())

            fuzzy_matches = {}
            total_fuzzy_score = 0

            for keyword in keywords_for_fuzzy:
                best_match = None
                best_similarity = 0
                keyword_threshold = dynamic_thresholds.get(
                    keyword, 0.7)  # Default fallback

                for word in words:
                    similarity = self.fuzzy_matcher.similarity_ratio(
                        keyword, word)
                    if similarity >= keyword_threshold and similarity > best_similarity:
                        best_similarity = similarity
                        best_match = word

                if best_match:
                    fuzzy_matches[keyword] = {
                        'matched_word': best_match,
                        'similarity': best_similarity
                    }
                    total_fuzzy_score += best_similarity

            if fuzzy_matches:
                fuzzy_results[applicant_id] = {
                    'applicant': applicant,
                    'exact_matches': {},
                    'total_exact_matches': 0,
                    'fuzzy_matches': fuzzy_matches,
                    'total_fuzzy_matches': len(fuzzy_matches),
                    'overall_score': total_fuzzy_score
                }

        return fuzzy_results

    def _empty_result(self, algorithm: str, keywords: List[str], start_time: float) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'results': [],
            'exact_match_time': 0.0,
            'fuzzy_match_time': 0.0,
            'total_time': time.time() - start_time,
            'algorithm_used': algorithm,
            'keywords_searched': keywords
        }

    def _error_result(self, algorithm: str, keywords: List[str], start_time: float, error: str) -> Dict[str, Any]:
        """Return error result structure"""
        return {
            'results': [],
            'exact_match_time': 0.0,
            'fuzzy_match_time': 0.0,
            'total_time': time.time() - start_time,
            'algorithm_used': algorithm,
            'keywords_searched': keywords,
            'error': error
        }

    def get_applicant_details(self, detail_id: int) -> Optional[Dict]:
        """Get detailed applicant information with computed CV fields by detail_id"""
        db = SessionLocal()
        try:
            from sqlalchemy.orm import joinedload

            # Get the specific applicant detail with profile
            applicant_detail = db.query(ApplicantDetail).options(
                joinedload(ApplicantDetail.profile)
            ).filter(ApplicantDetail.detail_id == detail_id).first()

            if not applicant_detail:
                print(f"No applicant found with detail_id: {detail_id}")
                return None

            # Convert to dictionary and process
            detail_dict = self._process_single_applicant(applicant_detail)

            return detail_dict

        except Exception as e:
            print(
                f"Error getting applicant details for detail_id {detail_id}: {e}")
            return None
        finally:
            db.close()

    def _can_use_multiprocessing(self) -> bool:
        """Check if multiprocessing is available and working"""
        try:
            # Try a simple multiprocessing test using module-level function
            with ProcessPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_test_multiprocessing_worker)
                result = future.result(timeout=5)  # 5 second timeout
                return result is True

        except (PermissionError, OSError, RuntimeError, Exception) as e:
            print(f"⚠️  Multiprocessing test failed: {e}")
            print("   Falling back to single-threaded processing")
            return False
