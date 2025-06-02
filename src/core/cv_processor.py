import pypdf
import re
import os
from typing import Dict, List, Optional
from datetime import datetime
import shutil
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
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information using regex"""
        info = {
            'name': '',
            'email': '',
            'phone': ''
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            info['email'] = email_match.group()
        
        # Extract phone number
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
        
        # Extract name (first non-empty line or line before email/contact)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Simple heuristic: first line is often the name
            info['name'] = lines[0]
            
            # If first line looks like a header/title, try next lines
            if any(word in lines[0].lower() for word in ['curriculum', 'cv', 'resume']):
                for line in lines[1:5]:  # Check next few lines
                    if line and not any(char in line for char in ['@', '+', '(', ')']):
                        info['name'] = line
                        break
        
        return info
    
    def extract_summary(self, text: str) -> str:
        """Extract summary/overview section"""
        summary_patterns = [
            r'(?i)(?:summary|overview|profile|objective|about me)[:\s]*\n(.*?)(?=\n\s*[A-Z][^a-z]*:|\n\s*$)',
            r'(?i)(?:professional summary|career objective)[:\s]*\n(.*?)(?=\n\s*[A-Z][^a-z]*:|\n\s*$)',
            r'(?i)(?:personal statement)[:\s]*\n(.*?)(?=\n\s*[A-Z][^a-z]*:|\n\s*$)'
        ]
        
        for pattern in summary_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills section"""
        skills = []
        
        # Find skills section
        skills_patterns = [
            r'(?i)(?:skills?|technical skills|core competencies|expertise)[:\s]*\n(.*?)(?=\n\s*[A-Z][^a-z]*:|\n\s*$)',
            r'(?i)(?:programming languages?|technologies)[:\s]*\n(.*?)(?=\n\s*[A-Z][^a-z]*:|\n\s*$)'
        ]
        
        skills_text = ""
        for pattern in skills_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                skills_text = match.group(1)
                break
        
        if skills_text:
            # Extract individual skills
            # Split by common delimiters
            skill_items = re.split(r'[,;•\n\t]', skills_text)
            
            for item in skill_items:
                item = item.strip()
                if item and len(item) < 50:  # Reasonable skill name length
                    # Remove bullet points and formatting
                    clean_skill = re.sub(r'^[-•*\s]+', '', item)
                    if clean_skill:
                        skills.append(clean_skill)
        
        return skills
    
    def extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience information"""
        experiences = []
        
        # Find work experience section
        exp_patterns = [
            r'(?i)(?:work experience|professional experience|employment history|career history)[:\s]*\n(.*?)(?=\n\s*[A-Z][^a-z]*:|\n\s*$)',
            r'(?i)(?:experience)[:\s]*\n(.*?)(?=\n\s*[A-Z][^a-z]*:|\n\s*$)'
        ]
        
        exp_text = ""
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                exp_text = match.group(1)
                break
        
        if exp_text:
            # Extract job entries
            job_entries = re.split(r'\n(?=[A-Z])', exp_text)
            
            for entry in job_entries:
                if len(entry.strip()) > 10:  # Minimum content
                    experience = self._parse_job_entry(entry)
                    if experience:
                        experiences.append(experience)
        
        return experiences
    
    def _parse_job_entry(self, entry: str) -> Optional[Dict[str, str]]:
        """Parse individual job entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None
        
        # Extract dates
        date_pattern = r'(\d{4}|\d{1,2}/\d{4}|\w+ \d{4})'
        dates = re.findall(date_pattern, entry)
        
        # First line often contains position and company
        position_line = lines[0]
        
        experience = {
            'position': position_line,
            'company': '',
            'start_date': dates[0] if dates else '',
            'end_date': dates[1] if len(dates) > 1 else 'Present',
            'description': '\n'.join(lines[1:]) if len(lines) > 1 else ''
        }
        
        return experience
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information"""
        education = []
        
        # Find education section
        edu_patterns = [
            r'(?i)(?:education|academic background|qualifications)[:\s]*\n(.*?)(?=\n\s*[A-Z][^a-z]*:|\n\s*$)',
            r'(?i)(?:academic qualifications)[:\s]*\n(.*?)(?=\n\s*[A-Z][^a-z]*:|\n\s*$)'
        ]
        
        edu_text = ""
        for pattern in edu_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                edu_text = match.group(1)
                break
        
        if edu_text:
            # Extract education entries
            edu_entries = re.split(r'\n(?=[A-Z])', edu_text)
            
            for entry in edu_entries:
                if len(entry.strip()) > 5:
                    edu_item = self._parse_education_entry(entry)
                    if edu_item:
                        education.append(edu_item)
        
        return education
    
    def _parse_education_entry(self, entry: str) -> Optional[Dict[str, str]]:
        """Parse individual education entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None
        
        # Extract graduation year
        year_pattern = r'(\d{4})'
        years = re.findall(year_pattern, entry)
        
        # Extract degree and institution
        degree_line = lines[0]
        
        education_item = {
            'degree': degree_line,
            'institution': lines[1] if len(lines) > 1 else '',
            'graduation_year': years[-1] if years else '',
            'gpa': ''
        }
        
        # Look for GPA
        gpa_pattern = r'gpa[:\s]*(\d+\.?\d*)'
        gpa_match = re.search(gpa_pattern, entry, re.IGNORECASE)
        if gpa_match:
            education_item['gpa'] = gpa_match.group(1)
        
        return education_item
    
    def save_extracted_text_to_file(self, extracted_text: str, filename: str) -> str:
        """Save extracted text to a TXT file"""
        try:
            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(filename)[0]
            txt_filename = f"{timestamp}_{base_name}_extracted.txt"
            txt_filepath = os.path.join(self.txt_storage_path, txt_filename)
            
            # Write extracted text to file
            with open(txt_filepath, 'w', encoding='utf-8') as txt_file:
                txt_file.write("=" * 50 + "\n")
                txt_file.write("EXTRACTED TEXT FROM CV\n")
                txt_file.write(f"Original PDF: {filename}\n")
                txt_file.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                txt_file.write("=" * 50 + "\n\n")
                txt_file.write(extracted_text)
                txt_file.write("\n\n" + "=" * 50 + "\n")
                txt_file.write("END OF EXTRACTED TEXT\n")
                txt_file.write("=" * 50)
            
            return txt_filepath
        except Exception as e:
            print(f"Error saving extracted text to file: {e}")
            return ""
    
    def process_cv_file(self, file_path: str, original_filename: str) -> Optional[int]:
        """Process uploaded CV file and save to database"""
        try:
            # Extract text from PDF
            extracted_text = self.extract_text_from_pdf(file_path)
            if not extracted_text:
                return None
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            stored_filename = f"{timestamp}_{original_filename}"
            stored_path = os.path.join(self.cv_storage_path, stored_filename)
            
            # Copy file to storage
            shutil.copy2(file_path, stored_path)
            
            # Save extracted text as TXT file
            txt_filepath = self.save_extracted_text_to_file(extracted_text, original_filename)
            
            # Extract information
            personal_info = self.extract_personal_info(extracted_text)
            summary = self.extract_summary(extracted_text)
            skills = self.extract_skills(extracted_text)
            work_experience = self.extract_work_experience(extracted_text)
            education = self.extract_education(extracted_text)
            
            # Prepare data for database
            applicant_data = {
                'name': personal_info['name'],
                'email': personal_info['email'],
                'phone': personal_info['phone'],
                'cv_file_path': stored_path,
                'txt_file_path': txt_filepath,
                'extracted_text': extracted_text,
                'summary': summary,
                'skills': skills,
                'work_experience': work_experience,
                'education': education
            }
            
            # Save to database using SQLAlchemy
            db = SessionLocal()
            try:
                applicant = Applicant.from_dict(applicant_data)
                db.add(applicant)
                db.commit()
                db.refresh(applicant)
                return applicant.id
            except Exception as e:
                db.rollback()
                print(f"Error saving to database: {e}")
                return None
            finally:
                db.close()
            
        except Exception as e:
            print(f"Error processing CV file: {e}")
        
        return None
