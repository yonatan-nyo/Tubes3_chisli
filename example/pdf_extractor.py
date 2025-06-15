# import PyPDF2
# import os

# class PDFExtractor:
#     def __init__(self):
#         self.extracted_texts = {}
    
#     def extract_text_from_pdf(self, pdf_path):
#         """Extract text from PDF file"""
#         try:
#             text = ""
            
#             with open(pdf_path, 'rb') as file:
#                 pdf_reader = PyPDF2.PdfReader(file)
                
#                 # Extract text from all pages
#                 for page_num in range(len(pdf_reader.pages)):
#                     page = pdf_reader.pages[page_num]
#                     text += page.extract_text()
            
#             # Clean text
#             text = self.clean_text(text)
            
#             # Cache extracted text
#             self.extracted_texts[pdf_path] = text
            
#             return text
            
#         except Exception as e:
#             print(f"Error extracting text from {pdf_path}: {e}")
#             return ""
    
#     def clean_text(self, text):
#         """Clean extracted text"""
#         # Remove excessive whitespace
#         text = ' '.join(text.split())
        
#         # Fix common PDF extraction issues
#         text = text.replace('ï¼', '：')  # Fix colon
#         text = text.replace('\n', ' ')
#         text = text.replace('\r', ' ')
        
#         # Remove non-printable characters
#         text = ''.join(char for char in text if char.isprintable() or char.isspace())
        
#         return text.strip()
    
#     def extract_all_pdfs_from_directory(self, directory_path):
#         """Extract text from all PDFs in a directory"""
#         extracted_data = []
#         category_count = {}
        
#         for root, dirs, files in os.walk(directory_path):
#             category = os.path.basename(root)
            
#             # Sort files alphabetically
#             pdf_files = sorted([f for f in files if f.endswith('.pdf')])
            
#             for file in pdf_files:
#                 # Limit to 20 files per category
#                 if category not in category_count:
#                     category_count[category] = 0
                
#                 if category_count[category] >= 20:
#                     continue
                
#                 pdf_path = os.path.join(root, file)
#                 text = self.extract_text_from_pdf(pdf_path)
                
#                 if text:
#                     extracted_data.append({
#                         'path': pdf_path,
#                         'filename': file,
#                         'text': text,
#                         'category': category
#                     })
#                     category_count[category] += 1
        
#         return extracted_data
    
#     def get_cached_text(self, pdf_path):
#         """Get cached extracted text if available"""
#         return self.extracted_texts.get(pdf_path, None)

import PyPDF2
import os
import sys
from datetime import datetime

class PDFExtractor:
    def __init__(self):
        self.extracted_texts = {}
        self.show_progress = True
        self.debug_mode = True
        
    def save_debug(self, filename, content, pdf_name=""):
        """Save debug information"""
        if self.debug_mode:
            debug_dir = "debug_pdf_extraction"
            os.makedirs(debug_dir, exist_ok=True)
            
            # Add PDF name to filename if provided
            if pdf_name:
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{pdf_name}{ext}"
            
            filepath = os.path.join(debug_dir, filename)
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content)
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file with debugging"""
        try:
            pdf_name = os.path.basename(pdf_path).replace('.pdf', '')
            raw_text = ""
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Debug: Save page count
                page_count = len(pdf_reader.pages)
                # self.save_debug(f"1_page_count.txt", f"PDF: {pdf_name}\nPages: {page_count}", pdf_name)
                
                # Extract text from all pages
                page_texts = []
                for page_num in range(page_count):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    page_texts.append(f"=== PAGE {page_num + 1} ===\n{page_text}\n")
                    raw_text += page_text + "\n"
                
                # Save raw extracted text
                # self.save_debug(f"2_raw_extracted.txt", "\n".join(page_texts), pdf_name)
                
                # Clean text
                cleaned_text = self.clean_text(raw_text, pdf_name)
                
                # Cache extracted text
                self.extracted_texts[pdf_path] = cleaned_text
                
                return cleaned_text
                
        except Exception as e:
            error_msg = f"Error extracting text from {pdf_path}: {e}"
            print(error_msg)
            self.save_debug(f"error.txt", error_msg, pdf_name)
            return ""
    
    def clean_text(self, text, pdf_name=""):
        """Clean extracted text while preserving structure"""
        # Save original text
        # self.save_debug(f"3_before_cleaning.txt", f"Length: {len(text)}\n\n{text}", pdf_name)
        
        # Step 1: Replace PDF artifacts
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
        }
        
        cleaned = text
        artifacts_found = []
        
        for old, new in replacements.items():
            count = cleaned.count(old)
            if count > 0:
                artifacts_found.append(f"'{old}' -> '{new}': {count} occurrences")
                cleaned = cleaned.replace(old, new)
        
        # Save artifacts found
        # if artifacts_found:
        #     self.save_debug(f"4_artifacts_found.txt", "\n".join(artifacts_found), pdf_name)
        
        # Step 2: Fix spacing while preserving line breaks
        # Remove excessive spaces on each line
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
        
        # Step 4: Remove non-printable characters except newlines
        cleaned = ''.join(char for char in cleaned if char.isprintable() or char == '\n')
        
        # Save cleaned text
        # self.save_debug(f"5_after_cleaning.txt", f"Length: {len(cleaned)}\nLines: {len(cleaned.split(chr(10)))}\n\n{cleaned}", pdf_name)
        
        return cleaned.strip()
    
    def extract_all_pdfs_from_directory(self, directory_path):
        """Extract text from all PDFs in a directory with progress tracking"""
        extracted_data = []
        category_count = {}
        total_files = 0
        processed_files = 0
        
        # First, count total files to process
        print("\n=== Scanning for PDF files ===")
        for root, dirs, files in os.walk(directory_path):
            category = os.path.basename(root)
            pdf_files = [f for f in files if f.endswith('.pdf')]
            if pdf_files:
                print(f"Found {len(pdf_files)} PDFs in {category}")
                total_files += min(len(pdf_files), 20)  # Max 20 per category
        
        print(f"\nTotal PDFs to process: {total_files}")
        print("=== Starting extraction ===\n")
        
        start_time = datetime.now()
        
        for root, dirs, files in os.walk(directory_path):
            category = os.path.basename(root)
            
            # Sort files alphabetically
            pdf_files = sorted([f for f in files if f.endswith('.pdf')])
            
            for file in pdf_files:
                # Limit to 20 files per category
                if category not in category_count:
                    category_count[category] = 0
                
                if category_count[category] >= 20:
                    continue
                
                pdf_path = os.path.join(root, file)
                
                # Show progress
                processed_files += 1
                print(f"[{processed_files}/{total_files}] Processing: {category}/{file}", end='')
                sys.stdout.flush()
                
                # Extract text
                text = self.extract_text_from_pdf(pdf_path)
                
                if text:
                    extracted_data.append({
                        'path': pdf_path,
                        'filename': file,
                        'text': text,
                        'category': category
                    })
                    category_count[category] += 1
                    print(" ✓")
                else:
                    print(" ✗ (failed)")
        
        # Show completion statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n=== Extraction Complete ===")
        print(f"Total processed: {processed_files} files")
        print(f"Successful: {len(extracted_data)} files")
        print(f"Failed: {processed_files - len(extracted_data)} files")
        print(f"Time taken: {duration:.2f} seconds")
        print(f"Average: {duration/processed_files:.2f} seconds per file")
        print("========================\n")
        
        return extracted_data
    
    def get_cached_text(self, pdf_path):
        """Get cached extracted text if available"""
        return self.extracted_texts.get(pdf_path, None)