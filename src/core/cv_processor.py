import pdfplumber
import re
import os
from typing import Dict, List, Optional
from datetime import datetime
import shutil
import pandas as pd # Added for CSV processing
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
                    page_text = page.extract_text(x_tolerance=2) # Adjust tolerance to merge nearby words
                    if page_text:
                        full_text.append(page_text)
                return "\n".join(full_text)
        except Exception as e:
            print(f"Error extracting text with pdfplumber from {file_path}: {e}")
            return ""

    def extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information using regex"""
        info = {'name': '', 'email': '', 'phone': ''}
        if not text: return info

        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match: info['email'] = email_match.group()

        phone_patterns = [
            r'\+?(\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?(\d{1,3}[-.\s]?)?\d{10,14}',
            r'\(\d{3}\)\s?\d{3}-?\d{4}'
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                info['phone'] = phone_match.group()
                break

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            info['name'] = lines[0]
            if len(lines[0]) > 50 or any(word in lines[0].lower() for word in ['curriculum', 'cv', 'resume', 'vitae', 'biodata']):
                for line_content in lines[1:5]:
                    if line_content and not any(char in line_content for char in ['@', '+', '(', ')', '.com', 'www.']) and len(line_content) < 50 and not re.match(r'^\s*(summary|objective|profile|experience|education|skills)', line_content, re.I):
                        potential_name = True
                        if line_content.isupper() and len(line_content) > 15: potential_name = False
                        if len(line_content.split()) > 4 or re.search(r'\d', line_content): potential_name = False
                        if potential_name:
                            info['name'] = line_content
                            break
                else:
                    if info['name'] == lines[0] and (len(lines[0]) > 50 or any(word in lines[0].lower() for word in ['curriculum', 'cv', 'resume', 'vitae', 'biodata'])):
                        info['name'] = ''
        return info

    def extract_summary(self, text: str) -> str:
        """Extract summary/overview section"""
        if not text: return ""
        summary_patterns = [
            r'(?i)(?:summary|overview|profile|objective|about me|professional summary|career objective|personal statement)[:\s]*\n?(.*?)(?=\n\s*(?:[A-Z][^a-z\s]*\s*){1,3}:|\Z)',
        ]
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                summary_text = match.group(1).strip()
                summary_lines = summary_text.split('\n')
                cleaned_summary_lines = []
                for line in summary_lines:
                    if re.match(r'^\s*(?:[A-Z][^a-z\s]*\s*){1,3}:', line): break
                    cleaned_summary_lines.append(line)
                return "\n".join(cleaned_summary_lines).strip()
        return ""

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills section"""
        if not text: return []
        skills_section_text = ""
        skills_patterns = [
            r'(?i)(?:skills?|technical skills|core competencies|expertise|programming languages?|technologies)[:\s]*\n?(.*?)(?=\n\s*(?:[A-Z][^a-z\s]*\s*){1,3}:|\Z)'
        ]
        for pattern in skills_patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                skills_section_text = match.group(1).strip()
                break
        skills = []
        if skills_section_text:
            skill_items = re.split(r'[\n,;•*]+', skills_section_text)
            for item in skill_items:
                clean_skill = re.sub(r'^\s*-\s*', '', item.strip())
                if clean_skill and 1 < len(clean_skill) < 50:
                    skills.append(clean_skill)
        return list(set(skills))

    def extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience information"""
        if not text: return []
        experiences = []
        exp_text_section = ""
        exp_patterns = [
             r'(?i)(?:work experience|professional experience|employment history|career history|experience)[:\s]*\n?(.*?)(?=\n\s*(?:[A-Z][^a-z\s]*\s*){1,3}:|\Z)'
        ]
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                exp_text_section = match.group(1).strip()
                break
        if exp_text_section:
            job_entries_text = re.split(r'\n(?=\s*[A-Z0-9])', exp_text_section)
            for entry_text in job_entries_text:
                entry_text = entry_text.strip()
                if len(entry_text) > 10:
                    parsed_experience = self._parse_job_entry(entry_text)
                    if parsed_experience and parsed_experience.get('position'):
                        experiences.append(parsed_experience)
        return experiences

    def _parse_job_entry(self, entry_text: str) -> Optional[Dict[str, str]]:
        """Parse individual job entry text"""
        lines = [line.strip() for line in entry_text.split('\n') if line.strip()]
        if not lines: return None
        experience = {'position': '', 'company': '', 'start_date': '', 'end_date': '', 'description': ''}
        date_range_pattern = r'(?i)((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)\s*\d{4}|(?:\d{1,2}/\d{4}))\s*(?:to|-|–)\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)\s*\d{4}|(?:\d{1,2}/\d{4})|Present|Current)'
        date_match = re.search(date_range_pattern, entry_text)
        date_lines_indices = []
        if date_match:
            experience['start_date'] = date_match.group(1).strip()
            experience['end_date'] = date_match.group(2).strip()
            for i, line in enumerate(lines):
                if date_match.group(0) in line:
                    lines[i] = line.replace(date_match.group(0), "").strip()
                    date_lines_indices.append(i)
        remaining_lines = [lines[i] for i in range(len(lines)) if i not in date_lines_indices and lines[i]]
        if remaining_lines:
            experience['position'] = remaining_lines[0]
            if len(remaining_lines) > 1 and not any(s in remaining_lines[1].lower() for s in ["responsibilities:", "key achievements:"]):
                if len(remaining_lines[1].split()) < 5:
                    experience['company'] = remaining_lines[1]
                    experience['description'] = "\n".join(remaining_lines[2:]).strip()
                else:
                    experience['description'] = "\n".join(remaining_lines[1:]).strip()
            else:
                experience['description'] = "\n".join(remaining_lines[1:]).strip()
        return experience

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information"""
        if not text: return []
        education_list = []
        edu_text_section = ""
        edu_patterns = [
            r'(?i)(?:education|academic background|qualifications|academic qualifications)[:\s]*\n?(.*?)(?=\n\s*(?:[A-Z][^a-z\s]*\s*){1,3}:|\Z)'
        ]
        for pattern in edu_patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                edu_text_section = match.group(1).strip()
                break
        if edu_text_section:
            edu_entries_text = re.split(r'\n(?=\s*[A-Z0-9])', edu_text_section)
            for entry_text in edu_entries_text:
                entry_text = entry_text.strip()
                if len(entry_text) > 5:
                    parsed_edu = self._parse_education_entry(entry_text)
                    if parsed_edu and parsed_edu.get('degree') and parsed_edu.get('institution'):
                        education_list.append(parsed_edu)
        return education_list

    def _parse_education_entry(self, entry_text: str) -> Optional[Dict[str, str]]:
        """Parse individual education entry text"""
        lines = [line.strip() for line in entry_text.split('\n') if line.strip()]
        if not lines: return None
        education_item = {'degree': '', 'institution': '', 'graduation_year': '', 'gpa': ''}
        year_pattern = r'\b(19[89]\d|20\d{2})\b'
        years_found = re.findall(year_pattern, entry_text)
        if years_found: education_item['graduation_year'] = years_found[-1]
        gpa_pattern = r'(?i)(?:GPA|CGPA)[:\s]*([\d\.]+)(?:\s*/\s*[\d\.]+)?'
        gpa_match = re.search(gpa_pattern, entry_text)
        if gpa_match: education_item['gpa'] = gpa_match.group(1)
        if lines:
            education_item['degree'] = lines[0]
            if len(lines) > 1:
                if not gpa_match or (gpa_match and gpa_match.group(0) not in lines[1]):
                    if len(lines[1].split(',')) < 3 and len(lines[1].split(' and ')) < 3:
                         education_item['institution'] = lines[1]
        if education_item['institution'] in education_item['degree'] and education_item['institution']:
            education_item['degree'] = education_item['degree'].replace(education_item['institution'], '').strip(' ,-')
        if not education_item['degree'] and education_item['institution']:
            education_item['degree'] = education_item['institution']
            education_item['institution'] = ''
        return education_item

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
                txt_file.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                txt_file.write("=" * 50 + "\n\n")
                txt_file.write(extracted_text if extracted_text else "No text extracted or content was empty.")
                txt_file.write("\n\n" + "=" * 50 + "\nEND OF EXTRACTED TEXT\n" + "=" * 50)
            return txt_filepath
        except Exception as e:
            print(f"Error saving extracted text to file for {original_cv_filename}: {e}")
            return ""

    def process_cv_file(self, file_path: str, original_filename: str) -> Optional[int]:
        """Process uploaded CV file (PDF) and save to database"""
        try:
            extracted_text = self.extract_text_from_pdf(file_path)
            if not extracted_text:
                print(f"No text extracted from PDF: {original_filename}. Skipping.")
                return None
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_original_filename = re.sub(r'[^\w\.-]', '_', original_filename)
            stored_cv_filename = f"{timestamp}_{safe_original_filename}"
            stored_cv_path = os.path.join(self.cv_storage_path, stored_cv_filename)
            shutil.copy2(file_path, stored_cv_path)
            txt_filepath = self.save_extracted_text_to_file(extracted_text, original_filename)
            # Pass category as None for direct PDF processing, or derive if possible
            return self._process_common_resume_text(extracted_text, original_filename, 
                                                    cv_path_for_db=stored_cv_path, 
                                                    txt_path_for_db=txt_filepath,
                                                    category=None) # Or determine category if available
        except Exception as e:
            print(f"Error processing CV file {original_filename}: {e}")
            return None

    def _process_common_resume_text(self, extracted_text: str, source_reference: str,
                                   cv_path_for_db: Optional[str], txt_path_for_db: Optional[str],
                                   category: Optional[str] = None) -> Optional[int]:
        """Common logic to process extracted text and save to DB."""
        personal_info = self.extract_personal_info(extracted_text)
        summary = self.extract_summary(extracted_text)
        skills = self.extract_skills(extracted_text)
        work_experience = self.extract_work_experience(extracted_text)
        education = self.extract_education(extracted_text)

        applicant_name = personal_info.get('name')
        if not applicant_name or applicant_name.isspace():
            match_id = re.search(r'_([^_]+)\.(txt|pdf)$', source_reference, re.I)
            placeholder_id = match_id.group(1) if match_id else "UnknownID"
            applicant_name = f"Applicant {placeholder_id}"
            if category: # Add category to placeholder name if available and name is missing
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
            'email': personal_info.get('email'), # .get() handles missing keys, returns None
            'phone': personal_info.get('phone'),
            'cv_file_path': final_cv_path_for_db,
            'txt_file_path': final_txt_path_for_db,
            'extracted_text': extracted_text,
            'summary': summary,
            'skills': skills,
            'work_experience': work_experience,
            'education': education
            # The 'category' is not directly in the Applicant model provided.
            # If you add a 'category' column to your Applicant model, you can pass it here:
            # 'category': category,
        }

        db = SessionLocal()
        try:
            # Applicant.from_dict will handle JSON conversion for complex fields
            applicant = Applicant.from_dict(applicant_data)
            db.add(applicant)
            db.commit()
            db.refresh(applicant)
            print(f"Successfully processed and saved: {source_reference}. DB ID: {applicant.id}")
            return applicant.id
        except Exception as e:
            db.rollback()
            print(f"Error saving to database for {source_reference}: {e}. Data: {applicant_data}")
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
            df = pd.read_csv(csv_file_path, dtype={'Resume_str': str, 'Category': str, 'ID': str})
        except FileNotFoundError:
            print(f"Error: CSV file not found at {csv_file_path}")
            return
        except Exception as e:
            print(f"Error reading CSV file {csv_file_path}: {e}")
            return

        required_columns = ['ID', 'Resume_str', 'Category']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            print(f"Error: CSV file must contain columns: {', '.join(required_columns)}. Missing: {', '.join(missing_cols)}")
            return

        df.dropna(subset=['Resume_str', 'Category'], inplace=True)
        df = df[df['Resume_str'].str.strip() != '']
        df['Category'] = df['Category'].str.strip() # Ensure category names are clean

        selected_resumes_df = df.groupby('Category', as_index=False, group_keys=False).head(20)
        print(f"Found {len(selected_resumes_df)} resumes to process from CSV after selection.")

        processed_count = 0
        failed_to_save_db_count = 0

        for index, row in selected_resumes_df.iterrows():
            resume_id = str(row['ID']).strip()
            extracted_text = str(row['Resume_str']).strip()
            category = str(row['Category']).strip()
            source_reference_filename = f"csv_import_{category}_{resume_id}.txt"

            if not extracted_text:
                print(f"Skipping resume ID {resume_id} (Category: {category}) due to empty Resume_str content.")
                continue

            print(f"\nProcessing from CSV - ID: {resume_id}, Category: {category}")
            txt_filepath = self.save_extracted_text_to_file(extracted_text, source_reference_filename)
            if not txt_filepath:
                print(f"Failed to save extracted text for CSV resume ID {resume_id}. Skipping.")
                failed_to_save_db_count +=1
                continue

            db_id = self._process_common_resume_text(extracted_text, source_reference_filename,
                                                   cv_path_for_db=None, # Explicitly None for CSV
                                                   txt_path_for_db=txt_filepath,
                                                   category=category)
            if db_id is not None:
                processed_count += 1
            else:
                failed_to_save_db_count += 1
        
        print(f"\nCSV Processing Complete.")
        print(f"Successfully processed and saved to DB: {processed_count} resumes.")
        print(f"Failed to save to DB (or save text file): {failed_to_save_db_count} resumes.")