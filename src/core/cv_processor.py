import pdfplumber
import re
import os
from typing import Dict, List, Optional
from datetime import datetime
import shutil
import pandas as pd  # Added for CSV processing
# Assuming your database.py defines SessionLocal and Base,
# and your Applicant model is in a file from which it can be imported.
# If Applicant model is in, say, models.py, it would be:
# from .models import Applicant
# from .database import SessionLocal
# For now, assuming direct import as per previous context:
from database import SessionLocal, Applicant


class CVProcessor:
    """Process CV files and extract information"""

    def __init__(self):
        self.cv_storage_path = "data/cv_files"
        self.txt_storage_path = "data/extracted_text"
        self._ensure_storage_directories()

    def _ensure_storage_directories(self):
        """Ensure CV and text storage directories exist"""
        if not os.path.exists(self.cv_storage_path):
            os.makedirs(self.cv_storage_path)
        if not os.path.exists(self.txt_storage_path):
            os.makedirs(self.txt_storage_path)

    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            with pdfplumber.open(file_path) as pdf:
                full_text = []
                for page in pdf.pages:
                    # The .extract_text() method in pdfplumber is more advanced
                    # and attempts to reconstruct the reading order.
                    # Adjust tolerance to merge nearby words
                    page_text = page.extract_text(x_tolerance=2)
                    if page_text:
                        full_text.append(page_text)
                return "\n".join(full_text)
        except Exception as e:
            print(
                f"Error extracting text with pdfplumber from {file_path}: {e}")
            return ""

    def extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information from CV text - first line after headers is the applicant name"""
        info = {'name': '', 'email': '', 'phone': ''}
        if not text:
            return info

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Skip header lines and find the first content line (which is the name)
        name = ""
        header_ended = False

        for line in lines:
            # Skip header lines
            if "====" in line:
                header_ended = True
                continue

            if any(header in line for header in ["EXTRACTED TEXT FROM CV", "Source Reference:", "Extraction Date:"]):
                continue

            # First line after headers is the name
            if header_ended and line and not name:
                name = line
                break

        # Extract email and phone using regex from full text
        full_text = ' '.join(lines)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4})'

        email_match = re.search(email_pattern, full_text)
        phone_match = re.search(phone_pattern, full_text)

        if email_match:
            info['email'] = email_match.group()
        if phone_match:
            info['phone'] = phone_match.group()

        info['name'] = name
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

        for line in lines:
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
        """Extract summary section"""
        return self._extract_section_content(text, 'Summary')

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills section"""
        content = self._extract_section_content(text, 'Skills')
        if not content:
            return []

        # Split by lines and clean up
        skills = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                skills.append(line)

        return skills

    def extract_highlights(self, text: str) -> List[str]:
        """Extract highlights section"""
        content = self._extract_section_content(text, 'Highlights')
        if not content:
            return []

        # Split by lines and clean up
        highlights = []
        for line in content.split('\n'):
            line = line.strip()
            if line:
                highlights.append(line)

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
                accomplishments.append(line)

        return accomplishments

    def extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience: 1st line = date, 2nd line = company + job title, rest = description until next date"""
        content = self._extract_section_content(text, 'Experience')
        if not content:
            return []

        lines = [line.strip() for line in content.split('\n') if line.strip()]
        experiences = []

        # Simple date pattern - looking for dates at the start of lines
        date_pattern = r'^\d{2}/\d{4}\s*[-–]\s*\d{2}/\d{4}$|^\d{2}/\d{4}\s*[-–]\s*(?:Present|Current)$|^\d{4}\s*[-–]\s*\d{4}$'

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this line is a date
            if re.match(date_pattern, line, re.IGNORECASE):
                experience = {
                    'start_date': '',
                    'end_date': '',
                    'company': '',
                    'position': '',
                    'description': ''
                }

                # Parse the date
                if ' - ' in line or ' – ' in line:
                    parts = re.split(r'\s*[-–]\s*', line)
                    if len(parts) == 2:
                        experience['start_date'] = parts[0].strip()
                        experience['end_date'] = parts[1].strip()

                # Next line should be company + position
                if i + 1 < len(lines):
                    company_line = lines[i + 1]

                    # Split company line to get company and position
                    # Look for common separators
                    if ' ï¼​ ' in company_line:
                        parts = company_line.split(' ï¼​ ', 1)
                        experience['company'] = parts[0].strip()
                        if len(parts) > 1:
                            # Everything after the separator is position/location
                            remaining = parts[1].strip()
                            # Try to extract position from the end (usually the last part)
                            words = remaining.split()
                            if len(words) >= 2:
                                # Last 1-3 words are likely the position
                                position_words = words[-2:] if len(
                                    words) >= 2 else words[-1:]
                                experience['position'] = ' '.join(
                                    position_words)
                    else:
                        # If no separator, treat as company
                        experience['company'] = company_line

                    i += 2  # Move past date and company lines

                    # Collect description until next date
                    description_lines = []
                    while i < len(lines):
                        next_line = lines[i]

                        # Check if this is the start of next experience (date line)
                        if re.match(date_pattern, next_line, re.IGNORECASE):
                            break

                        description_lines.append(next_line)
                        i += 1

                    experience['description'] = '\n'.join(
                        description_lines).strip()

                    # Add if we have minimum required info
                    if experience['start_date'] and experience['company']:
                        experiences.append(experience)
                else:
                    i += 1
            else:
                i += 1

        return experiences

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education: 1st line = year, 2nd line = school + major, rest = description until next year"""
        content = self._extract_section_content(text, 'Education')
        if not content:
            return []

        lines = [line.strip() for line in content.split('\n') if line.strip()]
        education_list = []

        # Simple year pattern - 4 digit year at start of line
        year_pattern = r'^(19[5-9]\d|20[0-9]\d)$'

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this line is just a year
            if re.match(year_pattern, line):
                education = {
                    'graduation_year': line,
                    'institution': '',
                    'degree': '',
                    'gpa': '',
                    'description': ''
                }

                # Next line should be school + major
                if i + 1 < len(lines):
                    school_line = lines[i + 1]

                    # Parse school line to separate institution and degree
                    if ' ï¼​ ' in school_line:
                        parts = school_line.split(' ï¼​ ', 1)
                        education['institution'] = parts[0].strip()
                        if len(parts) > 1:
                            # Look for degree info after location
                            remaining = parts[1].strip()
                            # Pattern: "City, State, Country Degree : Major"
                            if ':' in remaining:
                                degree_parts = remaining.split(':', 1)
                                if len(degree_parts) == 2:
                                    education['degree'] = degree_parts[1].strip()
                    else:
                        # If no separator, treat as institution
                        education['institution'] = school_line

                    i += 2  # Move past year and school lines

                    # Collect description until next year
                    description_lines = []
                    while i < len(lines):
                        next_line = lines[i]

                        # Check if this is the start of next education (year line)
                        if re.match(year_pattern, next_line):
                            break

                        # Check for GPA in this line
                        gpa_match = re.search(
                            r'(?i)(?:GPA|CGPA)[:\s]*([\d\.]+)', next_line)
                        if gpa_match:
                            education['gpa'] = gpa_match.group(1)
                            # Remove GPA from line and add rest to description
                            line_without_gpa = re.sub(
                                r'(?i)(?:GPA|CGPA)[:\s]*[\d\.]+(?:\s*/\s*[\d\.]+)?', '', next_line).strip()
                            if line_without_gpa:
                                description_lines.append(line_without_gpa)
                        else:
                            description_lines.append(next_line)

                        i += 1

                    education['description'] = '\n'.join(
                        description_lines).strip()

                    # Add if we have minimum required info
                    if education['graduation_year'] and (education['institution'] or education['degree']):
                        education_list.append(education)
                else:
                    i += 1
            else:
                i += 1

        return education_list

    def save_extracted_text_to_file(self, extracted_text: str, original_cv_filename: str) -> str:
        """Save extracted text to a TXT file, using original CV filename for naming."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(original_cv_filename)[0]
            safe_base_name = re.sub(r'[^\w\.-]', '_', base_name)
            txt_filename = f"{timestamp}_{safe_base_name}_extracted.txt"
            txt_filepath = os.path.join(self.txt_storage_path, txt_filename)
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

    def process_cv_file(self, file_path: str, original_filename: str) -> Optional[int]:
        """Process uploaded CV file (PDF) and save to database"""
        try:
            extracted_text = self.extract_text_from_pdf(file_path)
            if not extracted_text:
                print(
                    f"No text extracted from PDF: {original_filename}. Skipping.")
                return None
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_original_filename = re.sub(
                r'[^\w\.-]', '_', original_filename)
            stored_cv_filename = f"{timestamp}_{safe_original_filename}"
            stored_cv_path = os.path.join(
                self.cv_storage_path, stored_cv_filename)
            shutil.copy2(file_path, stored_cv_path)
            txt_filepath = self.save_extracted_text_to_file(
                # Pass category as None for direct PDF processing, or derive if possible
                extracted_text, original_filename)
            return self._process_common_resume_text(extracted_text, original_filename,
                                                    cv_path_for_db=stored_cv_path,
                                                    txt_path_for_db=txt_filepath,
                                                    category=None)  # Or determine category if available
        except Exception as e:
            print(f"Error processing CV file {original_filename}: {e}")
            return None

    def _process_common_resume_text(self, extracted_text: str, source_reference: str,
                                    cv_path_for_db: Optional[str], txt_path_for_db: Optional[str],
                                    category: Optional[str] = None) -> Optional[int]:
        """Common logic to process extracted text and save to DB."""
        print(f"\n=== DEBUG: Processing CV - {source_reference} ===")

        personal_info = self.extract_personal_info(extracted_text)
        print(f"Personal Info extracted: {personal_info}")

        summary = self.extract_summary(extracted_text)
        print(
            f"Summary extracted: {summary[:100] + '...' if summary and len(summary) > 100 else summary}")

        skills = self.extract_skills(extracted_text)
        print(f"Skills extracted ({len(skills)} items): {skills}")

        highlights = self.extract_highlights(extracted_text)
        print(f"Highlights extracted ({len(highlights)} items): {highlights}")

        accomplishments = self.extract_accomplishments(extracted_text)
        print(
            f"Accomplishments extracted ({len(accomplishments)} items): {accomplishments}")

        work_experience = self.extract_work_experience(extracted_text)
        print(f"Work Experience extracted ({len(work_experience)} items):")
        for i, exp in enumerate(work_experience):
            print(f"  Experience {i+1}: {exp}")

        education = self.extract_education(extracted_text)
        print(f"Education extracted ({len(education)} items):")
        for i, edu in enumerate(education):
            print(f"  Education {i+1}: {edu}")

        print("=== END DEBUG OUTPUT ===\n")

        applicant_name = personal_info.get('name')
        if not applicant_name or applicant_name.isspace():
            match_id = re.search(
                r'_([^_]+)\.(txt|pdf)$', source_reference, re.I)
            placeholder_id = match_id.group(1) if match_id else "UnknownID"
            applicant_name = f"Applicant {placeholder_id}"
            if category:  # Add category to placeholder name if available and name is missing
                applicant_name += f" ({category})"

        # Ensure cv_file_path is never None to satisfy nullable=False constraint
        final_cv_path_for_db = cv_path_for_db
        if final_cv_path_for_db is None:
            if txt_path_for_db:
                final_cv_path_for_db = txt_path_for_db  # Use txt_file_path as a substitute
            else:
                # This is a last resort, should ideally not be hit if txt_file always saves
                final_cv_path_for_db = f"MISSING_FILE_PATH_FOR_{source_reference.replace('.', '_')}"

        # Ensure txt_file_path is also not None if DB expects it (model shows nullable=True, so None is okay)
        final_txt_path_for_db = txt_path_for_db
        if final_txt_path_for_db is None and final_cv_path_for_db is not None and ".txt" in final_cv_path_for_db:
            # If cv_path ended up being the txt_path, txt_path can be the same.
            final_txt_path_for_db = final_cv_path_for_db
        elif final_txt_path_for_db is None:
            final_txt_path_for_db = f"MISSING_TXT_PATH_FOR_{source_reference.replace('.', '_')}"

        applicant_data = {
            'name': applicant_name,
            # .get() handles missing keys, returns None
            'email': personal_info.get('email'),
            'phone': personal_info.get('phone'),
            'cv_file_path': final_cv_path_for_db,
            'txt_file_path': final_txt_path_for_db,
            'extracted_text': extracted_text,
            'summary': summary,
            'skills': skills,
            'highlights': highlights,
            'accomplishments': accomplishments,
            'work_experience': work_experience,
            'education': education
            # The 'category' is not directly in the Applicant model provided.
            # If you add a 'category' column to your Applicant model, you can pass it here:
            # 'category': category,
        }

        print(f"DEBUG: Final applicant data structure:")
        print(f"  - Name: {applicant_data['name']}")
        print(f"  - Email: {applicant_data['email']}")
        print(f"  - Phone: {applicant_data['phone']}")
        print(f"  - Skills count: {len(applicant_data['skills'])}")
        print(f"  - Highlights count: {len(applicant_data['highlights'])}")
        print(
            f"  - Accomplishments count: {len(applicant_data['accomplishments'])}")
        print(
            f"  - Work experience count: {len(applicant_data['work_experience'])}")
        print(f"  - Education count: {len(applicant_data['education'])}")
        print(
            f"  - Summary length: {len(applicant_data['summary']) if applicant_data['summary'] else 0}")
        print("DEBUG: Attempting to save to database...")

        db = SessionLocal()
        try:
            # Applicant.from_dict will handle JSON conversion for complex fields
            applicant = Applicant.from_dict(applicant_data)
            db.add(applicant)
            db.commit()
            db.refresh(applicant)
            print(
                f"Successfully processed and saved: {source_reference}. DB ID: {applicant.id}")
            return applicant.id
        except Exception as e:
            db.rollback()
            print(
                f"Error saving to database for {source_reference}: {e}. Data: {applicant_data}")
            return None
        finally:
            db.close()

    def process_csv_resumes(self, csv_file_path: str = "data/initial/resume.csv"):
        """
        Reads resumes from a CSV file, selects up to 20 from each category,
        and processes them.
        The CSV should have 'ID', 'Resume_str', 'Category' columns.
        'Resume_html' is ignored.
        """
        print(f"Starting CSV processing from: {csv_file_path}")
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

        df.dropna(subset=['Resume_str', 'Category'], inplace=True)
        df = df[df['Resume_str'].str.strip() != '']
        # Ensure category names are clean
        df['Category'] = df['Category'].str.strip()

        selected_resumes_df = df.groupby(
            'Category', as_index=False, group_keys=False).head(20)
        print(
            f"Found {len(selected_resumes_df)} resumes to process from CSV after selection.")

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
                continue

            print(
                f"\nProcessing from CSV - ID: {resume_id}, Category: {category}")
            txt_filepath = self.save_extracted_text_to_file(
                extracted_text, source_reference_filename)
            if not txt_filepath:
                print(
                    f"Failed to save extracted text for CSV resume ID {resume_id}. Skipping.")
                failed_to_save_db_count += 1
                continue

            db_id = self._process_common_resume_text(extracted_text, source_reference_filename,
                                                     cv_path_for_db=None,  # Explicitly None for CSV
                                                     txt_path_for_db=txt_filepath,
                                                     category=category)
            if db_id is not None:
                processed_count += 1
            else:
                failed_to_save_db_count += 1

        print(f"\nCSV Processing Complete.")
        print(
            f"Successfully processed and saved to DB: {processed_count} resumes.")
        print(
            f"Failed to save to DB (or save text file): {failed_to_save_db_count} resumes.")
