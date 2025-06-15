# import re
# from datetime import datetime

# class RegexExtractor:
#     def __init__(self):
#         # Regex patterns for extracting CV information
#         self.patterns = {
#             'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
#             'phone': r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
#             'linkedin': r'(?:linkedin\.com/in/|linkedin\.com/pub/)([a-zA-Z0-9-]+)',
#             'date': r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}\b',
#             'education_degree': r'\b(?:Bachelor|Master|PhD|Ph\.D|MBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|BSc|MSc|BA|MA|Associates?|Diploma|Certificate)\b',
#             'years_experience': r'\b\d+\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?\b',
#         }
        
#     def extract_personal_info(self, text):
#         """Extract personal information from CV text"""
#         info = {}
        
#         # Extract email
#         email_match = re.search(self.patterns['email'], text)
#         if email_match:
#             info['email'] = email_match.group(0)
        
#         # Extract phone
#         phone_match = re.search(self.patterns['phone'], text)
#         if phone_match:
#             info['phone'] = phone_match.group(0).strip()
        
#         # Extract LinkedIn
#         linkedin_match = re.search(self.patterns['linkedin'], text, re.IGNORECASE)
#         if linkedin_match:
#             info['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"
        
#         # Extract name (usually at the beginning)
#         name_pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
#         name_match = re.search(name_pattern, text[:200])
#         if name_match:
#             info['name'] = name_match.group(1)
        
#         return info
    
#     def extract_summary(self, text):
#         """Extract summary/objective section"""
#         summary_keywords = ['summary', 'objective', 'profile', 'about', 'overview']
        
#         for keyword in summary_keywords:
#             pattern = rf'(?i)\b{keyword}\b[:\s]*([^•\n]+(?:\n[^•\n]+)*)'
#             match = re.search(pattern, text)
#             if match:
#                 summary = match.group(1).strip()
#                 # Limit to reasonable length
#                 if len(summary) > 50:
#                     return summary[:500]
        
#         return ""
    
#     def extract_skills(self, text):
#         """Extract skills section"""
#         skills = []
        
#         # Look for skills section
#         skills_pattern = r'(?i)(?:skills|competencies|expertise|technologies|technical skills)[:\s]*([^•\n]+(?:\n[^•\n]+)*)'
#         skills_match = re.search(skills_pattern, text)
        
#         if skills_match:
#             skills_text = skills_match.group(1)
            
#             # Extract individual skills (comma, semicolon, bullet, or newline separated)
#             skills_list = re.split(r'[,;•\n]', skills_text)
            
#             for skill in skills_list:
#                 skill = skill.strip()
#                 # Filter out common non-skill words and ensure reasonable length
#                 non_skill_words = ['and', 'or', 'the', 'in', 'of', 'to', 'for', 'with', 'include', 'including', 'where', 'which', 'that']
#                 if skill and len(skill) > 2 and len(skill) < 50 and skill.lower() not in non_skill_words:
#                     # Check if it contains at least one letter
#                     if any(c.isalpha() for c in skill):
#                         skills.append(skill)
        
#         # Also look for common programming languages and technologies
#         tech_pattern = r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|C\b|PHP|Ruby|Swift|Kotlin|Go|Golang|R\b|Rust|SQL|NoSQL|MongoDB|MySQL|PostgreSQL|HTML5?|CSS3?|React|Angular|Vue|Node\.js|Django|Flask|Spring|\.NET|Docker|Kubernetes|AWS|Azure|GCP|Git|GitHub|Machine Learning|ML|Data Science|AI|Artificial Intelligence|DevOps|CI/CD|REST|API|Agile|Scrum|Linux|Windows|Excel|PowerBI|Tableau|Pandas|NumPy|TensorFlow|PyTorch|Scikit-learn|Jupyter|VS Code|IntelliJ|Eclipse)\b'
#         tech_matches = re.findall(tech_pattern, text, re.IGNORECASE)
        
#         for tech in tech_matches:
#             if tech not in skills:
#                 skills.append(tech)
        
#         # Remove duplicates and return top 20 unique skills
#         seen = set()
#         unique_skills = []
#         for skill in skills:
#             skill_lower = skill.lower()
#             if skill_lower not in seen:
#                 seen.add(skill_lower)
#                 unique_skills.append(skill)
        
#         return unique_skills[:20]
    
#     def extract_experience(self, text):
#         """Extract work experience"""
#         experience = []
        
#         # Pattern for job titles and companies
#         job_pattern = r'(?i)(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|\d{1,2}[-/]\d{4})\s*[-–]\s*(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}|\d{1,2}[-/]\d{4}|Present|Current)\s*\n?([^\n]+?)(?:\n|$)'
        
#         matches = re.findall(job_pattern, text)
        
#         for match in matches:
#             if match:
#                 # Clean up the job title/company
#                 job_info = match.strip()
#                 if len(job_info) > 10:
#                     experience.append(job_info)
        
#         # Alternative pattern for experience section
#         exp_section_pattern = r'(?i)(?:experience|employment|work\s+history)[:\s]*\n((?:[^\n]+\n)*)'
#         exp_section = re.search(exp_section_pattern, text)
        
#         if exp_section and not experience:
#             exp_text = exp_section.group(1)
#             # Extract job entries
#             job_entries = re.split(r'\n\s*\n', exp_text)
            
#             for entry in job_entries[:5]:  # Limit to 5 entries
#                 if entry.strip():
#                     lines = entry.strip().split('\n')
#                     if lines:
#                         experience.append(lines[0])
        
#         return experience[:5]  # Return top 5 experiences
    
#     def extract_education(self, text):
#         """Extract education information"""
#         education = []
        
#         # Look for education section
#         edu_pattern = r'(?i)(?:education|academic|qualification)[:\s]*\n((?:[^\n]+\n)*)'
#         edu_match = re.search(edu_pattern, text)
        
#         if edu_match:
#             edu_text = edu_match.group(1)
            
#             # Extract degree information
#             degree_matches = re.findall(self.patterns['education_degree'], edu_text, re.IGNORECASE)
            
#             # Extract universities
#             uni_pattern = r'(?:University|College|Institute|School)\s+(?:of\s+)?[A-Z][a-zA-Z\s&]+(?:[,\n]|$)'
#             uni_matches = re.findall(uni_pattern, edu_text)
            
#             # Combine degree and university info
#             for i, degree in enumerate(degree_matches):
#                 edu_entry = degree
#                 if i < len(uni_matches):
#                     edu_entry += f" - {uni_matches[i].strip()}"
#                 education.append(edu_entry)
        
#         # Also look for dates near education entries
#         date_pattern = r'(\d{4})\s*[-–]\s*(\d{4})'
#         date_matches = re.findall(date_pattern, text)
        
#         for i, edu in enumerate(education):
#             if i < len(date_matches):
#                 education[i] += f" ({date_matches[i][0]}-{date_matches[i][1]})"
        
#         return education[:3]  # Return top 3 education entries
    
#     def extract_all(self, text):
#         """Extract all information from CV text"""
#         return {
#             'personal_info': self.extract_personal_info(text),
#             'summary': self.extract_summary(text),
#             'skills': self.extract_skills(text),
#             'experience': self.extract_experience(text),
#             'education': self.extract_education(text)
#         }

# import re
# from datetime import datetime
# import os

# class RegexExtractor:
#     def __init__(self):
#         self.patterns = {
#             'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
#             'phone': r'(?:(?:\+?\d{1,3})?[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2,3}\d{3,4}',
#             'linkedin': r'(?:linkedin\.com/in/|linkedin\.com/pub/)([a-zA-Z0-9-]+)',
#             'date': r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}\b',
#             'education_degree': r'\b(?:Bachelor|Master|PhD|Ph\.D|MBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|BSc|MSc|BA|MA|BBA|Associates?|Diploma|Certificate|High School Diploma)\b',
#             'years_experience': r'\b\d+\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?\b',
#         }
#         self.debug_mode = True  # Enable debug mode

#     def save_debug_info(self, filename, content):
#         """Save debug information to file"""
#         if self.debug_mode:
#             debug_dir = "debug_output"
#             os.makedirs(debug_dir, exist_ok=True)
#             with open(os.path.join(debug_dir, filename), 'w', encoding='utf-8') as f:
#                 f.write(content)

#     def clean_text(self, text):
#         """Clean text from PDF extraction artifacts"""
#         # Replace common PDF artifacts
#         text = text.replace('ï¼', ':')
#         text = text.replace('：', ':')  # Replace full-width colon
#         text = text.replace('Â', ' ')
#         text = text.replace('â€‹', '')
#         text = text.replace('  ', ' ')
#         # Remove multiple spaces
#         text = re.sub(r'\s+', ' ', text)
#         return text

#     def extract_personal_info(self, text):
#         """Extract personal information from CV text"""
#         info = {}
        
#         # Clean text first
#         text = self.clean_text(text)
        
#         # Extract email
#         email_match = re.search(self.patterns['email'], text)
#         if email_match:
#             info['email'] = email_match.group(0)
        
#         # Extract phone - look for phone patterns
#         phone_patterns = [
#             r'(?:Phone|Tel|Mobile|Cell|Contact)[\s:]*([+\d\s\-\(\)\.]+)',
#             r'\b(?:\+?1)?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
#             r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b'
#         ]
        
#         for pattern in phone_patterns:
#             phone_match = re.search(pattern, text[:1000], re.IGNORECASE)
#             if phone_match:
#                 phone = phone_match.group(1) if phone_match.lastindex else phone_match.group(0)
#                 phone = phone.strip()
#                 digits = re.sub(r'\D', '', phone)
#                 if len(digits) >= 10:
#                     info['phone'] = phone
#                     break
        
#         # Extract LinkedIn
#         linkedin_match = re.search(self.patterns['linkedin'], text, re.IGNORECASE)
#         if linkedin_match:
#             info['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"
        
#         # Extract name - usually at the beginning
#         name_patterns = [
#             r'^([A-Z][A-Z\s]+)(?:\n|$)',  # All caps name at start
#             r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Title case full name
#             r'(?:Name|Nama)[\s:]*([A-Z][a-zA-Z\s]+)(?:\n|$)',
#         ]
        
#         text_start = text[:500]
#         for pattern in name_patterns:
#             name_match = re.search(pattern, text_start, re.MULTILINE)
#             if name_match:
#                 name = name_match.group(1).strip()
#                 job_titles = ['ACCOUNTANT', 'MANAGER', 'ENGINEER', 'DEVELOPER', 'ANALYST', 
#                              'ADMINISTRATOR', 'DIRECTOR', 'SUPERVISOR', 'COORDINATOR', 'ADVOCATE',
#                              'FINANCIAL', 'CONSUMER']
#                 if name and not any(title in name.upper() for title in job_titles):
#                     if name.isupper() and len(name.split()) > 1:
#                         name = name.title()
#                     info['name'] = name
#                     break
        
#         return info

#     def extract_summary(self, text):
#         """Extract summary/objective section"""
#         text = self.clean_text(text)        
#         # Look for Summary section - more specific pattern
#         summary_patterns = [
#             r'(?i)Summary\s*(?:\n|:)?\s*([^\n]+(?:\n(?!Skills|Experience|Education|Highlights)[^\n]+)*)',
#             r'(?i)(?:Objective|Profile|Professional Profile|About|Overview)\s*(?:\n|:)?\s*([^\n]+(?:\n(?!Skills|Experience|Education)[^\n]+)*)'
#         ]
        
#         for pattern in summary_patterns:
#             match = re.search(pattern, text)
#             if match:
#                 summary = match.group(1).strip()
#                 # Clean up summary
#                 summary = re.sub(r'\s+', ' ', summary)
#                 summary = summary.replace('•', '').strip()
                
#                 # Make sure it's not too short or too long
#                 if 20 < len(summary) < 1000:
#                     self.save_debug_info("summary_extracted.txt", f"Pattern: {pattern}\nExtracted: {summary}")
#                     return summary[:500]
        
#         return ""
    
#     def extract_skills(self, text):
#         """Extract skills section"""
#         text = self.clean_text(text)
#         skills = []
        
#         # Pattern to find Skills section - more flexible
#         skills_patterns = [
#             r'(?i)Skills\s*(?:\n|:)\s*(.*?)(?=\n(?:Experience|Education|Employment|Professional|$))',
#             r'(?i)(?:Technical\s+)?Skills\s*(?:\n|:)\s*(.*?)(?=\n\n)',
#             r'(?i)Highlights\s*(?:\n|:)\s*(.*?)(?=\n(?:Experience|Education|Accomplishments|$))',
#         ]
        
#         skills_text = ""
#         for pattern in skills_patterns:
#             match = re.search(pattern, text, re.DOTALL)
#             if match:
#                 skills_text = match.group(1)
#                 break
        
#         if skills_text:
#             # Extract individual skills - handle both bullet points and regular text
#             lines = skills_text.split('\n')
#             for line in lines:
#                 line = line.strip()
#                 if not line:
#                     continue
                
#                 # Check if line contains a colon (skill category)
#                 if ':' in line:
#                     # Extract skills after colon
#                     parts = line.split(':', 1)
#                     if len(parts) > 1:
#                         skill_part = parts[1].strip()
#                         # Split by common separators
#                         if any(sep in skill_part for sep in [',', ';', '•']):
#                             sub_skills = re.split(r'[,;•]', skill_part)
#                             for skill in sub_skills:
#                                 skill = skill.strip()
#                                 if skill and len(skill) > 2:
#                                     skills.append(skill)
#                         elif len(skill_part) > 2:
#                             skills.append(skill_part)
#                 else:
#                     # It's a standalone skill line
#                     if len(line) > 2 and not any(word in line.lower() for word in ['experience', 'education', 'employment']):
#                         skills.append(line)
        
#         # Also look for technical skills mentioned in the text
#         tech_pattern = r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Swift|Kotlin|Go|R\b|SQL|NoSQL|MongoDB|MySQL|PostgreSQL|Oracle|HTML5?|CSS3?|React|Angular|Vue|Node\.js|Django|Flask|Spring|\.NET|Docker|Kubernetes|AWS|Azure|GCP|Git|Machine Learning|Data Science|AI|DevOps|Linux|Windows|Excel|PowerBI|Tableau|QuickBooks|SAP|ERP|Accounting|Financial Reporting|Budget|Audit|Payroll|Tax|GAAP|Financial Analysis|Microsoft Office|CPA|Customer Service|Communication|Leadership)\b'
#         tech_matches = re.findall(tech_pattern, text, re.IGNORECASE)
        
#         for tech in tech_matches:
#             if tech not in skills:
#                 skills.append(tech)
        
#         # Remove duplicates while preserving order
#         seen = set()
#         unique_skills = []
#         for skill in skills:
#             skill_lower = skill.lower()
#             if skill_lower not in seen and len(skill) < 100:
#                 seen.add(skill_lower)
#                 unique_skills.append(skill)
#         self.save_debug_info("skills_final.txt", "\n".join(unique_skills))
#         return unique_skills[:20]

#     def extract_experience(self, text):
#         """Extract work experience with better formatting"""
#         text = self.clean_text(text)
#         experience = []
        
#         # Find Experience section
#         exp_patterns = [
#             r'(?i)Experience\s*(?:\n|:)?\s*(.*?)(?=Education|Skills|Professional\s+Affiliations|Languages|$)',
#             r'(?i)(?:Employment|Work\s+History|Professional\s+Experience)\s*(?:\n|:)?\s*(.*?)(?=Education|Skills|$)',
#         ]
        
#         exp_text = ""
#         for pattern in exp_patterns:
#             match = re.search(pattern, text, re.DOTALL)
#             if match:
#                 exp_text = match.group(1).strip()
#                 self.save_debug_info("experience_section.txt", f"Pattern: {pattern}\nExtracted: {exp_text}")
#                 break
        
#         if exp_text:
#             # Pattern to match date ranges and job entries
#             # More flexible pattern to handle various formats
#             job_patterns = [
#                 # Pattern 1: MM/YYYY to MM/YYYY or Current
#                 r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current|Present)\s*\n?\s*([^\n]+?)\s+Company\s*Name\s*[:：]\s*([^\n]+)',
#                 # Pattern 2: Date to Date followed by position
#                 r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current|Present)\s*\n?\s*([^\n]+)',
#                 # Pattern 3: Any date pattern
#                 r'([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4})\s+to\s+([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4}|Current|Present)\s*\n?\s*([^\n]+)',
#             ]
            
#             # Try each pattern
#             for pattern in job_patterns:
#                 matches = list(re.finditer(pattern, exp_text, re.MULTILINE))
#                 if matches:
#                     self.save_debug_info("experience_matches.txt", f"Pattern: {pattern}\nMatches: {len(matches)}")
#                     for match in matches:
#                         start_date = match.group(1)
#                         end_date = match.group(2)
#                         position = match.group(3).strip()
                        
#                         # Get company if available (for pattern 1)
#                         company = ""
#                         if match.lastindex >= 4:
#                             company = match.group(4).strip()
                        
#                         # Extract first responsibility line
#                         remaining_text = exp_text[match.end():]
#                         resp_lines = remaining_text.split('\n')
#                         responsibility = ""
#                         for line in resp_lines:
#                             line = line.strip()
#                             if line and len(line) > 20 and not re.match(r'\d{1,2}/\d{4}', line):
#                                 responsibility = line
#                                 break
                        
#                         # Format the experience entry
#                         if company:
#                             exp_entry = f"• {position} at {company}\n  {start_date} - {end_date}"
#                         else:
#                             exp_entry = f"• {position}\n  {start_date} - {end_date}"
                        
#                         if responsibility:
#                             responsibility = re.sub(r'^[-•·]\s*', '', responsibility)
#                             exp_entry += f"\n  {responsibility[:150]}..."
                        
#                         experience.append(exp_entry)
                        
#                         if len(experience) >= 5:
#                             break
                    
#                     if experience:
#                         break
        
#         self.save_debug_info("experience_final.txt", "\n\n".join(experience))
#         return experience[:5]

#     def extract_education(self, text):
#         """Extract education information"""
#         text = self.clean_text(text)
#         education = []
        
#         # Find Education section
#         edu_patterns = [
#             r'(?i)Education(?:\s+and\s+Training)?\s*(?:\n|:)?\s*(.*?)(?=Skills|Professional|Certificates|Languages|$)',
#             r'(?i)(?:Academic|Qualifications?)\s*(?:\n|:)?\s*(.*?)(?=Skills|Professional|$)',
#         ]
        
#         edu_text = ""
#         for pattern in edu_patterns:
#             match = re.search(pattern, text, re.DOTALL)
#             if match:
#                 edu_text = match.group(1).strip()
#                 self.save_debug_info("education_section.txt", f"Pattern: {pattern}\nExtracted: {edu_text}")
#                 break
        
#         if edu_text:
#             # Pattern to match education entries
#             # Looking for patterns like: "January 2014 Master's : Business Administration Troy University"
#             edu_entry_patterns = [
#                 # Pattern 1: Month Year Degree : Field University
#                 r'([A-Za-z]+\s+\d{4})\s+([^:\n]+)\s*:\s*([^\n]+?)\s+([A-Z][^\n]+(?:University|College|Institute|School))',
#                 # Pattern 2: Year Degree in/of Field - University
#                 r'(\d{4})\s+([^:\n]+?)\s+(?:in|of)\s+([^\n-]+)\s*-?\s*([A-Z][^\n]+(?:University|College|Institute|School))',
#                 # Pattern 3: Degree : Field University Location
#                 r'([^:\n]+)\s*:\s*([^\n]+?)\s+([A-Z][^\n]+(?:University|College|Institute|School))\s*[:：]\s*([^\n]+)',
#             ]
            
#             # Try to match education entries
#             for pattern in edu_entry_patterns:
#                 matches = list(re.finditer(pattern, edu_text, re.MULTILINE))
#                 if matches:
#                     self.save_debug_info("education_matches.txt", f"Pattern: {pattern}\nMatches: {len(matches)}")
#                     for match in matches:
#                         if match.lastindex >= 4:
#                             # Extract components based on pattern
#                             if 'Month' in pattern or 'Year' in pattern:
#                                 date = match.group(1)
#                                 degree = match.group(2).strip()
#                                 field = match.group(3).strip()
#                                 institution = match.group(4).strip()
#                                 edu_entry = f"{degree} in {field} - {institution} ({date})"
#                             else:
#                                 degree = match.group(1).strip()
#                                 field = match.group(2).strip()
#                                 institution = match.group(3).strip()
#                                 edu_entry = f"{degree} in {field} - {institution}"
#                         else:
#                             # Fallback: just use the matched text
#                             edu_entry = match.group(0).strip()
                        
#                         education.append(edu_entry)
                        
#                         if len(education) >= 3:
#                             break
                    
#                     if education:
#                         break
            
#             # If no structured matches, try to extract any degree mentions
#             if not education:
#                 degree_matches = re.finditer(self.patterns['education_degree'], edu_text, re.IGNORECASE)
#                 for match in degree_matches:
#                     # Get context around the degree
#                     start = max(0, match.start() - 50)
#                     end = min(len(edu_text), match.end() + 100)
#                     context = edu_text[start:end].strip()
#                     # Clean up the context
#                     context = re.sub(r'\s+', ' ', context)
#                     if context:
#                         education.append(context)
#                         if len(education) >= 3:
#                             break
        
#         self.save_debug_info("education_final.txt", "\n\n".join(education))
#         return education[:3]

#     def extract_all(self, text):
#         """Extract all information from CV text"""
#         self.save_debug_info("original_text.txt", text)
        
#         result = {
#             'personal_info': self.extract_personal_info(text),
#             'summary': self.extract_summary(text),
#             'skills': self.extract_skills(text),
#             'experience': self.extract_experience(text),
#             'education': self.extract_education(text)
#         }
        
#         # Save final result
#         import json
#         self.save_debug_info("final_result.json", json.dumps(result, indent=2))
        
#         return result

# import re
# from datetime import datetime
# import os
# import json

# class RegexExtractor:
#     def __init__(self):
#         self.patterns = {
#             'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
#             'phone': r'(?:(?:\+?\d{1,3})?[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2,3}\d{3,4}',
#             'linkedin': r'(?:linkedin\.com/in/|linkedin\.com/pub/)([a-zA-Z0-9-]+)',
#             'date': r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}\b',
#             'education_degree': r'\b(?:Bachelor|Master|PhD|Ph\.D|MBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|BSc|MSc|BA|MA|BBA|A\.A\.|Associates?|Diploma|Certificate|High School Diploma)\b',
#             'years_experience': r'\b\d+\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?\b',
#         }
#         self.debug_mode = True
#         self.current_filename = ""

#     def save_debug(self, step, content):
#         """Save debug information"""
#         if self.debug_mode:
#             debug_dir = "debug_regex_extraction"
#             os.makedirs(debug_dir, exist_ok=True)
            
#             filename = f"{self.current_filename}_{step}.txt"
#             filepath = os.path.join(debug_dir, filename)
            
#             with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
#                 f.write(content)

#     def extract_personal_info(self, text):
#         """Extract personal information from CV text"""
#         info = {}
        
#         try:
#             # Look at first 1000 chars for personal info
#             text_start = text[:1000]
            
#             # Extract email
#             email_match = re.search(self.patterns['email'], text)
#             if email_match:
#                 info['email'] = email_match.group(0)
            
#             # Extract phone
#             phone_patterns = [
#                 r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
#                 r'\+1\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
#                 r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b'
#             ]
            
#             for pattern in phone_patterns:
#                 phone_match = re.search(pattern, text)
#                 if phone_match:
#                     info['phone'] = phone_match.group(0).strip()
#                     break
            
#             # Extract name - look at first line or lines
#             lines = text.split('\n')
#             for i, line in enumerate(lines[:5]):  # Check first 5 lines
#                 line = line.strip()
#                 if not line:
#                     continue
                    
#                 # Skip if it's a section header
#                 if any(header in line.upper() for header in ['SUMMARY', 'OBJECTIVE', 'SKILLS', 'EXPERIENCE']):
#                     continue
                
#                 # Check if it looks like a name
#                 if len(line) < 50:
#                     # All caps name (common in CVs)
#                     if line.isupper() and ' ' not in line:
#                         # Single word in caps - likely job title or name
#                         if line not in ['ACCOUNTANT', 'MANAGER', 'ENGINEER', 'DEVELOPER', 'ANALYST', 'ADVOCATE']:
#                             info['name'] = line.title()
#                             break
#                     # Regular name format
#                     elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', line):
#                         info['name'] = line
#                         break
            
#             self.save_debug("1_personal_info", f"Personal Info Extracted:\n{json.dumps(info, indent=2)}")
            
#         except Exception as e:
#             self.save_debug("1_personal_info_error", f"Error: {str(e)}")
        
#         return info

#     def extract_summary(self, text):
#         """Extract summary/objective section"""
#         try:
#             # Find Summary section
#             summary_patterns = [
#                 r'Summary\s*\n+(.*?)(?=\n(?:Skills|Experience|Education|Highlights|Accomplishments)|$)',
#                 r'Objective\s*\n+(.*?)(?=\n(?:Skills|Experience|Education)|$)',
#                 r'Profile\s*\n+(.*?)(?=\n(?:Skills|Experience|Education)|$)'
#             ]
            
#             for pattern in summary_patterns:
#                 match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
#                 if match:
#                     summary = match.group(1).strip()
#                     # Clean up
#                     summary = re.sub(r'\s+', ' ', summary)
                    
#                     if 20 < len(summary) < 1000:
#                         self.save_debug("2_summary", f"Pattern: {pattern}\n\nExtracted Summary:\n{summary}")
#                         return summary[:500]
            
#             self.save_debug("2_summary", "No summary found")
            
#         except Exception as e:
#             self.save_debug("2_summary_error", f"Error: {str(e)}")
        
#         return ""

#     def extract_skills(self, text):
#         """Extract skills section"""
#         skills = []
        
#         try:
#             # Find Skills section
#             skills_section_patterns = [
#                 r'Skills\s*\n+(.*?)(?=\n(?:Experience|Education|Employment)|$)',
#                 r'Technical Skills\s*\n+(.*?)(?=\n(?:Experience|Education)|$)',
#                 r'Core Competencies\s*\n+(.*?)(?=\n(?:Experience|Education)|$)',
#                 r'Highlights\s*\n+(.*?)(?=\n(?:Experience|Education|Accomplishments)|$)'
#             ]
            
#             skills_text = ""
#             for pattern in skills_section_patterns:
#                 match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
#                 if match:
#                     skills_text = match.group(1)
#                     self.save_debug("3a_skills_section", f"Pattern: {pattern}\n\nExtracted Section:\n{skills_text}")
#                     break
            
#             if skills_text:
#                 # Check if it's a comma-separated list at the end
#                 if ',' in skills_text and skills_text.count(',') > 5:
#                     # Likely a comma-separated list
#                     skill_items = re.split(r'[,;]', skills_text)
#                     for item in skill_items:
#                         item = item.strip()
#                         if 2 < len(item) < 50 and item:
#                             skills.append(item)
#                 else:
#                     # Process line by line
#                     lines = skills_text.split('\n')
#                     for line in lines:
#                         line = line.strip()
#                         if not line:
#                             continue
                        
#                         # Remove bullet points
#                         line = re.sub(r'^[•\-*]\s*', '', line)
                        
#                         # Check for skill categories (e.g., "Technical Skills: Python, Java")
#                         if ':' in line:
#                             parts = line.split(':', 1)
#                             if len(parts) == 2:
#                                 # Extract skills after colon
#                                 skill_list = parts[1]
#                                 sub_skills = re.split(r'[,;]', skill_list)
#                                 for skill in sub_skills:
#                                     skill = skill.strip()
#                                     if 2 < len(skill) < 50:
#                                         skills.append(skill)
#                         else:
#                             # Add the whole line as a skill
#                             if 2 < len(line) < 100:
#                                 skills.append(line)
            
#             # Also look for technical skills throughout the document
#             tech_skills = set()
#             tech_pattern = r'\b(?:Python|Java|JavaScript|C\+\+|SQL|Excel|Word|PowerPoint|Outlook|QuickBooks|Accounting|Payroll|Financial Analysis|Project Management|Customer Service|Communication|Leadership|Teamwork|Problem Solving|Data Analysis|Microsoft Office|CPA|GAAP|SAP|Oracle)\b'
            
#             tech_matches = re.findall(tech_pattern, text, re.IGNORECASE)
#             for tech in tech_matches:
#                 tech_skills.add(tech)
            
#             # Add technical skills
#             skills.extend(list(tech_skills))
            
#             # Remove duplicates
#             seen = set()
#             unique_skills = []
#             for skill in skills:
#                 skill_lower = skill.lower().strip()
#                 if skill_lower not in seen and skill_lower:
#                     seen.add(skill_lower)
#                     unique_skills.append(skill)
            
#             self.save_debug("3b_skills_final", f"Total skills found: {len(unique_skills)}\n\n" + "\n".join(f"- {s}" for s in unique_skills))
            
#         except Exception as e:
#             self.save_debug("3_skills_error", f"Error: {str(e)}")
        
#         return unique_skills[:20]

#     def extract_experience(self, text):
#         """Extract work experience"""
#         experience = []
        
#         try:
#             # Find Experience section
#             exp_section_pattern = r'Experience\s*\n+(.*?)(?=\n(?:Education|Skills|Certifications|Interests|Additional)|$)'
#             exp_match = re.search(exp_section_pattern, text, re.IGNORECASE | re.DOTALL)
            
#             if exp_match:
#                 exp_text = exp_match.group(1)
#                 self.save_debug("4a_experience_section", f"Experience Section Found:\n{exp_text}")
                
#                 # Pattern for job entries with dates
#                 job_patterns = [
#                     # Pattern 1: MM/YYYY to MM/YYYY followed by position and company
#                     r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current|Present)\s*\n+([^\n]+?)\s+Company\s*Name\s*:\s*([^\n]+)',
#                     # Pattern 2: Position Company Name : Location with dates nearby
#                     r'([A-Za-z\s,/\-]+?)\s+Company\s*Name\s*:\s*([^\n]+)',
#                     # Pattern 3: Company Name Date to Date Position
#                     r'Company\s*Name\s*([A-Za-z]+\s+\d{4})\s+to\s+([A-Za-z]+\s+\d{4}|Present)\s+([^\n]+)'
#                 ]
                
#                 # Try first pattern (most common)
#                 matches = list(re.finditer(job_patterns[0], exp_text))
                
#                 if matches:
#                     self.save_debug("4b_job_matches", f"Found {len(matches)} jobs with pattern 1")
                    
#                     for i, match in enumerate(matches):
#                         start_date = match.group(1)
#                         end_date = match.group(2)
#                         position = match.group(3).strip()
#                         location = match.group(4).strip()
                        
#                         # Get responsibilities
#                         start_pos = match.end()
#                         # Find next job or end
#                         if i + 1 < len(matches):
#                             end_pos = matches[i + 1].start()
#                         else:
#                             end_pos = len(exp_text)
                        
#                         resp_text = exp_text[start_pos:end_pos].strip()
                        
#                         # Extract first few responsibilities
#                         responsibilities = []
#                         sentences = re.split(r'(?<=[.!?])\s+', resp_text)
                        
#                         for sent in sentences[:3]:
#                             sent = sent.strip()
#                             if sent and len(sent) > 20:
#                                 if not re.match(r'\d{1,2}/\d{4}', sent):  # Not a date
#                                     responsibilities.append(f"• {sent}")
                        
#                         # Format entry
#                         exp_entry = f"{position} at {location}\n{start_date} - {end_date}"
#                         if responsibilities:
#                             exp_entry += "\n" + "\n".join(responsibilities)
                        
#                         experience.append(exp_entry)
#                 else:
#                     # Try pattern 2 if pattern 1 fails
#                     self.save_debug("4b_job_matches", "Trying pattern 2")
#                     matches = list(re.finditer(job_patterns[1], exp_text))
                    
#                     for match in matches[:5]:
#                         position = match.group(1).strip()
#                         location = match.group(2).strip()
                        
#                         # Look for dates before this match
#                         before_text = exp_text[:match.start()]
#                         date_pattern = r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current|Present)'
#                         date_match = None
                        
#                         for dm in re.finditer(date_pattern, before_text):
#                             date_match = dm  # Get the last date match before this position
                        
#                         if date_match:
#                             exp_entry = f"{position} at {location}\n{date_match.group(1)} - {date_match.group(2)}"
#                         else:
#                             exp_entry = f"{position} at {location}"
                        
#                         experience.append(exp_entry)
            
#             self.save_debug("4c_experience_final", f"Total experience entries: {len(experience)}\n\n" + 
#                            "\n\n---\n\n".join(experience))
            
#         except Exception as e:
#             self.save_debug("4_experience_error", f"Error: {str(e)}\n\nStack trace:\n{e.__traceback__}")
        
#         return experience[:5]

#     def extract_education(self, text):
#         """Extract education information"""
#         education = []
        
#         try:
#             # Find Education section
#             edu_patterns = [
#                 r'Education\s*(?:and Training)?\s*\n+(.*?)(?=\n(?:Skills|Certifications|Interests|Additional|$))',
#                 r'Education\s*\n+(.*?)$'  # If education is at the end
#             ]
            
#             edu_text = ""
#             for pattern in edu_patterns:
#                 match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
#                 if match:
#                     edu_text = match.group(1)
#                     self.save_debug("5a_education_section", f"Pattern: {pattern}\n\nEducation Section:\n{edu_text}")
#                     break
            
#             if edu_text:
#                 # Look for degree entries
#                 # Pattern: Degree : Field Institution Year
#                 degree_patterns = [
#                     # A.A. : Business Management-Accounting , 2016
#                     r'([A-Z]\.[A-Z]\.|Bachelor|Master|MBA|BBA|PhD|Diploma|Certificate)\s*:\s*([^,\n]+?)(?:\s*,\s*(\d{4}))?',
#                     # January 2014 Master's : Business Administration Troy University
#                     r'([A-Za-z]+\s+\d{4})\s+([^:]+)\s*:\s*([^\n]+)',
#                     # Traditional format: Bachelor of Science in Computer Science
#                     r'(Bachelor|Master|MBA|BBA|PhD)\s+(?:of\s+)?([^,\n]+?)(?:\s+(?:from|at)\s+)?([A-Z][^\n]*(?:University|College|Institute|School))'
#                 ]
                
#                 for pattern in degree_patterns:
#                     matches = list(re.finditer(pattern, edu_text, re.IGNORECASE))
                    
#                     if matches:
#                         self.save_debug("5b_degree_matches", f"Pattern: {pattern}\nFound {len(matches)} matches")
                        
#                         for match in matches:
#                             groups = match.groups()
                            
#                             if pattern.startswith(r'([A-Z]\.[A-Z]\.|'):
#                                 # First pattern
#                                 degree = groups[0]
#                                 field = groups[1].strip()
#                                 year = groups[2] if len(groups) > 2 and groups[2] else ""
                                
#                                 # Look for institution after this match
#                                 after_text = edu_text[match.end():match.end()+200]
#                                 inst_match = re.search(r'([A-Z][^\n:,]+(?:University|College|Institute|School))', after_text)
#                                 institution = inst_match.group(1) if inst_match else ""
                                
#                                 if institution:
#                                     edu_entry = f"{degree} in {field} - {institution}"
#                                 else:
#                                     edu_entry = f"{degree} in {field}"
                                
#                                 if year:
#                                     edu_entry += f" ({year})"
                                    
#                                 education.append(edu_entry)
                            
#                             elif pattern.startswith(r'([A-Za-z]+\s+\d{4})'):
#                                 # Second pattern
#                                 date = groups[0]
#                                 degree = groups[1].strip()
#                                 field_and_inst = groups[2].strip()
                                
#                                 # Try to separate field and institution
#                                 inst_match = re.search(r'([A-Z][^\n]+(?:University|College|Institute|School))', field_and_inst)
#                                 if inst_match:
#                                     institution = inst_match.group(1)
#                                     field = field_and_inst.replace(institution, '').strip()
#                                     edu_entry = f"{degree} in {field} - {institution} ({date})"
#                                 else:
#                                     edu_entry = f"{degree} in {field_and_inst} ({date})"
                                
#                                 education.append(edu_entry)
                        
#                         if education:
#                             break
            
#             self.save_debug("5c_education_final", f"Total education entries: {len(education)}\n\n" + 
#                            "\n".join(f"- {e}" for e in education))
            
#         except Exception as e:
#             self.save_debug("5_education_error", f"Error: {str(e)}")
        
#         return education[:3]

#     def extract_all(self, text):
#         """Extract all information from CV text"""
#         try:
#             # Set current filename for debugging
#             if hasattr(self, '_current_cv_path'):
#                 self.current_filename = os.path.basename(self._current_cv_path).replace('.pdf', '')
#             else:
#                 self.current_filename = "unknown"
            
#             # Save original text
#             self.save_debug("0_original_text", f"Text length: {len(text)}\nLine count: {len(text.split(chr(10)))}\n\n{text}")
            
#             # Limit text length to prevent performance issues
#             if len(text) > 50000:
#                 text = text[:50000]
#                 self.save_debug("0_text_truncated", "Text was truncated to 50000 characters")
            
#             result = {
#                 'personal_info': self.extract_personal_info(text),
#                 'summary': self.extract_summary(text),
#                 'skills': self.extract_skills(text),
#                 'experience': self.extract_experience(text),
#                 'education': self.extract_education(text)
#             }
            
#             # Save final result
#             self.save_debug("6_final_result", json.dumps(result, indent=2))
            
#             return result
            
#         except Exception as e:
#             error_msg = f"Error in extract_all: {str(e)}"
#             self.save_debug("error_extract_all", error_msg)
#             print(error_msg)
            
#             return {
#                 'personal_info': {},
#                 'summary': '',
#                 'skills': [],
#                 'experience': [],
#                 'education': []
#             }

import re
from datetime import datetime
import os
import json

class RegexExtractor:
    def __init__(self):
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(?:(?:\+?\d{1,3})?[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2,3}\d{3,4}',
            'linkedin': r'(?:linkedin\.com/in/|linkedin\.com/pub/)([a-zA-Z0-9-]+)',
            'date': r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}\b',
            'education_degree': r'\b(?:Bachelor|Master|PhD|Ph\.D|MBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|BSc|MSc|BA|MA|BBA|A\.A\.|Associates?|Diploma|Certificate|High School Diploma)\b',
            'years_experience': r'\b\d+\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)?\b',
        }
        self.debug_mode = True # This can be set to False to disable saving debug files
        self.current_filename = ""

    def save_debug(self, step, content):
        """Save debug information if debug_mode is True."""
        if self.debug_mode:
            debug_dir = "debug_regex_extraction"
            os.makedirs(debug_dir, exist_ok=True)
            
            filename_base = self.current_filename if self.current_filename else "unknown_cv"
            filename = f"{filename_base}_{step}.txt"
            filepath = os.path.join(debug_dir, filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(content)
            except Exception as e:
                print(f"Error saving debug file {filepath}: {e}")

    def extract_personal_info(self, text):
        """Extract personal information from CV text"""
        info = {}
        try:
            text_start = text[:1000]
            
            email_match = re.search(self.patterns['email'], text)
            if email_match:
                info['email'] = email_match.group(0)
            
            phone_patterns = [
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\+1\s*\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b'
            ]
            for pattern in phone_patterns:
                phone_match = re.search(pattern, text_start)
                if phone_match:
                    info['phone'] = phone_match.group(0).strip()
                    break
            
            lines = text.split('\n')
            for i, line in enumerate(lines[:5]):
                line = line.strip()
                if not line: continue
                if any(header in line.upper() for header in ['SUMMARY', 'OBJECTIVE', 'SKILLS', 'EXPERIENCE', 'EDUCATION', 'PROFILE']):
                    continue
                if len(line) < 50:
                    if line.isupper() and ' ' in line and len(line.split()) > 1 and len(line.split()) < 4 :
                        is_likely_name = True
                        for word in line.split():
                            if word in ['ACCOUNTANT', 'MANAGER', 'ENGINEER', 'DEVELOPER', 'ANALYST', 'ADVOCATE', 'SUMMARY', 'OBJECTIVE', 'SKILLS', 'EXPERIENCE', 'PROFILE']:
                                is_likely_name = False
                                break
                        if is_likely_name:
                            info['name'] = line.title()
                            break
                    elif re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$', line):
                        info['name'] = line
                        break
            # self.save_debug("1_personal_info", f"Personal Info Extracted:\n{json.dumps(info, indent=2)}")
        except Exception as e:
            # self.save_debug("1_personal_info_error", f"Error in extract_personal_info: {str(e)}")
            print(f"Error in extract_personal_info: {str(e)}")
        return info

    def extract_summary(self, text):
        """Extract summary/objective section"""
        summary = ""
        try:
            summary_patterns = [
                r'Summary\s*\n+(.*?)(?=\n(?:Skills|Experience|Education|Highlights|Accomplishments|Core Competencies)|$)',
                r'Objective\s*\n+(.*?)(?=\n(?:Skills|Experience|Education|Highlights|Accomplishments|Core Competencies)|$)',
                r'Profile\s*\n+(.*?)(?=\n(?:Skills|Experience|Education|Highlights|Accomplishments|Core Competencies)|$)'
            ]
            
            for pattern in summary_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    summary_text = match.group(1).strip()
                    summary_text = re.sub(r'\s+', ' ', summary_text)
                    if 20 < len(summary_text) < 1000:
                        # self.save_debug("2_summary", f"Pattern: {pattern}\n\nExtracted Summary:\n{summary_text}")
                        summary = summary_text[:500]
                        return summary
            # self.save_debug("2_summary", "No summary found or summary too short/long.")
        except Exception as e:
            # self.save_debug("2_summary_error", f"Error in extract_summary: {str(e)}")
            print(f"Error in extract_summary: {str(e)}")
        return summary

    def extract_skills(self, text):
        """Extract skills section"""
        skills = []
        try:
            skills_section_patterns = [
                r'Skills\s*\n+(.*?)(?=\n(?:Experience|Education|Employment|Professional Affiliations|Interests|Awards)|$)',
                r'Technical Skills\s*\n+(.*?)(?=\n(?:Experience|Education|Employment|Professional Affiliations)|$)',
                r'Core Competencies\s*\n+(.*?)(?=\n(?:Experience|Education|Employment|Professional Affiliations)|$)',
                r'Highlights\s*\n+(.*?)(?=\n(?:Experience|Education|Employment|Accomplishments)|$)'
            ]
            
            skills_text_content = ""
            for pattern in skills_section_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    skills_text_content = match.group(1).strip()
                    # self.save_debug("3a_skills_section", f"Pattern: {pattern}\n\nExtracted Section:\n{skills_text_content}")
                    break
            
            temp_skills_list = []
            if skills_text_content:
                lines = skills_text_content.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    line = re.sub(r'^[•\-*]\s*', '', line)
                    
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            skill_list_after_colon = parts[1]
                            sub_skills_from_colon = re.split(r'[,;]', skill_list_after_colon)
                            for skill_item in sub_skills_from_colon:
                                skill_item = skill_item.strip().rstrip('.')
                                if 2 < len(skill_item) < 50 and skill_item:
                                    temp_skills_list.append(skill_item)
                    else:
                        if ';' in line or (',' in line and line.count(',') > 0 and line.count(',') < 5) :
                            sub_skills_from_line = re.split(r'[,;]', line)
                            for skill_item in sub_skills_from_line:
                                skill_item = skill_item.strip().rstrip('.')
                                if 2 < len(skill_item) < 50 and skill_item:
                                    temp_skills_list.append(skill_item)
                        elif 2 < len(line) < 100 and not any(header in line.upper() for header in ['EXPERIENCE', 'EDUCATION', 'CERTIFICATIONS']):
                            temp_skills_list.append(line.rstrip('.'))

            tech_skills_found = set()
            tech_pattern = r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Swift|Kotlin|Go|R\b|SQL|NoSQL|MongoDB|MySQL|PostgreSQL|Oracle|HTML5?|CSS3?|React|Angular|Vue|Node\.js|Django|Flask|Spring|\.NET|Docker|Kubernetes|AWS|Azure|GCP|Git|Machine Learning|Data Analysis|Data Science|AI|DevOps|Linux|Windows|Excel|Word|PowerPoint|Outlook|QuickBooks|Accounting|General Accounting|Accounts Payable|Payroll|Financial Analysis|Financial Reporting|Budget(?:ing)?|Audit(?:ing)?|Tax(?:ation)?|GAAP|SAP|ERP|Program Management|Project Management|Customer Service|Communication|Leadership|Teamwork|Problem Solving|Microsoft Office|CPA)\b'
            tech_matches = re.findall(tech_pattern, text, re.IGNORECASE)
            for tech in tech_matches:
                tech_skills_found.add(tech)
            
            temp_skills_list.extend(list(tech_skills_found))
            
            seen = set()
            unique_skills = []
            for skill_val in temp_skills_list:
                skill_lower = skill_val.lower().strip()
                if skill_lower not in seen and skill_lower:
                    seen.add(skill_lower)
                    unique_skills.append(skill_val)
            
            skills = unique_skills
            # self.save_debug("3b_skills_final", f"Total skills found: {len(skills)}\n\n" + "\n".join(f"- {s}" for s in skills))
        except Exception as e:
            # self.save_debug("3_skills_error", f"Error in extract_skills: {str(e)}")
            print(f"Error in extract_skills: {str(e)}")
        return skills[:20]

    def extract_experience(self, text):
        """Extract work experience"""
        experience = []
        exp_text = ""
        try:
            exp_section_pattern = r'Experience\s*\n+(.*?)(?=\n(?:Education|Skills|Certifications|Interests|Additional Information|Professional Affiliations|Languages)|$)'
            exp_match = re.search(exp_section_pattern, text, re.IGNORECASE | re.DOTALL)
            
            if exp_match:
                exp_text = exp_match.group(1).strip()
                # self.save_debug("4a_experience_section", f"Experience Section Found:\n{exp_text}")
            else:
                # self.save_debug("4a_experience_section", "No Experience Section Found with primary pattern.")
                return []

            pattern_original_mm_yyyy = r'(\d{1,2}/\d{4})\s+to\s+(\d{1,2}/\d{4}|Current|Present)\s*\n+([^\n]+?)\s+Company\s*Name\s*:\s*([^\n]+)'
            pattern_original_pos_company_loc = r'([A-Za-z\s,/\-]+?)\s+Company\s*Name\s*:\s*([^\n]+)'
            pattern_accountant_job = r'^(Company Name)\s*\n+([A-Za-z]+\s+\d{4})\s+to\s+([A-Za-z]+\s+\d{4}|Current|Present)\s*\n+([^\n]+?)\s*\n+([^\n]*(?:City|State)[^\n]*)\s*\n+'

            job_patterns = [
                pattern_original_mm_yyyy,
                pattern_accountant_job,
                pattern_original_pos_company_loc,
            ]

            all_exp_matches = []
            matched_pattern_type = None
            
            for idx, pattern_str in enumerate(job_patterns):
                flags = re.IGNORECASE | re.DOTALL
                if pattern_str.startswith('^'):
                    flags |= re.MULTILINE
                current_matches = list(re.finditer(pattern_str, exp_text, flags))
                if current_matches:
                    # self.save_debug(f"4b_job_matches_pattern_{idx}", f"Found {len(current_matches)} jobs with pattern index {idx}:\n{pattern_str}")
                    all_exp_matches = current_matches
                    if pattern_str == pattern_original_mm_yyyy: matched_pattern_type = "original_mm_yyyy"
                    elif pattern_str == pattern_accountant_job: matched_pattern_type = "accountant_month_yyyy"
                    elif pattern_str == pattern_original_pos_company_loc: matched_pattern_type = "original_pos_company_loc"
                    break 
            
            if all_exp_matches:
                # self.save_debug("4b_job_matches_summary", f"Processing {len(all_exp_matches)} jobs with pattern type: {matched_pattern_type}")
                for i, match_obj in enumerate(all_exp_matches):
                    exp_entry = ""
                    company = ""
                    position = ""
                    start_date = ""
                    end_date = ""
                    location = ""

                    if matched_pattern_type == "original_mm_yyyy":
                        start_date = match_obj.group(1)
                        end_date = match_obj.group(2)
                        position = match_obj.group(3).strip()
                        company_or_location = match_obj.group(4).strip() if match_obj.lastindex >= 4 else ""
                        company = company_or_location 
                        exp_entry = f"{position} at {company}\n{start_date} - {end_date}"
                    
                    elif matched_pattern_type == "accountant_month_yyyy":
                        company_placeholder = match_obj.group(1).strip()
                        start_date = match_obj.group(2).strip()
                        end_date = match_obj.group(3).strip()
                        position = match_obj.group(4).strip()
                        location = match_obj.group(5).strip()
                        company = location if company_placeholder.lower() == "company name" else company_placeholder
                        exp_entry = f"{position} at {company}\n{start_date} - {end_date}"

                    elif matched_pattern_type == "original_pos_company_loc":
                        position = match_obj.group(1).strip()
                        company = match_obj.group(2).strip() 
                        before_text = exp_text[:match_obj.start()]
                        date_pattern_exp = r'([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4})\s+to\s+([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4}|Current|Present)'
                        date_match_exp = None
                        for dm_exp in reversed(list(re.finditer(date_pattern_exp, before_text))):
                            date_match_exp = dm_exp
                            break
                        if date_match_exp:
                            start_date = date_match_exp.group(1)
                            end_date = date_match_exp.group(2)
                            exp_entry = f"{position} at {company}\n{start_date} - {end_date}"
                        else:
                            exp_entry = f"{position} at {company}"
                    
                    if exp_entry:
                        start_pos_resp = match_obj.end()
                        end_pos_resp = len(exp_text)
                        if i + 1 < len(all_exp_matches):
                            end_pos_resp = all_exp_matches[i+1].start()
                        
                        resp_text_segment = exp_text[start_pos_resp:end_pos_resp].strip()
                        responsibilities_list = []
                        resp_lines = resp_text_segment.split('\n')
                        for resp_line in resp_lines:
                            resp_line = resp_line.strip()
                            resp_line = re.sub(r'^[•*-]\s*', '', resp_line)
                            if resp_line and len(resp_line) > 10 and \
                               not re.match(r'([A-Za-z]+\s+\d{4}|\d{1,2}/\d{4})\s+to', resp_line) and \
                               not resp_line.lower().startswith("company name"):
                                responsibilities_list.append(f"• {resp_line}")
                                if len(responsibilities_list) >= 2:
                                    break
                        if responsibilities_list:
                            exp_entry += "\n" + "\n".join(responsibilities_list)
                        experience.append(exp_entry)
                    if len(experience) >= 5: break
            # else:
                 # self.save_debug("4b_job_matches_summary", "No job matches found with any defined patterns.")
            # self.save_debug("4c_experience_final", f"Total experience entries: {len(experience)}\n\n" + "\n\n---\n\n".join(experience))
        except Exception as e:
            # self.save_debug("4_experience_error", f"Error in extract_experience: {str(e)}\n\nStack trace:\n{e.__traceback__}")
            print(f"Error in extract_experience: {str(e)}")
        return experience[:5]

    def extract_education(self, text):
        """Extract education information"""
        education = []
        edu_text = ""
        try:
            edu_patterns_main = [
                r'Education(?:\s+and\s+Training)?\s*\n+(.*?)(?=\n(?:Skills|Professional Affiliations|Certifications|Interests|Additional Information|Awards|Languages)|$)',
                r'Education\s*\n+(.*?)$' 
            ]
            
            for pattern in edu_patterns_main:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    edu_text = match.group(1).strip()
                    # self.save_debug("5a_education_section", f"Pattern: {pattern}\n\nEducation Section:\n{edu_text}")
                    break
            
            if edu_text:
                pattern_edu_aa_field_year = r'([A-Z]\.[A-Z]\.|Bachelor|Master|MBA|BBA|PhD|Diploma|Certificate)\s*:\s*([^,\n]+?)(?:\s*,\s*(\d{4}))?'
                pattern_edu_month_year_degree_fieldinst = r'([A-Za-z]+\s+\d{4})\s+([^:]+)\s*:\s*([^\n]+)'
                pattern_edu_degree_of_field_inst = r'(Bachelor|Master|MBA|BBA|PhD)\s+(?:of\s+)?([^,\n]+?)(?:\s+(?:from|at)\s+)?([A-Z][^\n]*(?:University|College|Institute|School))'
                pattern_edu_consumer_advocate = r'^(Certificate[^\n]*\.\s*)\n+([A-Z][A-Za-z\s.,&-]+(?:Association|Institute|School|College|University))\s*(?:\n*:\s*\n*([A-Za-z\s]+,\s*[A-Z]{2}))?'
                pattern_edu_accountant = r'^([A-Z][A-Za-z\s.,-]+(?:University|College|Institute|School))\s*\n+(\d{4})\s*\n+([A-Za-z.\s()]+?)\s*:\s*([^,\n]+)'

                degree_patterns_list = [
                    pattern_edu_aa_field_year,
                    pattern_edu_month_year_degree_fieldinst,
                    pattern_edu_degree_of_field_inst,
                    pattern_edu_consumer_advocate,
                    pattern_edu_accountant
                ]
                
                for pattern_str in degree_patterns_list:
                    flags = re.IGNORECASE | re.DOTALL
                    if pattern_str.startswith('^'):
                        flags |= re.MULTILINE
                    
                    matches = list(re.finditer(pattern_str, edu_text, flags))
                    
                    if matches:
                        # self.save_debug("5b_degree_matches", f"Pattern: {pattern_str}\nFound {len(matches)} matches for education")
                        for match_obj in matches:
                            groups = match_obj.groups()
                            edu_entry = ""
                            year = "" # Initialize year to check if it's found by specific patterns

                            if pattern_str == pattern_edu_aa_field_year:
                                degree = groups[0]
                                field = groups[1].strip()
                                year = groups[2] if len(groups) > 2 and groups[2] else ""
                                after_text = edu_text[match_obj.end():match_obj.end()+200]
                                inst_match_edu = re.search(r'([A-Z][^\n:,]+(?:University|College|Institute|School))', after_text)
                                institution = inst_match_edu.group(1).strip() if inst_match_edu else ""
                                if institution: edu_entry = f"{degree} in {field} - {institution}"
                                else: edu_entry = f"{degree} in {field}"
                                if year: edu_entry += f" ({year})"

                            elif pattern_str == pattern_edu_month_year_degree_fieldinst:
                                date = groups[0] # This contains year
                                year = re.search(r'\d{4}', date).group(0) if re.search(r'\d{4}', date) else ""
                                degree_text = groups[1].strip()
                                field_and_inst = groups[2].strip()
                                inst_match_edu = re.search(r'([A-Z][^\n]+(?:University|College|Institute|School))', field_and_inst)
                                if inst_match_edu:
                                    institution = inst_match_edu.group(1).strip()
                                    field = field_and_inst.replace(institution, '').strip()
                                    edu_entry = f"{degree_text} in {field} - {institution} ({date})"
                                else:
                                    edu_entry = f"{degree_text} in {field_and_inst} ({date})"
                            
                            elif pattern_str == pattern_edu_degree_of_field_inst:
                                degree = groups[0].strip()
                                field = groups[1].strip()
                                institution = groups[2].strip() if len(groups) > 2 and groups[2] else ""
                                edu_entry = f"{degree} in {field}"
                                if institution: edu_entry += f" - {institution}"
                                context_around_match = edu_text[max(0, match_obj.start()-50) : min(len(edu_text), match_obj.end()+50)]
                                year_match_edu = re.search(r'\b((?:19|20)\d{2})\b', context_around_match)
                                if year_match_edu and not year in edu_entry :
                                    edu_entry += f" ({year_match_edu.group(1)})"
                                    year = year_match_edu.group(1) # Store found year
                            
                            elif pattern_str == pattern_edu_consumer_advocate:
                                description = groups[0].strip()
                                institution = groups[1].strip()
                                location = groups[2].strip() if len(groups) > 2 and groups[2] else ""
                                edu_entry = f"{description} - {institution}"
                                if location: edu_entry += f" ({location})"
                            
                            elif pattern_str == pattern_edu_accountant:
                                institution = groups[0].strip()
                                year = groups[1].strip()
                                degree = groups[2].strip()
                                field = groups[3].strip()
                                edu_entry = f"{degree} in {field} - {institution} ({year})"

                            if edu_entry and edu_entry not in education:
                                education.append(edu_entry)
                            if len(education) >= 3: break
                        if education: break
                
                if not education:
                    # self.save_debug("5b_degree_matches", "No matches with primary patterns, trying fallback.")
                    degree_keyword_matches = list(re.finditer(self.patterns['education_degree'], edu_text, re.IGNORECASE))
                    for dk_match in degree_keyword_matches:
                        start_context = max(0, dk_match.start() - 70)
                        end_context = min(len(edu_text), dk_match.end() + 100)
                        context = edu_text[start_context:end_context].strip()
                        context = re.sub(r'\s+', ' ', context)
                        context_lines = context.split('\n')
                        best_context_line = ""
                        for c_line in context_lines:
                            if dk_match.group(0) in c_line:
                                best_context_line = c_line.strip()
                                break
                        if not best_context_line: best_context_line = context
                        if best_context_line and best_context_line not in education:
                            education.append(best_context_line)
                            if len(education) >= 3: break
            # self.save_debug("5c_education_final", f"Total education entries: {len(education)}\n\n" + "\n".join(f"- {e}" for e in education))
        except Exception as e:
            # self.save_debug("5_education_error", f"Error in extract_education: {str(e)}")
            print(f"Error in extract_education: {str(e)}")
        return education[:3]

    def extract_all(self, text):
        """Extract all information from CV text"""
        try:
            if hasattr(self, '_current_cv_path_for_debug'):
                self.current_filename = os.path.basename(self._current_cv_path_for_debug).replace('.pdf', '')
            elif 'unknown' not in self.current_filename and self.current_filename :
                 pass
            else:
                first_line = text.split('\n')[0].strip()
                potential_name = "".join(c for c in first_line if c.isalnum() or c == ' ')[:30].replace(" ","_")
                self.current_filename = potential_name if potential_name else "unknown_cv"

            # self.save_debug("0_original_text", f"Text length: {len(text)}\nLine count: {len(text.split(chr(10)))}\n\n{text}")
            
            if len(text) > 70000:
                text = text[:70000]
                # self.save_debug("0_text_truncated", "Text was truncated to 70000 characters")
            
            result = {
                'personal_info': self.extract_personal_info(text),
                'summary': self.extract_summary(text),
                'skills': self.extract_skills(text),
                'experience': self.extract_experience(text),
                'education': self.extract_education(text)
            }
            
            # self.save_debug("6_final_result", json.dumps(result, indent=2))
            return result
            
        except Exception as e:
            error_msg = f"Error in extract_all: {str(e)}"
            # self.save_debug("error_extract_all", error_msg)
            print(f"Error in extract_all: {str(e)}") # Also print to console
            return {
                'personal_info': {}, 'summary': '', 'skills': [],
                'experience': [], 'education': []
            }