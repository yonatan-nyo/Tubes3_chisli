import pdfplumber
import re
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil
import pandas as pd
from database.models.applicant import ApplicantProfile, ApplicantDetail
from database.models.database import SessionLocal


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
                for page in pdf.pages:                    # The .extract_text() method in pdfplumber is more advanced
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

    def extract_applicant_role(self, text: str) -> str:
        """Extract applicant role from CV text - first line is the applicant role"""
        if not text:
            return ""

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # The first line is the applicant role
        if lines:
            return lines[0]

        return ""

    def extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information from CV text - deprecated, keeping for compatibility"""
        # This method is now deprecated since we don't extract personal info from CV text anymore
        # The first line is the applicant role, not personal info
        return {}

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
                # Check if line contains multiple skills separated by common patterns
                # Split by multiple spaces (usually indicates separate items)
                if '  ' in line:  # Two or more spaces
                    parts = re.split(r'\s{2,}', line)
                    for part in parts:
                        part = part.strip()
                        if part:
                            skills.append(part)
                else:
                    skills.append(line)

        return skills

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
                        # Next line should be company + position
                        experience['end_date'] = parts[1].strip()
                if i + 1 < len(lines):
                    company_line = lines[i + 1]

                    # Split company line to get company and position
                    # Look for the specific separator pattern "ï¼​"
                    if 'ï¼​' in company_line:
                        parts = company_line.split('ï¼​', 1)
                        experience['company'] = parts[0].strip()
                        if len(parts) > 1:
                            # Everything after the separator contains location and position
                            remaining = parts[1].strip()
                            # Split by comma to separate location from position
                            location_position = remaining.split(',')
                            if len(location_position) >= 3:
                                # Usually format: "City , State Position"
                                # Take the last part after the state as position
                                position_part = location_position[-1].strip()
                                experience['position'] = position_part
                            else:
                                # If format is different, use the whole remaining part
                                experience['position'] = remaining
                    else:
                        # If no separator, treat whole line as company name
                        experience['company'] = company_line
                        experience['position'] = 'Not specified'

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
                    # Parse school line to separate institution and degree
                    school_line = lines[i + 1]
                    if 'ï¼​' in school_line:
                        parts = school_line.split('ï¼​', 1)
                        education['institution'] = parts[0].strip()
                        if len(parts) > 1:
                            # Look for degree info after location
                            remaining = parts[1].strip()
                            # Pattern: "City, State, Country Degree : Major"
                            if ':' in remaining:
                                degree_parts = remaining.split(':', 1)
                                if len(degree_parts) == 2:
                                    education['degree'] = degree_parts[1].strip()
                                    # Keep the part before : as additional info but extract degree
                                    location_degree = degree_parts[0].strip()
                                    # Try to extract degree from location_degree
                                    degree_words = location_degree.split()
                                    if degree_words:
                                        # Usually the degree is at the end before the colon
                                        potential_degree = ' '.join(
                                            degree_words[-2:]) if len(degree_words) >= 2 else degree_words[-1]
                                        # If nothing after colon
                                        if not education['degree']:
                                            education['degree'] = potential_degree
                            else:
                                # No colon, try to extract degree from the remaining part
                                location_parts = remaining.split(',')
                                if len(location_parts) >= 3:
                                    # Usually format: "City, State, Country DegreeType"
                                    education['degree'] = location_parts[-1].strip()
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
            txt_filepath = os.path.join(self.txt_storage_path, txt_filename).replace('\\', '/')
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
            stored_cv_path = os.path.join(self.cv_storage_path, stored_cv_filename).replace('\\', '/')
            shutil.copy2(file_path, stored_cv_path)
            txt_filepath = self.save_extracted_text_to_file(
                # Pass category as None for direct PDF processing, or derive if possible
                extracted_text, original_filename)
            return self._process_common_resume_text(extracted_text, original_filename,
                                                    cv_path_for_db=stored_cv_path,
                                                    txt_path_for_db=txt_filepath,
                                                    category=None,
                                                    applicant_id=applicant_id)
        except Exception as e:
            print(f"Error processing CV file {original_filename}: {e}")
            return None

    def _process_common_resume_text(self, extracted_text: str, source_reference: str,
                                    cv_path_for_db: Optional[str], txt_path_for_db: Optional[str],
                                    category: Optional[str] = None, applicant_id: Optional[int] = None) -> Optional[int]:
        """Common logic to process extracted text and save to DB using new schema."""
        # Extract applicant role from first line
        applicant_role = self.extract_applicant_role(extracted_text)

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
            'applicant_role': applicant_role,
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
            db.rollback()
            # Return a default ID (1) as fallback
            return 1
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

    def compute_cv_fields(self, cv_path: str) -> Dict[str, Any]:
        """Compute all CV fields on demand from stored CV file or extracted text"""

        try:
            # First try to read from corresponding extracted text file
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
                    extracted_text = self.extract_text_from_pdf(cv_path)

            if not extracted_text:
                return {
                    'summary': '',
                    'skills': [],
                    'highlights': [],
                    'accomplishments': [],
                    'work_experience': [],
                    'education': [],
                    'extracted_text': ''
                }

            # Compute all fields
            result = {
                'summary': self.extract_summary(extracted_text),
                'skills': self.extract_skills(extracted_text),
                'highlights': self.extract_highlights(extracted_text),
                'accomplishments': self.extract_accomplishments(extracted_text),
                'work_experience': self.extract_work_experience(extracted_text),
                'education': self.extract_education(extracted_text),
                'extracted_text': extracted_text
            }

            return result

        except Exception as e:
            print(f"Error computing CV fields for {cv_path}: {e}")
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
        """Read extracted text from a stored text file"""
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
                        return cv_content

                # Fallback: return whole content minus obvious header/footer
                return content

        except Exception as e:
            print(f"Error reading extracted text file {file_path}: {e}")
            return ""
