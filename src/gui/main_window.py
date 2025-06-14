import flet as ft
from typing import Dict, List, Callable, Optional, Any
from gui.pages.applicants_page import ApplicantsPage
from gui.pages.applications_page import ApplicationsPage
from gui.pages.search_page import SearchPage
from gui.pages.detail_page import DetailPage
from database.models.applicant import ApplicantProfile


class MainWindow:
    """Main window for CV matching application with multipage navigation and type safety"""

    def __init__(self, page: ft.Page, session_factory: Callable, cv_processor: Any, search_engine: Any):
        self.page: ft.Page = page
        self.session_factory: Callable = session_factory
        self.cv_processor: Any = cv_processor
        self.search_engine: Any = search_engine

        # Initialize page classes
        try:
            self.applicants_page: ApplicantsPage = ApplicantsPage(
                self.page, self.session_factory, self.cv_processor, self._view_applicant_detail
            )
            self.applications_page: ApplicationsPage = ApplicationsPage(
                self.page, self.session_factory, self.cv_processor, self._view_application_detail
            )
            self.search_page: SearchPage = SearchPage(
                self.page, self.search_engine, self.on_result_selected
            )
            self.detail_page: DetailPage = DetailPage(
                self.page, self.session_factory, self.on_back_to_results
            )

            # Set upload callback for applications page
            self.applications_page.set_upload_callback(self.on_cv_uploaded)

            # Set callback for applicant creation to refresh applications dropdown
            self.applicants_page.set_applicant_created_callback(
                self.on_applicant_created)

        except Exception as e:
            print(f"Error initializing page components: {e}")
            self.components_initialized = False
        else:
            self.components_initialized = True

        # Navigation state
        self.current_page: str = "applicants"
        self.current_view: str = "main"  # main, detail
        self.search_results: List[Dict[str, Any]] = []
        self.selected_applicant_id: Optional[int] = None
        self.selected_application_id: Optional[int] = None

        # UI components
        self.content_area: ft.Container = ft.Container(expand=True)
        self.sidebar_container = ft.Container()
        # Check database connection on startup
        self.sidebar_container = ft.Container()
        self._check_database_connection()

    def _check_database_connection(self):
        """Check if database connection is working"""
        try:
            db = self.session_factory()
            db.query(ApplicantProfile).first()
            db.close()
            print("Database connection verified")
        except Exception as e:
            print(f"Database connection failed: {e}")

    def build(self) -> ft.Control:
        """Build the main window interface with sidebar navigation"""
        if not self.components_initialized:
            return self._build_error_view()        # Initialize content with the current page
        self._update_content()

        # Initialize sidebar
        self.sidebar_container = self._build_sidebar()

        return ft.Row([
            # Sidebar
            self.sidebar_container,
            # Main content area
            ft.Container(
                content=self.content_area,
                expand=True,
                padding=0
            )
        ], expand=True)

    def _build_sidebar(self) -> ft.Control:
        """Build the navigation sidebar"""
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Column([
                        ft.Text("CV Matching", size=20,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("System", size=16, color=ft.Colors.WHITE70),
                    ], spacing=5),
                    padding=ft.Padding(20, 30, 20, 20),
                    bgcolor=ft.Colors.BLUE_800,
                ),                # Navigation items
                ft.Container(
                    content=ft.Column([
                        self._create_nav_item(
                            "Applicants", ft.Icons.PEOPLE, "applicants"),
                        self._create_nav_item(
                            "Applications", ft.Icons.DESCRIPTION, "applications"),
                        self._create_nav_item(
                            "Search", ft.Icons.SEARCH, "search"),
                    ], spacing=5),
                    padding=ft.Padding(10, 20, 10, 20),
                ),                # Footer
                ft.Container(expand=True),
                ft.Container(
                    content=ft.Text(
                        "Tubes 3 - Stima",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=20,
                )
            ], expand=True),
            width=250,
            bgcolor=ft.Colors.GREY_100,
            border=ft.border.only(right=ft.BorderSide(1, ft.Colors.GREY_300))
        )

    def _create_nav_item(self, title: str, icon: str, page_key: str) -> ft.Control:
        """Create a navigation item"""
        is_selected = self.current_page == page_key

        return ft.Container(
            content=ft.Row([
                ft.Icon(
                    icon, color=ft.Colors.WHITE if is_selected else ft.Colors.GREY_700),
                ft.Text(title, color=ft.Colors.WHITE if is_selected else ft.Colors.GREY_700,
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL),], spacing=15),
            padding=ft.Padding(15, 12, 15, 12),
            bgcolor=ft.Colors.BLUE_600 if is_selected else ft.Colors.TRANSPARENT,
            border_radius=8,
            on_click=lambda e, page=page_key: self._navigate_to_page(page),
            ink=True
        )

    def _navigate_to_page(self, page_key: str):
        """Navigate to a specific page"""
        if page_key == self.current_page:
            return

        self.current_page = page_key
        self.current_view = "main"
        self._update_content()
        self._update_sidebar()  # Refresh sidebar to update highlighting
        self.page.update()

    def _update_content(self):
        """Update the main content area based on current page and view"""
        if self.current_view == "detail" and (self.selected_applicant_id or self.selected_application_id):
            detail_id = self.selected_application_id or self.selected_applicant_id
            content = self.detail_page.build(detail_id)
        elif self.current_page == "applicants":
            content = self.applicants_page.build()
        elif self.current_page == "applications":
            content = self.applications_page.build()
        elif self.current_page == "search":
            content = self.search_page.build()
        else:
            content = self.applicants_page.build()

        self.content_area.content = content

    def _view_applicant_detail(self, applicant_id: int):
        """View applicant detail"""
        self.selected_applicant_id = applicant_id
        self.current_view = "detail"
        self._update_content()
        self.page.update()

    def _view_application_detail(self, application_id: int):
        """View application detail"""
        self.selected_application_id = application_id
        self.current_view = "detail"
        self._update_content()
        self.page.update()

    def on_cv_uploaded(self, success: bool, message: str):
        """Handle CV upload completion"""
        if success:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Success: {message}"),
                bgcolor=ft.Colors.GREEN_100
            )
            # Refresh current page content
            self._update_content()
        else:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {message}"),
                bgcolor=ft.Colors.RED_100
            )
        self.page.snack_bar.open = True
        self.page.update()
        self.page.update()

    def on_search_performed(self, results: Dict):
        """Handle search completion - delegated to search page"""
        if hasattr(self, 'search_page'):
            self.search_page.on_search_performed(results)

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
    #         )    #         self.page.snack_bar.open = True
    #         self.page.update()
    #         print(f"Error loading applicant details: {e}") # Keep console log

    def on_result_selected(self, applicant_id: int):
        """Handle result selection"""
        self.selected_applicant_id = applicant_id
        self.current_view = "detail"
        self._update_content()
        self.page.update()

    def on_back_to_results(self):
        """Handle back button from detail view"""
        self.current_view = "main"
        self._update_content()
        self.page.update()

    def on_applicant_created(self, success: bool, message: str):
        """Handle applicant creation completion"""
        if success:
            # Refresh applications page dropdown if it exists
            if hasattr(self.applications_page, '_refresh_applicant_dropdown'):
                self.applications_page._refresh_applicant_dropdown()

            # Refresh current page content
            self._update_content()

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

    def _build_error_view(self) -> ft.Control:
        """Build error view when components fail to initialize"""
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("Application Error", size=24,
                            weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Failed to initialize application components.", size=16),
                    ft.Text("Please check the console for error details.",
                            size=14, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=50,
                alignment=ft.alignment.center
            )
        ], expand=True)

    def _update_sidebar(self):
        """Update the sidebar to refresh navigation highlighting"""
        self.sidebar_container.content = self._build_sidebar().content
