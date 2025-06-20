import flet as ft
from typing import Callable, Dict, Optional
from database.models.applicant import ApplicantProfile, ApplicantDetail
from gui.components.upload_section import UploadSection


class ApplicationsPage:
    """Applications management page for CV uploads and application details"""

    def __init__(self, page: ft.Page, session_factory, cv_processor, on_view_detail: Callable):
        self.page = page
        self.session_factory = session_factory
        self.cv_processor = cv_processor
        self.on_view_detail = on_view_detail

        # State
        self.selected_applicant_id = None
        self.applicant_profiles = []

        # Pagination state
        self.current_page = 1
        self.items_per_page = 10
        self.total_applications = 0
        self.total_pages = 0

        # UI component references for dynamic updates
        self.applications_list_container = None
        self.applicant_dropdown = None
        self.pagination_info = None
        self.prev_button = None
        self.next_button = None
        self.page_input = None

        # Initialize upload section
        self.upload_section = UploadSection(
            self.page, self.cv_processor, self.on_cv_uploaded, self.get_selected_applicant_id
        )

        # Callback for when upload completes
        self.on_upload_callback = None

    def set_upload_callback(self, callback: Callable):
        """Set callback for upload completion"""
        self.on_upload_callback = callback

    def build(self) -> ft.Control:
        """Build the applications management page"""
        # Initialize pagination components
        self.pagination_info = ft.Text("", size=12, color=ft.Colors.GREY_600)
        self.prev_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            on_click=self._on_prev_page,
            disabled=True
        )
        self.next_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            on_click=self._on_next_page,
            disabled=True
        )
        self.page_input = ft.TextField(
            label="Page",
            width=80,
            text_align=ft.TextAlign.CENTER,
            on_submit=self._on_page_input_submit,
            input_filter=ft.NumbersOnlyInputFilter()
        )

        # Create the applications list container
        self.applications_list_container = ft.Container(
            content=self._build_applications_list(),
            expand=True,
            padding=20,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            margin=ft.Margin(20, 0, 0, 0),
            height=600
        )

        return ft.Column([
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Text("Application Management", size=24,
                            weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.START),
                padding=10,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.only(
                    bottom=ft.BorderSide(1, ft.Colors.GREY_300))
            ),

            # Content
            ft.Container(
                content=ft.Row([
                    # Upload section and applicant selector
                    ft.Container(
                        content=ft.Column([
                            self._build_applicant_selector(),
                            ft.Divider(height=20),
                            self.upload_section.build()
                        ], scroll=ft.ScrollMode.AUTO),
                        width=400,
                        padding=20,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        height=600),

                    # Applications list with pagination
                    ft.Column([
                        self.applications_list_container,
                        self._build_pagination_controls()
                    ], expand=True)
                ], expand=True),
                padding=10,
                expand=True
            )], expand=True, scroll=ft.ScrollMode.AUTO)

    def _build_applicant_selector(self) -> ft.Control:
        """Build applicant selection dropdown"""
        self._load_applicant_profiles()

        options = [
            ft.dropdown.Option(key="random", text="Random Applicant"),
        ]

        for profile in self.applicant_profiles:
            # Get decrypted data for display
            display_profile = profile.get_display_data()
            full_name = f"{display_profile.first_name or ''} {display_profile.last_name or ''}".strip(
            )
            if not full_name:
                full_name = f"Applicant #{display_profile.applicant_id}"
            options.append(
                ft.dropdown.Option(
                    # Use original profile for ID
                    key=str(profile.applicant_id),
                    text=full_name
                )
            )

        self.applicant_dropdown = ft.Dropdown(
            label="Choose applicant for new application",
            options=options,
            on_change=self._on_applicant_selected,
            width=350
        )

        return ft.Column([
            ft.Text("Select Applicant", size=16, weight=ft.FontWeight.BOLD),
            self.applicant_dropdown,
        ], spacing=10)

    def _build_applications_list(self) -> ft.Control:
        """Build the list of applications (ApplicantDetail records) with pagination"""
        try:
            db = self.session_factory()
            try:
                # Get total count for pagination
                self.total_applications = db.query(ApplicantDetail).count()
                self.total_pages = max(
                    1, (self.total_applications + self.items_per_page - 1) // self.items_per_page)

                # Ensure current page is within bounds
                self.current_page = max(
                    1, min(self.current_page, self.total_pages))

                # Calculate offset for pagination
                offset = (self.current_page - 1) * self.items_per_page

                # Get paginated applications
                applications = db.query(ApplicantDetail).join(ApplicantProfile).order_by(
                    ApplicantDetail.detail_id.desc()).offset(offset).limit(self.items_per_page).all()

                # Update pagination info
                self._update_pagination_controls()

                if not applications:
                    if self.total_applications == 0:
                        return ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.FOLDER_OPEN, size=64,
                                        color=ft.Colors.GREY_400),
                                ft.Text("No applications found", size=16,
                                        color=ft.Colors.GREY_600),
                                ft.Text("Upload a CV to get started",
                                        size=14, color=ft.Colors.GREY_500),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center,
                            expand=True
                        )
                    else:
                        return ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.FOLDER_OPEN, size=64,
                                        color=ft.Colors.GREY_400),
                                ft.Text("No applications on this page", size=16,
                                        color=ft.Colors.GREY_600),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center,
                            expand=True
                        )

                return ft.Column([
                    ft.Row([
                        ft.Text("Applications", size=18,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Text(f"Total: {self.total_applications}",
                                size=14, color=ft.Colors.GREY_600)
                    ]),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column([
                            self._build_application_card(app) for app in applications
                        ], spacing=10, scroll=ft.ScrollMode.AUTO),
                        expand=True
                    )
                ], spacing=10, expand=True)

            finally:
                db.close()
        except Exception as e:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR, size=64, color=ft.Colors.RED_400),
                    ft.Text("Error loading applications",
                            size=16, color=ft.Colors.RED_600),
                    ft.Text(str(e), size=12, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )

    def _build_application_card(self, application: ApplicantDetail) -> ft.Control:
        """Build a card for an application"""        # Get applicant name
        applicant_name = "Unknown"
        if application.profile:
            # Get decrypted data for display
            display_profile = application.profile.get_display_data()
            full_name = f"{display_profile.first_name or ''} {display_profile.last_name or ''}".strip(
            )
            applicant_name = full_name if full_name else f"Applicant #{display_profile.applicant_id}"

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(applicant_name, size=16,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(application.application_role or "No role specified",
                                    size=14, color=ft.Colors.GREY_600),
                        ], expand=True),                        ft.Column([
                            ft.Text(f"ID: {application.detail_id}",
                                    size=12, color=ft.Colors.GREY_500),
                        ], horizontal_alignment=ft.CrossAxisAlignment.END),
                    ]),

                    ft.Row([
                        ft.ElevatedButton(
                            "View Details",
                            icon=ft.Icons.VISIBILITY,
                            on_click=lambda e, app_id=application.detail_id: self.on_view_detail(
                                app_id)
                        ),
                    ], alignment=ft.MainAxisAlignment.END)
                ], spacing=10),
                padding=15
            ),            elevation=2
        )

    def _load_applicant_profiles(self):
        """Load all applicant profiles for the dropdown"""
        try:
            db = self.session_factory()
            try:
                self.applicant_profiles = db.query(ApplicantProfile).order_by(
                    ApplicantProfile.first_name, ApplicantProfile.last_name
                ).all()
            finally:
                db.close()
        except Exception as e:
            print(f"Error loading applicant profiles: {e}")
            self.applicant_profiles = []

    def _on_applicant_selected(self, e):
        """Handle applicant selection from dropdown"""
        if e.control.value == "random":
            self.selected_applicant_id = None
        else:
            try:
                self.selected_applicant_id = int(e.control.value)
            except (ValueError, TypeError):
                self.selected_applicant_id = None

    def on_cv_uploaded(self, success: bool, message: str, applicant_data: Dict = None):
        """Handle CV upload completion"""
        if self.on_upload_callback:
            self.on_upload_callback(success, message)

        # Refresh the applications list
        if success:
            try:
                # Update the applications list content
                new_applications_content = self._build_applications_list()
                self.applications_list_container.content = new_applications_content

                # Also refresh the applicant dropdown in case new applicants were created
                self._refresh_applicant_dropdown()

                self.page.update()
            except Exception as e:
                print(f"Error refreshing applications list: {e}")

    def _refresh_applicant_dropdown(self):
        """Refresh the applicant dropdown with latest data"""
        try:
            self._load_applicant_profiles()

            # Rebuild dropdown options
            options = [
                ft.dropdown.Option(key="random", text="Random Applicant"),
            ]

            for profile in self.applicant_profiles:
                # Get decrypted data for display
                display_profile = profile.get_display_data()
                full_name = f"{display_profile.first_name or ''} {display_profile.last_name or ''}".strip(
                )
                if not full_name:
                    full_name = f"Applicant #{display_profile.applicant_id}"
                options.append(
                    ft.dropdown.Option(
                        # Use original profile for ID
                        key=str(profile.applicant_id),
                        text=full_name
                    )
                )

            # Update dropdown options
            if self.applicant_dropdown:
                self.applicant_dropdown.options = options

        except Exception as e:
            print(f"Error refreshing applicant dropdown: {e}")

    def get_selected_applicant_id(self) -> Optional[int]:
        """Get the currently selected applicant ID for CV upload"""
        return self.selected_applicant_id

    def refresh_applicant_dropdown(self):
        """Refresh the applicant dropdown with updated data"""
        try:
            if self.applicant_dropdown:
                self._load_applicant_profiles()

                options = [
                    ft.dropdown.Option(key="random", text="Random Applicant"),
                ]

                for profile in self.applicant_profiles:
                    # Get decrypted data for display
                    display_profile = profile.get_display_data()
                    full_name = f"{display_profile.first_name or ''} {display_profile.last_name or ''}".strip(
                    )
                    if not full_name:
                        full_name = f"Applicant #{display_profile.applicant_id}"
                    options.append(
                        ft.dropdown.Option(
                            # Use original profile for ID
                            key=str(profile.applicant_id),
                            text=full_name
                        )
                    )

                self.applicant_dropdown.options = options
                self.page.update()
        except Exception as e:
            print(f"Error refreshing applicant dropdown: {e}")

    def _build_pagination_controls(self) -> ft.Control:
        """Build pagination controls"""
        return ft.Container(
            content=ft.Row([
                self.prev_button,
                self.pagination_info,
                self.page_input,
                self.next_button,
                ft.Container(expand=True),
                ft.Dropdown(
                    label="Items per page",
                    value=str(self.items_per_page),
                    options=[
                        ft.dropdown.Option("5", "5"),
                        ft.dropdown.Option("10", "10"),
                        ft.dropdown.Option("20", "20"),
                        ft.dropdown.Option("50", "50")
                    ],
                    width=120,
                    on_change=self._on_items_per_page_change
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
            padding=10,
            border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300))
        )

    def _update_pagination_controls(self):
        """Update pagination control states"""
        if self.pagination_info:
            start_item = (self.current_page - 1) * self.items_per_page + 1
            end_item = min(self.current_page *
                           self.items_per_page, self.total_applications)
            self.pagination_info.value = f"Page {self.current_page} of {self.total_pages} ({start_item}-{end_item} of {self.total_applications})"

        if self.prev_button:
            self.prev_button.disabled = self.current_page <= 1

        if self.next_button:
            self.next_button.disabled = self.current_page >= self.total_pages

        if self.page_input:
            self.page_input.value = str(self.current_page)

    def _on_prev_page(self, e):
        """Handle previous page button click"""
        if self.current_page > 1:
            self.current_page -= 1
            self._refresh_applications_list()

    def _on_next_page(self, e):
        """Handle next page button click"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._refresh_applications_list()

    def _on_page_input_submit(self, e):
        """Handle page input submission"""
        try:
            page = int(self.page_input.value)
            if 1 <= page <= self.total_pages:
                self.current_page = page
                self._refresh_applications_list()
            else:
                self.page_input.value = str(self.current_page)
                self.page.update()
        except ValueError:
            self.page_input.value = str(self.current_page)
            self.page.update()

    def _on_items_per_page_change(self, e):
        """Handle items per page change"""
        self.items_per_page = int(e.control.value)
        self.current_page = 1  # Reset to first page
        self._refresh_applications_list()

    def _refresh_applications_list(self):
        """Refresh the applications list"""
        try:
            if self.applications_list_container:
                self.applications_list_container.content = self._build_applications_list()
                self.page.update()
        except Exception as e:
            print(f"Error refreshing applications list: {e}")
