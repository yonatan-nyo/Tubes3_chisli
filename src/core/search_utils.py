"""
Utility functions for the search engine.
"""

from typing import List, Dict, Any
from utils.type_safety import (
    safe_get_str,
    safe_get_list,
    safe_get_dict,
    is_dict,
)


def get_searchable_text(applicant: Dict) -> str:
    """Get all searchable text from an applicant with type safety"""
    text_parts = []

    try:
        # Basic info from ApplicantProfile (through the relationship)
        profile = safe_get_dict(applicant, 'profile', {})
        first_name = safe_get_str(profile, 'first_name', '')
        last_name = safe_get_str(profile, 'last_name', '')
        phone = safe_get_str(profile, 'phone_number', '')
        address = safe_get_str(profile, 'address', '')

        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            text_parts.append(full_name)
        if phone:
            text_parts.append(phone)
        if address:
            text_parts.append(address)

        # Add applicant role from the ApplicationDetail
        application_role = safe_get_str(applicant, 'application_role', '')
        if application_role:
            text_parts.append(application_role)

        # CV content (computed fields)
        summary = safe_get_str(applicant, 'summary', '')
        if summary:
            text_parts.append(summary)

        # Skills
        skills = safe_get_list(applicant, 'skills', [])
        for skill in skills:
            if isinstance(skill, str):
                text_parts.append(skill)

        # Work Experience
        work_experience = safe_get_list(applicant, 'work_experience', [])
        for exp in work_experience:
            if is_dict(exp):
                position = safe_get_str(exp, 'position', '')
                company = safe_get_str(exp, 'company', '')
                description = safe_get_str(exp, 'description', '')
                if position:
                    text_parts.append(position)
                if company:
                    text_parts.append(company)
                if description:
                    text_parts.append(description)

        # Education
        education = safe_get_list(applicant, 'education', [])
        for edu in education:
            if is_dict(edu):
                degree = safe_get_str(edu, 'degree', '')
                institution = safe_get_str(edu, 'institution', '')
                if degree:
                    text_parts.append(degree)
                if institution:
                    text_parts.append(institution)

        # Raw extracted text from CV
        extracted_text = safe_get_str(applicant, 'extracted_text', '')
        if extracted_text:
            text_parts.append(extracted_text)

        # Filter out empty strings and join
        filtered_parts = [part.strip()
                          for part in text_parts if part and part.strip()]
        return ' '.join(filtered_parts)

    except Exception as e:
        print(f"Warning: Error getting searchable text: {e}")
        # Return basic applicant info as fallback
        profile = safe_get_dict(applicant, 'profile', {})
        first_name = safe_get_str(profile, 'first_name', '')
        last_name = safe_get_str(profile, 'last_name', '')
        role = safe_get_str(applicant, 'application_role', '')
        return f"{first_name} {last_name} {role}".strip()


def combine_and_rank_results(exact_results: Dict[int, Dict],
                             fuzzy_results: Dict[int, Dict]) -> List[Dict]:
    """Combine and rank search results with type safety"""
    combined = {}

    # Add exact match results
    for applicant_id, result in exact_results.items():
        combined[applicant_id] = result.copy()

    # Add or merge fuzzy results
    for applicant_id, fuzzy_result in fuzzy_results.items():
        if applicant_id in combined:
            # Merge fuzzy matches into existing exact match result
            combined[applicant_id]['fuzzy_matches'].update(
                fuzzy_result.get('fuzzy_matches', {}))
            combined[applicant_id]['total_fuzzy_matches'] += fuzzy_result.get(
                'total_fuzzy_matches', 0)
            combined[applicant_id]['overall_score'] += fuzzy_result.get(
                'overall_score', 0)
        else:
            # Add new fuzzy-only result
            combined[applicant_id] = fuzzy_result.copy()

    # Convert to list and sort by overall score (descending)
    results_list = list(combined.values())
    results_list.sort(key=lambda x: x.get('overall_score', 0), reverse=True)

    return results_list


def validate_search_params(keywords: List[str], algorithm: str, max_results: int,
                           fuzzy_threshold: float) -> tuple:
    """Validate and sanitize search parameters"""
    # Ensure keywords is a list of non-empty strings
    if not isinstance(keywords, list):
        keywords = [str(keywords)] if keywords else []
    keywords = [str(kw).strip().lower() for kw in keywords if str(kw).strip()]

    # Validate algorithm
    valid_algorithms = ["KMP", "BM", "AC"]
    if algorithm not in valid_algorithms:
        algorithm = "KMP"  # Default

    # Validate max_results
    max_results = max(1, min(1000, int(max_results)))  # Between 1 and 1000

    # Validate fuzzy_threshold
    # Between 0.0 and 1.0
    fuzzy_threshold = max(0.0, min(1.0, float(fuzzy_threshold)))

    return keywords, algorithm, max_results, fuzzy_threshold


def calculate_optimal_chunk_size(total_items: int, num_workers: int,
                                 min_chunk_size: int = 5, max_chunk_size: int = 100) -> int:
    """Calculate optimal chunk size for multiprocessing"""
    if total_items <= 0 or num_workers <= 0:
        return min_chunk_size

    # Basic calculation
    chunk_size = max(min_chunk_size, total_items // num_workers)

    # Cap at maximum
    chunk_size = min(chunk_size, max_chunk_size)

    return chunk_size


def should_use_multiprocessing(total_items: int, use_multiprocessing: bool = False,
                               min_threshold: int = 10) -> bool:
    """Determine if multiprocessing should be used based on data size and preference"""
    if not use_multiprocessing:
        return False

    # Only use multiprocessing if we have enough data to make it worthwhile
    return total_items >= min_threshold
