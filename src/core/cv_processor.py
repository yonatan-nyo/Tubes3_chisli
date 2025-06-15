import pdfplumber
import re
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil
import pandas as pd
from database.models.applicant import ApplicantProfile, ApplicantDetail
from database.models.database import SessionLocal


class CVProcessor:
    """Process CV files and extract information with robust PDF handling"""

    def __init__(self, debug_mode: bool = False, show_progress: bool = True):
        self.cv_storage_path = "data/cv_files"
        self.txt_storage_path = "data/extracted_text"
        self.debug_mode = debug_mode
        self.show_progress = show_progress
        self.extracted_texts = {}  # Cache for extracted texts

        # Regex patterns for extracting CV information (from regex_extractor example)
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(?:(?:\+?\d{1,3})?[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2,3}\d{3,4}',
            'linkedin': r'(?:linkedin\.com/in/|linkedin\.com/pub/)([a-zA-Z0-9-]+)',
            'date': r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}\b',
            'education_degree': r'\b(?:Bachelor|Master|PhD|Ph\.D|MBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|BSc|MSc|BA|MA|BBA|A\.A\.|Associates?|Diploma|Certificate|High School Diploma)\b',
            'years_experience': r'\b\d+\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?\b',
        }

        self._ensure_storage_directories()

    def _ensure_storage_directories(self):
        """Ensure CV and text storage directories exist"""
        if not os.path.exists(self.cv_storage_path):
            os.makedirs(self.cv_storage_path)
        if not os.path.exists(self.txt_storage_path):
            os.makedirs(self.txt_storage_path)

        # Create debug directory if debug mode is enabled
        if self.debug_mode:
            debug_dir = "debug_cv_extraction"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)

    def _save_debug(self, filename: str, content: str, cv_name: str = ""):
        """Save debug information for troubleshooting PDF extraction"""
        if not self.debug_mode:
            return

        try:
            debug_dir = "debug_cv_extraction"

            # Add CV name to filename if provided
            if cv_name:
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{cv_name}{ext}"

            filepath = os.path.join(debug_dir, filename)
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content)
        except Exception as e:
            print(f"Debug save failed for {filename}: {e}")

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF with robust cleaning and debugging"""
        try:
            cv_name = os.path.basename(file_path).replace('.pdf', '')
            raw_text = ""

            # Check cache first
            if file_path in self.extracted_texts:
                return self.extracted_texts[file_path]

            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)

                if self.show_progress:
                    print(
                        f"Extracting text from {cv_name} ({page_count} pages)...")

                # Debug: Save page count
                self._save_debug(
                    "1_page_count.txt", f"PDF: {cv_name}\nPages: {page_count}", cv_name)

                # Extract text from all pages
                page_texts = []
                for page_num, page in enumerate(pdf.pages):
                    # Use pdfplumber's advanced text extraction with tolerance
                    page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
                    if page_text:
                        page_texts.append(
                            f"=== PAGE {page_num + 1} ===\n{page_text}\n")
                        raw_text += page_text + "\n"

                # Save raw extracted text for debugging
                self._save_debug("2_raw_extracted.txt",
                                 "\n".join(page_texts), cv_name)

                # Clean text using robust cleaning method
                cleaned_text = self._clean_text(raw_text, cv_name)

                # Cache the result
                self.extracted_texts[file_path] = cleaned_text

                return cleaned_text

        except Exception as e:
            error_msg = f"Error extracting text from {file_path}: {e}"
            print(error_msg)
            self._save_debug("extraction_error.txt", error_msg, cv_name)
            return ""

    def _clean_text(self, text: str, cv_name: str = "") -> str:
        """Clean extracted text while preserving structure"""
        if not text:
            return ""

        # Save original text for debugging
        self._save_debug("3_before_cleaning.txt",
                         f"Length: {len(text)}\n\n{text}", cv_name)

        # Step 1: Replace common PDF artifacts and encoding issues
        replacements = {
            'ï¼': ':',          # Corrupted colon
            '：': ':',          # Full-width colon
            'Â': '',            # Spurious character
            'â€‹': '',          # Zero-width space
            'â€"': '-',         # Em dash
            'â€™': "'",         # Smart quote
            'â€œ': '"',         # Smart quote open
            'â€': '"',          # Smart quote close
            'â—': '•',          # Bullet point
            '\xa0': ' ',        # Non-breaking space
            '\r': '',           # Carriage return
            '\ufeff': '',       # Byte order mark
            '\u200b': '',       # Zero-width space
            '\u200c': '',       # Zero-width non-joiner
            '\u200d': '',       # Zero-width joiner
        }

        cleaned = text
        artifacts_found = []

        for old, new in replacements.items():
            count = cleaned.count(old)
            if count > 0:
                artifacts_found.append(
                    f"'{old}' -> '{new}': {count} occurrences")
                cleaned = cleaned.replace(old, new)

        # Save artifacts found for debugging
        if artifacts_found:
            self._save_debug("4_artifacts_found.txt",
                             "\n".join(artifacts_found), cv_name)

        # Step 2: Fix spacing while preserving line structure
        lines = cleaned.split('\n')
        cleaned_lines = []

        for line in lines:
            # Remove leading/trailing spaces
            line = line.strip()
            # Replace multiple spaces with single space
            line = ' '.join(line.split())
            cleaned_lines.append(line)

        # Join lines back together
        cleaned = '\n'.join(cleaned_lines)

        # Step 3: Remove excessive line breaks (more than 2 consecutive)
        while '\n\n\n' in cleaned:
            cleaned = cleaned.replace('\n\n\n', '\n\n')

        # Step 4: Remove non-printable characters except newlines and tabs
        cleaned = ''.join(
            char for char in cleaned if char.isprintable() or char in '\n\t')

        # Save cleaned text for debugging
        self._save_debug("5_after_cleaning.txt",
                         f"Length: {len(cleaned)}\nLines: {len(cleaned.split(chr(10)))}\n\n{cleaned}",
                         cv_name)

        return cleaned.strip()

    def extract_application_role(self, text: str) -> str:
        """Extract applicant role from CV text - first line is the applicant role"""
        if not text:
            return ""

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # The first line is the applicant role
        if lines:
            return lines[0]

        return ""

    def extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information from CV text using regex patterns"""
        info = {}

        try:
            # Look at first 1000 chars for personal info
            text_start = text[:1000]

            # Extract email
            email_match = re.search(self.patterns['email'], text)
            if email_match:
                info['email'] = email_match.group(0)

            # Extract phone - look for phone patterns
            phone_patterns = [
                r'(?:Phone|Tel|Mobile|Cell|Contact)[\s:]*([+\d\s\-\(\)\.]+)',
                r'\b(?:\+?1)?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b'
            ]

            for pattern in phone_patterns:
                phone_match = re.search(pattern, text[:1000], re.IGNORECASE)
                if phone_match:
                    phone = phone_match.group(
                        1) if phone_match.lastindex else phone_match.group(0)
                    phone = phone.strip()
                    digits = re.sub(r'\D', '', phone)
                    if len(digits) >= 10:
                        info['phone'] = phone
                        break

            # Extract LinkedIn
            linkedin_match = re.search(
                self.patterns['linkedin'], text, re.IGNORECASE)
            if linkedin_match:
                info['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"

            # Extract name - usually at the beginning
            name_patterns = [
                r'^([A-Z][A-Z\s]+)(?:\n|$)',  # All caps name at start
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Title case full name
                r'(?:Name|Nama)[\s:]*([A-Z][a-zA-Z\s]+)(?:\n|$)',
            ]

            for pattern in name_patterns:
                name_match = re.search(pattern, text_start, re.MULTILINE)
                if name_match:
                    name = name_match.group(1).strip()
                    job_titles = ['ACCOUNTANT', 'MANAGER', 'ENGINEER', 'DEVELOPER', 'ANALYST',
                                  'ADMINISTRATOR', 'DIRECTOR', 'SUPERVISOR', 'COORDINATOR', 'ADVOCATE',
                                  'FINANCIAL', 'CONSUMER']
                    if name and not any(title in name.upper() for title in job_titles):
                        if name.isupper() and len(name.split()) > 1:
                            name = name.title()
                        info['name'] = name
                        break

            # Save debug info
            self._save_debug("personal_info_extracted.txt", f"Extracted: {info}",
                             f"personal_{datetime.now().strftime('%H%M%S')}")

        except Exception as e:
            print(f"Error extracting personal info: {e}")

        return info

    def _extract_section_content(self, text: str, section_name: str) -> str:
        """Extract content between section headers using case insensitive matching"""
        if not text:
            return ""

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        section_content = []
        in_section = False

        # Section headers to recognize (case insensitive)
        section_headers = ['skills', 'summary', 'highlights',
                           'accomplishments', 'experience', 'education']
        target_section = section_name.lower()

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check if this line is the target section header
            if line_lower == target_section:
                in_section = True
                continue

            # Check if this line is any other section header
            elif line_lower in section_headers and line_lower != target_section:
                if in_section:
                    break
                continue

            # If we're in the target section, collect content
            if in_section:
                section_content.append(line)

        return '\n'.join(section_content).strip()

    def extract_summary(self, text: str) -> str:
        """Extract summary/objective section using regex patterns"""
        try:
            # Look for Summary section - more specific patterns
            summary_patterns = [
                r'(?i)Summary\s*(?:\n|:)?\s*([^\n]+(?:\n(?!Skills|Experience|Education|Highlights)[^\n]+)*)',
                r'(?i)(?:Objective|Profile|Professional Profile|About|Overview)\s*(?:\n|:)?\s*([^\n]+(?:\n(?!Skills|Experience|Education)[^\n]+)*)'
            ]

            for pattern in summary_patterns:
                match = re.search(pattern, text)
                if match:
                    summary = match.group(1).strip()
                    # Clean up summary
                    summary = re.sub(r'\s+', ' ', summary)
                    summary = summary.replace('•', '').strip()

                    # Make sure it's not too short or too long
                    if 20 < len(summary) < 1000:
                        self._save_debug("summary_extracted.txt", f"Pattern: {pattern}\nExtracted: {summary}",
                                         f"summary_{datetime.now().strftime('%H%M%S')}")
                        return summary[:500]

            # Fallback to section-based extraction
            return self._extract_section_content(text, 'Summary')

        except Exception as e:
            print(f"Error extracting summary: {e}")
            return ""

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills section using regex patterns"""
        skills = []

        try:
            # Pattern to find Skills section - more flexible
            skills_patterns = [
                r'(?i)Skills\s*(?:\n|:)\s*(.*?)(?=\n(?:Experience|Education|Employment|Professional|$))',
                r'(?i)(?:Technical\s+)?Skills\s*(?:\n|:)\s*(.*?)(?=\n\n)',
                r'(?i)Highlights\s*(?:\n|:)\s*(.*?)(?=\n(?:Experience|Education|Accomplishments|$))',
            ]

            skills_text = ""
            for pattern in skills_patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    skills_text = match.group(1)
                    break

            if skills_text:
                # Extract individual skills - handle both bullet points and regular text
                lines = skills_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Check if line contains a colon (skill category)
                    if ':' in line:
                        # Extract skills after colon
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            skill_part = parts[1].strip()
                            # Split by common separators
                            if any(sep in skill_part for sep in [',', ';', '•']):
                                sub_skills = re.split(r'[,;•]', skill_part)
                                for skill in sub_skills:
                                    skill = skill.strip()
                                    if skill and len(skill) > 2:
                                        skills.append(skill)
                            elif len(skill_part) > 2:
                                skills.append(skill_part)
                    else:
                        # It's a standalone skill line
                        if len(line) > 2 and not any(word in line.lower() for word in ['experience', 'education', 'employment']):
                            skills.append(line)

            # Also look for technical skills mentioned in the text
            tech_pattern = r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Swift|Kotlin|Go|R\b|SQL|NoSQL|MongoDB|MySQL|PostgreSQL|Oracle|HTML5?|CSS3?|React|Angular|Vue|Node\.js|Django|Flask|Spring|\.NET|Docker|Kubernetes|AWS|Azure|GCP|Git|Machine Learning|Data Science|AI|DevOps|Linux|Windows|Excel|PowerBI|Tableau|QuickBooks|SAP|ERP|Accounting|Financial Reporting|Budget|Audit|Payroll|Tax|GAAP|Financial Analysis|Microsoft Office|CPA|Customer Service|Communication|Leadership)\b'
            tech_matches = re.findall(tech_pattern, text, re.IGNORECASE)

            for tech in tech_matches:
                if tech not in skills:
                    skills.append(tech)

            # Remove duplicates while preserving order
            seen = set()
            unique_skills = []
            for skill in skills:
                skill_lower = skill.lower()
                if skill_lower not in seen and len(skill) < 100:
                    seen.add(skill_lower)
                    unique_skills.append(skill)

            # Save debug info
            self._save_debug("skills_final.txt", "\n".join(unique_skills),
                             f"skills_{datetime.now().strftime('%H%M%S')}")

            return unique_skills[:20]

        except Exception as e:
            print(f"Error extracting skills: {e}")
            # Fallback to simple section-based extraction
            content = self._extract_section_content(text, 'Skills')
            if content:
                return [line.strip() for line in content.split('\n') if line.strip()][:20]
            return []

    def extract_highlights(self, text: str) -> List[str]:
        """Extract highlights section - split by capitalized characters"""
        content = self._extract_section_content(text, 'Highlights')
        if not content:
            return []

        # Split by lines and clean up
        highlights = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                # Split by capitalized characters (new highlight starts with capital letter)
                # Use regex to split before capital letters, but keep the capital letter
                parts = re.split(r'(?=[A-Z][a-z])', line)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 1:  # Ignore single characters
                        highlights.append(part)

        return highlights

    def extract_accomplishments(self, text: str) -> List[str]:
        """Extract accomplishments section"""
        content = self._extract_section_content(text, 'Accomplishments')
        if not content:
            return []

        # Split by lines and clean up
        accomplishments = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                # Check if line contains multiple accomplishments separated by multiple spaces
                if '  ' in line:  # Two or more spaces
                    parts = re.split(r'\s{2,}', line)
                    for part in parts:
                        part = part.strip()
                        if part:
                            accomplishments.append(part)
                else:
                    accomplishments.append(line)

        return accomplishments

    def extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience using regex patterns for better accuracy"""
        experience = []

        try:
            # Find Experience section
            exp_patterns = [
                r'(?i)Experience\s*(?:\n|:)?\s*(.*?)(?=Education|Skills|Professional\s+Affiliations|Languages|$)',
                r'(?i)(?:Employment|Work\s+History|Professional\s+Experience)\s*(?:\n|:)?\s*(.*?)(?=Education|Skills|$)',
            ]

            exp_text = ""
            for pattern in exp_patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    exp_text = match.group(1).strip()
                    self._save_debug("experience_section.txt", f"Pattern: {pattern}\nExtracted: {exp_text}",
                                     f"exp_{datetime.now().strftime('%H%M%S')}")
                    break

            if exp_text:
                # Pattern to match date ranges and job entries
                # More flexible pattern to handle various formats
                job_patterns = [
                    # Pattern 1: MM/YYYY to MM/YYYY or Current
                    r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current|Present)\s*\n?\s*([^\n]+?)\s+Company\s*Name\s*[:：]\s*([^\n]+)',
                    # Pattern 2: Date to Date followed by position
                    r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current|Present)\s*\n?\s*([^\n]+)',
                    # Pattern 3: Any date pattern
                    r'([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4})\s+to\s+([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4}|Current|Present)\s*\n?\s*([^\n]+)',
                ]

                # Try each pattern
                for pattern in job_patterns:
                    matches = list(re.finditer(
                        pattern, exp_text, re.MULTILINE))
                    if matches:
                        self._save_debug("experience_matches.txt", f"Pattern: {pattern}\nMatches: {len(matches)}",
                                         f"exp_matches_{datetime.now().strftime('%H%M%S')}")
                        for match in matches:
                            start_date = match.group(1)
                            end_date = match.group(2)
                            position = match.group(3).strip()

                            # Get company if available (for pattern 1)
                            company = ""
                            if match.lastindex >= 4:
                                company = match.group(4).strip()

                            # Extract first responsibility line
                            remaining_text = exp_text[match.end():]
                            resp_lines = remaining_text.split('\n')
                            responsibility = ""
                            for line in resp_lines:
                                line = line.strip()
                                if line and len(line) > 20 and not re.match(r'\d{1,2}/\d{4}', line):
                                    responsibility = line
                                    break

                            # Create experience entry
                            exp_entry = {
                                'start_date': start_date,
                                'end_date': end_date,
                                'position': position,
                                'company': company if company else 'Not specified',
                                'description': responsibility[:150] + '...' if responsibility else ''
                            }

                            experience.append(exp_entry)

                            if len(experience) >= 5:
                                break

                        if experience:
                            break

            # Fallback to simple section-based extraction if regex patterns don't work
            if not experience:
                content = self._extract_section_content(text, 'Experience')
                if content:
                    lines = [line.strip()
                             for line in content.split('\n') if line.strip()]
                    date_pattern = r'^\d{2}/\d{4}\s*[-–]\s*\d{2}/\d{4}$|^\d{2}/\d{4}\s*[-–]\s*(?:Present|Current)$|^\d{4}\s*[-–]\s*\d{4}$'

                    i = 0
                    while i < len(lines) and len(experience) < 5:
                        line = lines[i]
                        if re.match(date_pattern, line, re.IGNORECASE):
                            exp_entry = {
                                'start_date': '',
                                'end_date': '',
                                'position': '',
                                'company': 'Not specified',
                                'description': ''
                            }

                            # Parse date
                            if ' - ' in line or ' – ' in line:
                                parts = re.split(r'\s*[-–]\s*', line)
                                if len(parts) == 2:
                                    exp_entry['start_date'] = parts[0].strip()
                                    exp_entry['end_date'] = parts[1].strip()

                            # Get company/position from next line
                            if i + 1 < len(lines):
                                exp_entry['position'] = lines[i + 1]
                                i += 2
                            else:
                                i += 1

                            if exp_entry['start_date']:
                                experience.append(exp_entry)
                        else:
                            i += 1

            # Save debug info
            self._save_debug("experience_final.txt",
                             "\n\n".join([f"{exp['position']} at {exp['company']} ({exp['start_date']} - {exp['end_date']})"
                                          for exp in experience]),
                             f"exp_final_{datetime.now().strftime('%H%M%S')}")

            return experience[:5]

        except Exception as e:
            print(f"Error extracting work experience: {e}")
            return []

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information using regex patterns"""
        education = []

        try:
            # Find Education section
            edu_patterns = [
                r'(?i)Education(?:\s+and\s+Training)?\s*(?:\n|:)?\s*(.*?)(?=Skills|Professional|Certificates|Languages|$)',
                r'(?i)(?:Academic|Qualifications?)\s*(?:\n|:)?\s*(.*?)(?=Skills|Professional|$)',
            ]

            edu_text = ""
            for pattern in edu_patterns:
                match = re.search(pattern, text, re.DOTALL)
                if match:
                    edu_text = match.group(1).strip()
                    self._save_debug("education_section.txt", f"Pattern: {pattern}\nExtracted: {edu_text}",
                                     f"edu_{datetime.now().strftime('%H%M%S')}")
                    break

            if edu_text:
                # Pattern to match education entries
                # Looking for patterns like: "January 2014 Master's : Business Administration Troy University"
                edu_entry_patterns = [
                    # Pattern 1: Month Year Degree : Field University
                    r'([A-Za-z]+\s+\d{4})\s+([^:\n]+)\s*:\s*([^\n]+?)\s+([A-Z][^\n]+(?:University|College|Institute|School))',
                    # Pattern 2: Year Degree in/of Field - University
                    r'(\d{4})\s+([^:\n]+?)\s+(?:in|of)\s+([^\n-]+)\s*-?\s*([A-Z][^\n]+(?:University|College|Institute|School))',
                    # Pattern 3: Degree : Field University Location
                    r'([^:\n]+)\s*:\s*([^\n]+?)\s+([A-Z][^\n]+(?:University|College|Institute|School))\s*[:：]\s*([^\n]+)',
                ]

                # Try to match education entries
                for pattern in edu_entry_patterns:
                    matches = list(re.finditer(
                        pattern, edu_text, re.MULTILINE))
                    if matches:
                        self._save_debug("education_matches.txt", f"Pattern: {pattern}\nMatches: {len(matches)}",
                                         f"edu_matches_{datetime.now().strftime('%H%M%S')}")
                        for match in matches:
                            if match.lastindex >= 4:
                                # Extract components based on pattern
                                if 'Month' in pattern or 'Year' in pattern:
                                    date = match.group(1)
                                    degree = match.group(2).strip()
                                    field = match.group(3).strip()
                                    institution = match.group(4).strip()

                                    edu_entry = {
                                        'graduation_year': date,
                                        'degree': degree,
                                        'institution': institution,
                                        'gpa': '',
                                        'description': f"{degree} in {field}"
                                    }
                                else:
                                    degree = match.group(1).strip()
                                    field = match.group(2).strip()
                                    institution = match.group(3).strip()

                                    edu_entry = {
                                        'graduation_year': '',
                                        'degree': degree,
                                        'institution': institution,
                                        'gpa': '',
                                        'description': f"{degree} in {field}"
                                    }
                            else:
                                # Fallback: just use the matched text
                                edu_entry = {
                                    'graduation_year': '',
                                    'degree': match.group(0).strip(),
                                    'institution': '',
                                    'gpa': '',
                                    'description': ''
                                }

                            education.append(edu_entry)

                            if len(education) >= 3:
                                break

                        if education:
                            break

                # If no structured matches, try to extract any degree mentions
                if not education:
                    degree_matches = re.finditer(
                        self.patterns['education_degree'], edu_text, re.IGNORECASE)
                    for match in degree_matches:
                        # Get context around the degree
                        start = max(0, match.start() - 50)
                        end = min(len(edu_text), match.end() + 100)
                        context = edu_text[start:end].strip()
                        # Clean up the context
                        context = re.sub(r'\s+', ' ', context)
                        if context:
                            edu_entry = {
                                'graduation_year': '',
                                'degree': match.group(0),
                                'institution': '',
                                'gpa': '',
                                'description': context
                            }
                            education.append(edu_entry)
                            if len(education) >= 3:
                                break

            # Fallback to simple section-based extraction if regex patterns don't work
            if not education:
                content = self._extract_section_content(text, 'Education')
                if content:
                    lines = [line.strip()
                             for line in content.split('\n') if line.strip()]
                    year_pattern = r'^(19[5-9]\d|20[0-9]\d)$'

                    i = 0
                    while i < len(lines) and len(education) < 3:
                        line = lines[i]
                        if re.match(year_pattern, line):
                            edu_entry = {
                                'graduation_year': line,
                                'degree': '',
                                'institution': '',
                                'gpa': '',
                                'description': ''
                            }

                            if i + 1 < len(lines):
                                edu_entry['institution'] = lines[i + 1]
                                i += 2
                            else:
                                i += 1

                            education.append(edu_entry)
                        else:
                            i += 1

            # Save debug info
            self._save_debug("education_final.txt",
                             "\n\n".join([f"{edu['degree']} - {edu['institution']} ({edu['graduation_year']})"
                                          for edu in education]),
                             f"edu_final_{datetime.now().strftime('%H%M%S')}")

            return education[:3]

        except Exception as e:
            print(f"Error extracting education: {e}")
            return []

    def save_extracted_text_to_file(self, extracted_text: str, original_cv_filename: str) -> str:
        """Save extracted text to a TXT file, using original CV filename for naming."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(original_cv_filename)[0]
            safe_base_name = re.sub(r'[^\w\.-]', '_', base_name)
            txt_filename = f"{timestamp}_{safe_base_name}_extracted.txt"
            txt_filepath = os.path.join(
                self.txt_storage_path, txt_filename).replace('\\', '/')
            with open(txt_filepath, 'w', encoding='utf-8') as txt_file:
                txt_file.write("=" * 50 + "\nEXTRACTED TEXT FROM CV\n")
                txt_file.write(f"Source Reference: {original_cv_filename}\n")
                txt_file.write(
                    f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                txt_file.write("=" * 50 + "\n\n")
                txt_file.write(
                    extracted_text if extracted_text else "No text extracted or content was empty.")
                txt_file.write("\n\n" + "=" * 50 +
                               "\nEND OF EXTRACTED TEXT\n" + "=" * 50)
            return txt_filepath
        except Exception as e:
            print(
                f"Error saving extracted text to file for {original_cv_filename}: {e}")
            return ""

    def process_cv_file(self, file_path: str, original_filename: str, applicant_id: Optional[int] = None) -> Optional[int]:
        """Process uploaded CV file (PDF) and save to database with improved extraction"""
        try:
            if self.show_progress:
                print(f"Processing CV file: {original_filename}")

            # Extract text using robust method
            extracted_text = self.extract_text_from_pdf(file_path)
            if not extracted_text:
                print(
                    f"No text extracted from PDF: {original_filename}. Skipping.")
                return None

            # Generate safe filename for storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_original_filename = re.sub(
                r'[^\w\.-]', '_', original_filename)
            stored_cv_filename = f"{timestamp}_{safe_original_filename}"
            stored_cv_path = os.path.join(
                self.cv_storage_path, stored_cv_filename).replace('\\', '/')

            # Copy CV to storage
            shutil.copy2(file_path, stored_cv_path)
            if self.show_progress:
                print(f"CV stored at: {stored_cv_path}")

            # Save extracted text to file
            txt_filepath = self.save_extracted_text_to_file(
                extracted_text, original_filename)
            if not txt_filepath:
                print(f"Failed to save extracted text for {original_filename}")
                return None

            # Process and save to database
            return self._process_common_resume_text(
                extracted_text,
                original_filename,
                cv_path_for_db=stored_cv_path,
                txt_path_for_db=txt_filepath,
                category=None,
                applicant_id=applicant_id
            )

        except Exception as e:
            print(f"Error processing CV file {original_filename}: {e}")
            self._save_debug("cv_processing_error.txt",
                             f"File: {original_filename}\nError: {str(e)}",
                             original_filename.replace('.pdf', ''))
            return None

    def _process_common_resume_text(self, extracted_text: str, source_reference: str,
                                    cv_path_for_db: Optional[str], txt_path_for_db: Optional[str],
                                    category: Optional[str] = None, applicant_id: Optional[int] = None) -> Optional[int]:
        """Common logic to process extracted text and save to DB using new schema."""
        # Extract applicant role from first line
        application_role = self.extract_application_role(extracted_text)

        # Ensure cv_path is never None to satisfy nullable=False constraint
        final_cv_path_for_db = cv_path_for_db
        if final_cv_path_for_db is None:
            if txt_path_for_db:
                final_cv_path_for_db = txt_path_for_db  # Use txt_path as fallback for cv_path
            else:
                # This is a last resort, should ideally not be hit if txt_file always saves
                # If no applicant_id is provided, use a random existing applicant
                final_cv_path_for_db = f"MISSING_FILE_PATH_FOR_{source_reference.replace('.', '_')}"
        if applicant_id is None:
            applicant_id = self._get_random_existing_applicant()

        applicant_detail_data = {
            'applicant_id': applicant_id,
            'application_role': application_role,
            'cv_path': final_cv_path_for_db
        }

        db = SessionLocal()
        try:
            # Create ApplicantDetail record
            applicant_detail = ApplicantDetail.from_dict(applicant_detail_data)
            db.add(applicant_detail)
            db.commit()
            db.refresh(applicant_detail)

            return applicant_detail.detail_id

        except Exception as e:
            print(f"ERROR: Failed to save CV to database: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def _get_random_existing_applicant(self) -> int:
        """Get a random existing applicant profile for uploads without specified applicant"""
        db = SessionLocal()
        try:
            # Get a random existing applicant from the database
            import random
            applicants = db.query(ApplicantProfile).all()

            if applicants:
                # Select a random applicant from existing ones
                random_applicant = random.choice(applicants)
                return random_applicant.applicant_id
            else:
                # If no applicants exist, create a default one
                default_applicant = ApplicantProfile(
                    first_name="Default",
                    last_name="User",
                    address="System generated profile for CV uploads"
                )

                # Encrypt the default applicant data before saving
                encrypted_default = default_applicant.encrypt_data()
                db.add(encrypted_default)
                db.commit()
                db.refresh(encrypted_default)

                print(
                    f"Created encrypted default applicant with ID: {encrypted_default.applicant_id}")
                return encrypted_default.applicant_id

        except Exception as e:
            print(f"Error getting random applicant: {e}")
            db.rollback()            # Return a default ID (1) as fallback
            return 1
        finally:
            db.close()

    def process_csv_resumes(self, csv_file_path: str = "data/initial/resume.csv"):
        """
        Reads resumes from a CSV file, selects up to 20 from each category,
        and processes them with progress tracking.
        The CSV should have 'ID', 'Resume_str', 'Category' columns.
        'Resume_html' is ignored.
        """
        print(f"\n=== Starting CSV processing from: {csv_file_path} ===")
        start_time = datetime.now()

        try:
            df = pd.read_csv(csv_file_path, dtype={
                             'Resume_str': str, 'Category': str, 'ID': str})
        except FileNotFoundError:
            print(f"Error: CSV file not found at {csv_file_path}")
            return
        except Exception as e:
            print(f"Error reading CSV file {csv_file_path}: {e}")
            return

        required_columns = ['ID', 'Resume_str', 'Category']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [
                col for col in required_columns if col not in df.columns]
            print(
                f"Error: CSV file must contain columns: {', '.join(required_columns)}. Missing: {', '.join(missing_cols)}")
            return

        # Clean and prepare data
        df.dropna(subset=['Resume_str', 'Category'], inplace=True)
        df = df[df['Resume_str'].str.strip() != '']
        df['Category'] = df['Category'].str.strip()

        # Select up to 20 resumes per category
        selected_resumes_df = df.groupby(
            'Category', as_index=False, group_keys=False).head(20)

        total_resumes = len(selected_resumes_df)
        print(
            f"Found {total_resumes} resumes to process from CSV after selection.")

        # Show category breakdown
        category_counts = selected_resumes_df['Category'].value_counts()
        print("\nCategory breakdown:")
        for category, count in category_counts.items():
            print(f"  {category}: {count} resumes")
        print()

        processed_count = 0
        failed_to_save_db_count = 0

        for index, row in selected_resumes_df.iterrows():
            resume_id = str(row['ID']).strip()
            extracted_text = str(row['Resume_str']).strip()
            category = str(row['Category']).strip()
            source_reference_filename = f"csv_import_{category}_{resume_id}.txt"

            if not extracted_text:
                print(
                    f"Skipping resume ID {resume_id} (Category: {category}) due to empty text.")
                failed_to_save_db_count += 1
                continue

            # Show progress
            progress = processed_count + failed_to_save_db_count + 1
            if self.show_progress:
                print(
                    f"[{progress}/{total_resumes}] Processing {category}/{resume_id}...", end='')
                sys.stdout.flush()

            # Clean the extracted text using our robust cleaning method
            cleaned_text = self._clean_text(
                extracted_text, f"csv_{category}_{resume_id}")

            # Save extracted text to file
            txt_filepath = self.save_extracted_text_to_file(
                cleaned_text, source_reference_filename)
            if not txt_filepath:
                print(" ✗ (failed to save text file)")
                failed_to_save_db_count += 1
                continue

            # Process and save to database
            db_id = self._process_common_resume_text(cleaned_text, source_reference_filename,
                                                     cv_path_for_db=None,  # Explicitly None for CSV
                                                     txt_path_for_db=txt_filepath,
                                                     category=category)
            if db_id is not None:
                processed_count += 1
                if self.show_progress:
                    print(" ✓")
            else:
                failed_to_save_db_count += 1
                if self.show_progress:
                    print(" ✗ (failed to save to database)")

        # Show completion statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n=== CSV Processing Complete ===")
        print(
            f"Total processed: {processed_count + failed_to_save_db_count} resumes")
        print(f"Successfully saved to DB: {processed_count} resumes")
        print(f"Failed to process: {failed_to_save_db_count} resumes")
        print(f"Time taken: {duration:.2f} seconds")
        if total_resumes > 0:
            print(f"Average: {duration/total_resumes:.2f} seconds per resume")
        print("=" * 32)

    def compute_cv_fields(self, cv_path: str) -> Dict[str, Any]:
        """Compute all CV fields on demand from stored CV file or extracted text with improved processing"""
        try:
            if self.show_progress:
                print(f"Computing CV fields for: {os.path.basename(cv_path)}")

            extracted_text = ""

            # Check if this is already an extracted text file
            if cv_path.endswith('_extracted.txt'):
                extracted_text = self._read_extracted_text_file(cv_path)
            else:
                # Try to find corresponding extracted text file
                base_name = os.path.basename(cv_path)
                # Remove the timestamp prefix and extension, then add _extracted.txt
                parts = base_name.split('_', 1)
                if len(parts) > 1:
                    original_part = parts[1]
                    # Remove extension
                    original_part = os.path.splitext(original_part)[0]
                    # Look for extracted text file
                    extracted_pattern = f"*_{original_part}_extracted.txt"
                    import glob
                    extracted_files = glob.glob(os.path.join(
                        self.txt_storage_path, extracted_pattern))
                    if extracted_files:
                        # Use the most recent one
                        extracted_files.sort()
                        extracted_text = self._read_extracted_text_file(
                            extracted_files[-1])

                # If no extracted text file found, extract from PDF directly
                if not extracted_text and cv_path.lower().endswith('.pdf'):
                    if self.show_progress:
                        print(f"Extracting text directly from PDF: {cv_path}")
                    extracted_text = self.extract_text_from_pdf(cv_path)

            if not extracted_text:
                if self.show_progress:
                    print(f"No text found for: {cv_path}")
                return {
                    'summary': '',
                    'skills': [],
                    'highlights': [],
                    'accomplishments': [],
                    'work_experience': [],
                    'education': [],
                    'extracted_text': ''
                }            # Use the comprehensive extract_all method
            result = self.extract_all(extracted_text)

            # Ensure extracted_text is included for backward compatibility
            result['extracted_text'] = extracted_text

            if self.show_progress:
                print(
                    f"Extracted {len(result['skills'])} skills, {len(result['work_experience'])} work experiences, {len(result['education'])} education entries")

            return result

        except Exception as e:
            error_msg = f"Error computing CV fields for {cv_path}: {e}"
            print(error_msg)
            self._save_debug("cv_fields_error.txt", error_msg,
                             os.path.basename(cv_path))
            return {
                'summary': '',
                'skills': [],
                'highlights': [],
                'accomplishments': [],
                'work_experience': [],
                'education': [],
                'extracted_text': ''
            }

    def _read_extracted_text_file(self, file_path: str) -> str:
        """Read extracted text from a stored text file with improved parsing"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Extract the actual CV text (after the header)
                if "END OF EXTRACTED TEXT" in content:
                    # Find the actual CV content between header and footer
                    lines = content.split('\n')
                    cv_start_idx = -1

                    # Skip the header section (===, title, source, date, ===)
                    for i, line in enumerate(lines):
                        if i > 4 and line.strip() and not line.startswith('='):
                            cv_start_idx = i
                            break

                    # Find where the footer starts
                    cv_end_idx = -1
                    for i, line in enumerate(lines):
                        if line.strip().startswith('=' * 50) and i > 10:  # Skip the header ===
                            cv_end_idx = i
                            break

                    if cv_start_idx != -1 and cv_end_idx != -1:
                        cv_content = '\n'.join(
                            lines[cv_start_idx:cv_end_idx]).strip()
                        # Apply additional cleaning if needed
                        if cv_content:
                            cv_content = self._clean_text(
                                cv_content, os.path.basename(file_path))
                        return cv_content

                # Fallback: return whole content minus obvious header/footer
                cleaned_content = self._clean_text(
                    content, os.path.basename(file_path))
                return cleaned_content

        except Exception as e:
            print(f"Error reading extracted text file {file_path}: {e}")
            self._save_debug("read_text_file_error.txt",
                             f"File: {file_path}\nError: {str(e)}",
                             os.path.basename(file_path))
            return ""

    def extract_all(self, text: str) -> Dict[str, Any]:
        """Extract all information from CV text using regex patterns"""
        try:
            # Save original text for debugging
            self._save_debug("original_text.txt", text,
                             f"extract_all_{datetime.now().strftime('%H%M%S')}")

            result = {
                'personal_info': self.extract_personal_info(text),
                'summary': self.extract_summary(text),
                'skills': self.extract_skills(text),
                'highlights': self.extract_highlights(text),
                'accomplishments': self.extract_accomplishments(text),
                'work_experience': self.extract_work_experience(text),
                'education': self.extract_education(text),
                'application_role': self.extract_application_role(text)
            }

            # Save final result
            import json
            self._save_debug("final_result.json", json.dumps(result, indent=2),
                             f"extract_all_{datetime.now().strftime('%H%M%S')}")

            return result

        except Exception as e:
            print(f"Error in extract_all: {e}")
            return {
                'personal_info': {},
                'summary': '',
                'skills': [],
                'highlights': [],
                'accomplishments': [],
                'work_experience': [],
                'education': [],
                'application_role': ''
            }
