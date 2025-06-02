import flet as ft
from typing import Callable

class UploadSection:
    """CV upload section component"""
    
    def __init__(self, page: ft.Page, cv_processor, on_upload_callback: Callable):
        self.page = page
        self.cv_processor = cv_processor
        self.on_upload_callback = on_upload_callback
        
        # UI components
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.selected_file_text = ft.Text("No file selected", color=ft.Colors.GREY_600)
        self.upload_button = ft.ElevatedButton(
            "Upload CV",
            disabled=True,
            on_click=self.upload_cv
        )
        self.progress_bar = ft.ProgressBar(visible=False)
        
        # Add file picker to page
        self.page.overlay.append(self.file_picker)
    
    def build(self) -> ft.Control:
        """Build upload section UI"""
        return ft.Column([
            ft.Text("Upload CV", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10),
            
            # File selection
            ft.Container(
                content=ft.Column([
                    ft.ElevatedButton(
                        "Select PDF File",
                        on_click=self.open_file_picker,
                        width=280
                    ),
                    ft.Container(height=8),
                    self.selected_file_text,
                ]),
                padding=15,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                bgcolor=ft.Colors.GREY_50
            ),
            
            ft.Container(height=15),
            
            # Upload button and progress
            self.upload_button,
            self.progress_bar,
            
            ft.Container(height=15),
            
            # Instructions - More compact
            ft.Container(
                content=ft.Column([
                    ft.Text("Instructions:", weight=ft.FontWeight.BOLD, size=13),
                    ft.Text("• Select a PDF file containing the CV", size=11),
                    ft.Text("• File will be processed automatically", size=11),
                    ft.Text("• Text will be extracted and saved as TXT", size=11),
                    ft.Text("• Information will be stored in database", size=11),
                ], spacing=3),
                padding=12,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=8
            )
        ], spacing=10, scroll=ft.ScrollMode.AUTO)
    
    def open_file_picker(self, e):
        """Open file picker dialog"""
        self.file_picker.pick_files(
            dialog_title="Select CV PDF File",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["pdf"]
        )
    
    def on_file_picked(self, e: ft.FilePickerResultEvent):
        """Handle file selection"""
        if e.files and len(e.files) > 0:
            file = e.files[0]
            self.selected_file = file
            self.selected_file_text.value = f"Selected: {file.name}"
            self.selected_file_text.color = ft.Colors.GREEN_600
            self.upload_button.disabled = False
        else:
            self.selected_file = None
            self.selected_file_text.value = "No file selected"
            self.selected_file_text.color = ft.Colors.GREY_600
            self.upload_button.disabled = True
        
        self.page.update()
    
    def upload_cv(self, e):
        """Handle CV upload and processing"""
        if not hasattr(self, 'selected_file') or not self.selected_file:
            return
        
        # Show progress
        self.progress_bar.visible = True
        self.upload_button.disabled = True
        self.upload_button.text = "Processing..."
        self.page.update()
        
        try:
            # Process the CV file
            applicant_id = self.cv_processor.process_cv_file(
                self.selected_file.path,
                self.selected_file.name
            )
            
            if applicant_id:
                # Success
                self.on_upload_callback(True, f"CV uploaded successfully! ID: {applicant_id}. Text extracted and saved.")
                self.reset_form()
            else:
                # Failed
                self.on_upload_callback(False, "Failed to process CV file")
                self.reset_upload_button()
                
        except Exception as ex:
            self.on_upload_callback(False, f"Error: {str(ex)}")
            self.reset_upload_button()
        
        finally:
            self.progress_bar.visible = False
            self.page.update()
    
    def reset_form(self):
        """Reset form after successful upload"""
        self.selected_file = None
        self.selected_file_text.value = "No file selected"
        self.selected_file_text.color = ft.Colors.GREY_600
        self.upload_button.disabled = True
        self.upload_button.text = "Upload CV"
    
    def reset_upload_button(self):
        """Reset upload button after failed upload"""
        self.upload_button.disabled = False
        self.upload_button.text = "Upload CV"
