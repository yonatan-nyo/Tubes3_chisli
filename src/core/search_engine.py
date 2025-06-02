import time
from typing import List, Dict, Optional
from database import SessionLocal, Applicant
from algorithms.kmp import KMPMatcher
from algorithms.boyer_moore import BoyerMooreMatcher
from algorithms.aho_corasick import AhoCorasickMatcher
from algorithms.fuzzy_matcher import FuzzyMatcher


class SearchEngine:
    """Main search engine for CV matching"""
    
    def __init__(self):
        # Initialize algorithm matchers
        self.kmp_matcher = KMPMatcher()
        self.boyer_moore_matcher = BoyerMooreMatcher()
        self.aho_corasick_matcher = AhoCorasickMatcher()
        self.fuzzy_matcher = FuzzyMatcher()
    
    def search(self, keywords: List[str], algorithm: str = "KMP", 
               max_results: int = 10, fuzzy_threshold: float = 0.7) -> Dict:
        """Perform CV search with specified algorithm"""
        
        start_time = time.time()
        
        # Get all applicants from database
        db = SessionLocal()
        try:
            applicants = db.query(Applicant).all()
            applicant_dicts = [applicant.to_dict() for applicant in applicants]
        finally:
            db.close()
        
        if not applicant_dicts:
            return {
                'results': [],
                'exact_match_time': 0,
                'fuzzy_match_time': 0,
                'total_time': 0,
                'algorithm_used': algorithm,
                'keywords_searched': keywords
            }
        
        # Perform exact matching
        exact_start = time.time()
        exact_results = self._perform_exact_matching(applicant_dicts, keywords, algorithm)
        exact_time = time.time() - exact_start
        
        # Perform fuzzy matching - pass exact_results as parameter
        fuzzy_start = time.time()
        fuzzy_results = self._perform_fuzzy_matching(applicant_dicts, keywords, fuzzy_threshold, exact_results)
        fuzzy_time = time.time() - fuzzy_start
        
        # Combine and rank results
        combined_results = self._combine_and_rank_results(exact_results, fuzzy_results)
        
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
    
    def _perform_exact_matching(self, applicant_dicts: List[Dict], 
                               keywords: List[str], algorithm: str) -> Dict[int, Dict]:
        """Perform exact matching using specified algorithm"""
        results = {}
        
        if algorithm == "AC":  # Aho-Corasick
            return self._aho_corasick_search(applicant_dicts, keywords)
        
        # For KMP and BM, search each keyword individually
        for applicant in applicant_dicts:
            applicant_id = applicant['id']
            
            # Combine all searchable text
            searchable_text = self._get_searchable_text(applicant).lower()
            
            matches = {}
            total_matches = 0
            
            for keyword in keywords:
                if algorithm == "KMP":
                    occurrences = self.kmp_matcher.search(searchable_text, keyword)
                elif algorithm == "BM":
                    occurrences = self.boyer_moore_matcher.search(searchable_text, keyword)
                else:
                    # Default to KMP
                    occurrences = self.kmp_matcher.search(searchable_text, keyword)
                
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
            applicant_id = applicant['id']
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
                               threshold: float, exact_results: Dict[int, Dict]) -> Dict[int, Dict]:
        """Perform fuzzy matching for keywords without exact matches"""
        fuzzy_results = {}
        
        # Find keywords that had no exact matches
        keywords_with_exact_matches = set()
        for result in exact_results.values():
            keywords_with_exact_matches.update(result['exact_matches'].keys())
        
        keywords_for_fuzzy = [kw for kw in keywords if kw not in keywords_with_exact_matches]
        
        if not keywords_for_fuzzy:
            return fuzzy_results
        
        for applicant in applicant_dicts:
            applicant_id = applicant['id']
            searchable_text = self._get_searchable_text(applicant)
            
            # Extract words from searchable text
            words = set(searchable_text.lower().split())
            
            fuzzy_matches = {}
            total_fuzzy_score = 0
            
            for keyword in keywords_for_fuzzy:
                best_match = None
                best_similarity = 0
                
                for word in words:
                    similarity = self.fuzzy_matcher.similarity_ratio(keyword, word)
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
                    exact_results[applicant_id]['total_fuzzy_matches'] = len(fuzzy_matches)
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
        """Combine all searchable text from applicant data"""
        text_parts = []
        
        # Basic info
        text_parts.append(applicant.get('name', ''))
        text_parts.append(applicant.get('email', ''))
        text_parts.append(applicant.get('summary', ''))
        
        # Skills
        if applicant.get('skills'):
            text_parts.extend(applicant['skills'])
        
        # Work experience
        if applicant.get('work_experience'):
            for exp in applicant['work_experience']:
                text_parts.append(exp.get('position', ''))
                text_parts.append(exp.get('company', ''))
                text_parts.append(exp.get('description', ''))
        
        # Education
        if applicant.get('education'):
            for edu in applicant['education']:
                text_parts.append(edu.get('degree', ''))
                text_parts.append(edu.get('institution', ''))
        
        # Full extracted text as fallback
        text_parts.append(applicant.get('extracted_text', ''))
        
        return ' '.join(text_parts)
    
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
    
    def get_applicant_details(self, applicant_id: int) -> Optional[Dict]:
        """Get detailed information for specific applicant"""
        db = SessionLocal()
        try:
            applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
            if applicant:
                return applicant.to_dict()
        finally:
            db.close()
        return None
