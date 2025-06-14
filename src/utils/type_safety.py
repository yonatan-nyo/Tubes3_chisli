"""
Type safety utilities for the CV matching system.
This module provides type checking and validation utilities to prevent runtime errors.
"""

from typing import Dict, List, Any, Optional, Union, TypeGuard, TypeVar, Callable
import json
from dataclasses import dataclass
from datetime import datetime

T = TypeVar('T')


@dataclass
class ApplicantDataSchema:
    """Type-safe schema for applicant data passed between components"""
    detail_id: int
    applicant_id: int
    name: str
    email: str
    phone: str
    cv_path: str
    extracted_text: str
    summary: str
    skills: List[str]
    work_experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    highlights: List[str]
    accomplishments: List[str]
    created_at: str
    applicant_role: str
    address: str
    date_of_birth: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicantDataSchema':
        """Create ApplicantDataSchema from dictionary with validation"""
        return cls(
            detail_id=safe_get_int(data, 'detail_id', 0),
            applicant_id=safe_get_int(data, 'applicant_id', 0),
            name=safe_get_str(data, 'name', 'Unknown'),
            email=safe_get_str(data, 'email', 'Not provided'),
            phone=safe_get_str(data, 'phone', 'Not provided'),
            cv_path=safe_get_str(data, 'cv_path', ''),
            extracted_text=safe_get_str(data, 'extracted_text', ''),
            summary=safe_get_str(data, 'summary', ''),
            skills=safe_get_list(data, 'skills', []),
            work_experience=safe_get_list(data, 'work_experience', []),
            education=safe_get_list(data, 'education', []),
            highlights=safe_get_list(data, 'highlights', []),
            accomplishments=safe_get_list(data, 'accomplishments', []),
            created_at=safe_get_str(data, 'created_at', 'Unknown'),
            applicant_role=safe_get_str(
                data, 'applicant_role', 'Not specified'),
            address=safe_get_str(data, 'address', 'Not provided'),
            date_of_birth=safe_get_str(data, 'date_of_birth', 'Not provided')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return {
            'detail_id': self.detail_id,
            'applicant_id': self.applicant_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'cv_path': self.cv_path,
            'extracted_text': self.extracted_text,
            'summary': self.summary,
            'skills': self.skills,
            'work_experience': self.work_experience,
            'education': self.education,
            'highlights': self.highlights,
            'accomplishments': self.accomplishments,
            'created_at': self.created_at,
            'applicant_role': self.applicant_role,
            'address': self.address,
            'date_of_birth': self.date_of_birth
        }


@dataclass
class SearchResultSchema:
    """Type-safe schema for search results"""
    results: List[Dict[str, Any]]
    exact_match_time: float
    fuzzy_match_time: float
    total_time: float
    algorithm_used: str
    keywords_searched: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchResultSchema':
        """Create SearchResultSchema from dictionary with validation"""
        return cls(
            results=safe_get_list(data, 'results', []),
            exact_match_time=safe_get_float(data, 'exact_match_time', 0.0),
            fuzzy_match_time=safe_get_float(data, 'fuzzy_match_time', 0.0),
            total_time=safe_get_float(data, 'total_time', 0.0),
            algorithm_used=safe_get_str(data, 'algorithm_used', 'Unknown'),
            keywords_searched=safe_get_list(data, 'keywords_searched', [])
        )


def is_dict(obj: Any) -> TypeGuard[Dict[str, Any]]:
    """Type guard to check if object is a dictionary"""
    return isinstance(obj, dict)


def is_list(obj: Any) -> TypeGuard[List[Any]]:
    """Type guard to check if object is a list"""
    return isinstance(obj, list)


def is_string(obj: Any) -> TypeGuard[str]:
    """Type guard to check if object is a string"""
    return isinstance(obj, str)


def is_int(obj: Any) -> TypeGuard[int]:
    """Type guard to check if object is an integer"""
    return isinstance(obj, int)


def is_float(obj: Any) -> TypeGuard[float]:
    """Type guard to check if object is a float"""
    return isinstance(obj, (int, float))


def safe_get_str(data: Any, key: str, default: str = '') -> str:
    """Safely get string value from dictionary-like object"""
    if not is_dict(data):
        return default

    value = data.get(key, default)
    if value is None:
        return default

    return str(value)


def safe_get_int(data: Any, key: str, default: int = 0) -> int:
    """Safely get integer value from dictionary-like object"""
    if not is_dict(data):
        return default

    value = data.get(key, default)
    if value is None:
        return default

    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_get_float(data: Any, key: str, default: float = 0.0) -> float:
    """Safely get float value from dictionary-like object"""
    if not is_dict(data):
        return default

    value = data.get(key, default)
    if value is None:
        return default

    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_get_list(data: Any, key: str, default: Optional[List[Any]] = None) -> List[Any]:
    """Safely get list value from dictionary-like object"""
    if default is None:
        default = []

    if not is_dict(data):
        return default

    value = data.get(key, default)
    if value is None:
        return default

    if is_list(value):
        return value

    # Try to parse JSON if it's a string
    if is_string(value):
        try:
            parsed = json.loads(value)
            if is_list(parsed):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    return default


def safe_get_dict(data: Any, key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Safely get dictionary value from dictionary-like object"""
    if default is None:
        default = {}

    if not is_dict(data):
        return default

    value = data.get(key, default)
    if value is None:
        return default

    if is_dict(value):
        return value

    # Try to parse JSON if it's a string
    if is_string(value):
        try:
            parsed = json.loads(value)
            if is_dict(parsed):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    return default


def validate_applicant_data(data: Any) -> ApplicantDataSchema:
    """Validate and convert applicant data to type-safe schema"""
    if not is_dict(data):
        raise TypeError(f"Expected dictionary, got {type(data)}")

    return ApplicantDataSchema.from_dict(data)


def validate_search_results(data: Any) -> SearchResultSchema:
    """Validate and convert search results to type-safe schema"""
    if not is_dict(data):
        raise TypeError(f"Expected dictionary, got {type(data)}")

    return SearchResultSchema.from_dict(data)


def safe_call(func: Callable[..., T], *args, **kwargs) -> Optional[T]:
    """Safely call a function and return None if it fails"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Safe call failed for {func.__name__}: {e}")
        return None


def ensure_string(value: Any, default: str = '') -> str:
    """Ensure value is a string, convert if possible, return default if not"""
    if value is None:
        return default
    if is_string(value):
        return value
    try:
        return str(value)
    except (ValueError, TypeError):
        return default


def ensure_list(value: Any, default: Optional[List[Any]] = None) -> List[Any]:
    """Ensure value is a list, convert if possible, return default if not"""
    if default is None:
        default = []

    if value is None:
        return default
    if is_list(value):
        return value

    # Try to convert single item to list
    try:
        return [value]
    except Exception:
        return default


def format_datetime_safe(dt: Any, format_str: str = "%Y-%m-%d %H:%M:%S", default: str = "Unknown") -> str:
    """Safely format datetime object to string"""
    if dt is None:
        return default

    if isinstance(dt, datetime):
        try:
            return dt.strftime(format_str)
        except (ValueError, TypeError):
            return default

    if is_string(dt):
        return dt

    return default


def parse_json_safe(json_str: Any, default: Any = None) -> Any:
    """Safely parse JSON string"""
    if not is_string(json_str):
        return default

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


class TypeSafetyError(Exception):
    """Custom exception for type safety violations"""
    pass


def assert_type(obj: Any, expected_type: type, message: str = "") -> None:
    """Assert that object is of expected type, raise TypeSafetyError if not"""
    if not isinstance(obj, expected_type):
        if message:
            raise TypeSafetyError(
                f"{message}: Expected {expected_type.__name__}, got {type(obj).__name__}")
        else:
            raise TypeSafetyError(
                f"Expected {expected_type.__name__}, got {type(obj).__name__}")


def assert_dict_has_keys(data: Dict[str, Any], required_keys: List[str]) -> None:
    """Assert that dictionary has all required keys"""
    if not is_dict(data):
        raise TypeSafetyError(
            f"Expected dictionary, got {type(data).__name__}")

    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        raise TypeSafetyError(f"Missing required keys: {missing_keys}")
