import flet as ft
from typing import Dict
from gui.components.upload_section import UploadSection
from gui.components.search_section import SearchSection
from gui.components.results_section import ResultsSection
from gui.components.detail_view import DetailView
from database import Applicant

class MainWindow:
    """Main window for CV matching application"""
    
    def __init__(self, page: ft.Page, session_factory, cv_processor, search_engine):
        self.page = page
        self.session_factory = session_factory  # SQLAlchemy SessionLocal
        self.cv_processor = cv_processor
        self.search_engine = search_engine
        
        # Initialize components
        try:
            self.upload_section = UploadSection(self.page, self.cv_processor, self.on_cv_uploaded)
            self.search_section = SearchSection(self.page, self.search_engine, self.on_search_performed)
            self.results_section = ResultsSection(self.page, self.on_result_selected)
            self.detail_view = DetailView(self.page, self.on_back_to_results)
        except Exception as e:
            print(f"Error initializing components: {e}")
            # Create fallback UI if components fail
            self.components_initialized = False
        else:
            self.components_initialized = True
        
        # Current view state
        self.current_view = "main"
        self.search_results = []
        
        # Main container
        self.main_container = ft.Container()
        
        # Check database connection on startup
        self._check_database_connection()
    
    def _check_database_connection(self):
        """Check if database connection is working"""
        try:
            db = self.session_factory()
            db.query(Applicant).first()
            db.close()
            print("Database connection verified")
        except Exception as e:
            print(f"Database connection failed: {e}")

    def build(self) -> ft.Control:
        """Build the main window interface"""
        if not self.components_initialized:
            return self._build_error_view()
        return self._build_main_view()
    
    def _build_error_view(self) -> ft.Control:
        """Build error view when components fail to initialize"""
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("Application Error", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Failed to initialize application components.", size=16),
                    ft.Text("Please check the console for error details.", size=14, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=50,
                alignment=ft.alignment.center
            )
        ], expand=True)
    
    def _build_main_view(self) -> ft.Control:
        """Build the main view with upload and search"""
        return ft.Column([
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Text("CV Matching System", size=24, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=20,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=10,
                margin=ft.Margin(0, 0, 0, 20)
            ),
            
            # Main content - Make scrollable
            ft.Container(
                content=ft.Row([
                    # Left side - Upload section
                    ft.Container(
                        content=ft.Column([
                            self.upload_section.build()
                        ], scroll=ft.ScrollMode.AUTO),
                        width=400,
                        padding=20,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        height=600  # Fixed height to enable scrolling
                    ),
                    
                    # Right side - Search section and results
                    ft.Container(
                        content=ft.Column([
                            self.search_section.build(),
                            ft.Divider(height=20),
                            self.results_section.build()
                        ], scroll=ft.ScrollMode.AUTO),
                        expand=True,
                        padding=20,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        margin=ft.Margin(20, 0, 0, 0),
                        height=600  # Fixed height to enable scrolling
                    )
                ], expand=True, scroll=ft.ScrollMode.AUTO),
                expand=True
            ),
            
            # Footer
            ft.Container(
                content=ft.Text(
                    "CV Matching System - Tubes 3 Strategi dan Algoritma",
                    size=12,
                    color=ft.Colors.GREY_600
                ),
                alignment=ft.alignment.center,
                padding=10
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO)
    
    def _build_detail_view(self, applicant_data: Dict) -> ft.Control:
        """Build detailed view for selected applicant"""
        return self.detail_view.build(applicant_data)
    
    def on_cv_uploaded(self, success: bool, message: str):
        """Handle CV upload completion"""
        if success:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Success: {message}"),
                bgcolor=ft.Colors.GREEN_100
            )
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {message}"),
                bgcolor=ft.Colors.RED_100
            )
        self.page.snack_bar.open = True
        self.page.update()
    
    def on_search_performed(self, results: Dict):
        """Handle search completion"""
        self.search_results = results
        self.results_section.update_results(results)
        
        # Show search timing info
        timing_message = f"Search completed in {results['total_time']:.3f}s"
        if results['exact_match_time'] > 0:
            timing_message += f" (Exact: {results['exact_match_time']:.3f}s"
        if results['fuzzy_match_time'] > 0:
            timing_message += f", Fuzzy: {results['fuzzy_match_time']:.3f}s)"
        else:
            timing_message += ")"
        
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(timing_message),
            bgcolor=ft.Colors.BLUE_100
        )
        self.page.snack_bar.open = True
        self.page.update()
        
    # def on_result_selected(self, applicant_id: int):
    #     """Handle result selection"""
    #     try:
    #         db = self.session_factory()
    #         try:
    #             applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    #             if applicant:
    #                 applicant_data = applicant.to_dict()  # Ensure this method exists and works
                    
    #                 # Prepare the detail view content
    #                 detail_view_content = self.detail_view.build(applicant_data)
                    
    #                 self.current_view = "detail"
    #                 self.page.clean()  # Clear all existing content from the page
    #                 self.page.add(detail_view_content)  # Add the new detail view
    #                 self.page.update()
    #             else:
    #                 self.page.snack_bar = ft.SnackBar(
    #                     content=ft.Text(f"Applicant with ID {applicant_id} not found."),
    #                     bgcolor=ft.Colors.YELLOW_200
    #                 )
    #                 self.page.snack_bar.open = True
    #                 self.page.update()
    #                 print(f"Applicant with ID {applicant_id} not found") # Keep console log for debugging
    #         finally:
    #             db.close()
    #     except Exception as e:
    #         self.page.snack_bar = ft.SnackBar(
    #             content=ft.Text(f"Error loading applicant details: {str(e)}"),
    #             bgcolor=ft.Colors.RED_100
    #         )
    #         self.page.snack_bar.open = True
    #         self.page.update()
    #         print(f"Error loading applicant details: {e}") # Keep console log

    def on_result_selected(self, applicant_id: int):
        """Handle result selection"""
        try:
            db = self.session_factory()
            try:
                applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
                if applicant:
                    applicant_data = applicant.to_dict()

                    # <--- COMPREHENSIVE DEBUGGING BLOCK FOR ALL FIELDS --->
                    print("\n" + "="*25 + " DEBUG START " + "="*25)
                    print(f"--- All Data for Applicant ID: {applicant_data.get('id')} ---")

                    # --- Basic Information ---
                    print("\n[-- Personal Info --]")
                    print(f"  Name: {applicant_data.get('name')}")
                    print(f"  Email: {applicant_data.get('email')}")
                    print(f"  Phone: {applicant_data.get('phone')}")

                    # --- File Paths and Timestamps ---
                    print("\n[-- File & Time Info --]")
                    print(f"  CV File Path: {applicant_data.get('cv_file_path')}")
                    print(f"  TXT File Path: {applicant_data.get('txt_file_path')}")
                    print(f"  Created At: {applicant_data.get('created_at')}")
                    print(f"  Updated At: {applicant_data.get('updated_at')}")

                    # --- Skills (List) ---
                    print("\n[-- Skills --]")
                    skills_list = applicant_data.get('skills', [])
                    if skills_list:
                        for i, skill in enumerate(skills_list):
                            print(f"  - Skill #{i+1}: {skill}")
                    else:
                        print("  No skills listed.")

                    # --- Work Experience (List of Dictionaries) ---
                    print("\n[-- Work Experience --]")
                    work_experience_list = applicant_data.get('work_experience', [])
                    if work_experience_list:
                        for i, exp in enumerate(work_experience_list):
                            print(f"  - Experience #{i+1}:")
                            print(f"    Position: {exp.get('position')}")
                            print(f"    Company: {exp.get('company')}")
                            print(f"    Dates: {exp.get('start_date')} to {exp.get('end_date')}")
                            print(f"    Description: {exp.get('description', 'N/A')[:100]}...") # Truncated
                    else:
                        print("  No work experience listed.")

                    # --- Education (List of Dictionaries) ---
                    print("\n[-- Education --]")
                    education_list = applicant_data.get('education', [])
                    if education_list:
                        for i, edu in enumerate(education_list):
                            print(f"  - Education #{i+1}:")
                            print(f"    Degree: {edu.get('degree')}")
                            print(f"    Institution: {edu.get('institution')}")
                            print(f"    Year: {edu.get('graduation_year')}")
                            print(f"    GPA: {edu.get('gpa', 'N/A')}")
                    else:
                        print("  No education listed.")

                    # --- Summary (String) ---
                    print("\n[-- Summary --]")
                    summary = applicant_data.get('summary', '')
                    print(f"  {summary if summary else 'No summary available.'}")

                    # --- Full Extracted Text (String) ---
                    print("\n[-- Full Extracted Text (first 200 chars) --]")
                    extracted_text = applicant_data.get('extracted_text', '')
                    print(f"  {extracted_text[:200] if extracted_text else 'No extracted text.'}...")

                    print("\n" + "="*26 + " DEBUG END " + "="*26 + "\n")


                    # Prepare the detail view content
                    detail_view_content = self.detail_view.build(applicant_data)

                    self.current_view = "detail"
                    self.page.clean()  # Clear all existing content from the page
                    self.page.add(detail_view_content)  # Add the new detail view
                    self.page.update()
                else:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Applicant with ID {applicant_id} not found."),
                        bgcolor=ft.Colors.YELLOW_200
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                    print(f"Applicant with ID {applicant_id} not found") # Keep console log for debugging
            finally:
                db.close()
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error loading applicant details: {str(e)}"),
                bgcolor=ft.Colors.RED_100
            )
            self.page.snack_bar.open = True
            self.page.update()
            print(f"Error loading applicant details: {e}") # Keep console log

    def on_back_to_results(self):
        """Handle back button from detail view"""
        self.current_view = "main"
        main_view_content = self._build_main_view() # This builds your main layout
        
        self.page.clean()
        self.page.add(main_view_content)
        
        # Restore search results if they exist after the main view is added
        if hasattr(self, 'search_results') and self.search_results and self.components_initialized:
            # Assuming results_section is part of what _build_main_view recreates
            # You might need to access it through the newly built main_view_content if it's not directly self.results_section
            # For simplicity, if _build_main_view uses self.results_section directly, this is fine:
            self.results_section.update_results(self.search_results) 
        
        self.page.update()

