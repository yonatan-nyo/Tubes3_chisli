import flet as ft
from typing import Callable
from database.models.applicant import ApplicantProfile
from datetime import datetime


class ApplicantsPage:
    """Applicants management page for creating and managing applicant profiles"""

    def __init__(self, page: ft.Page, session_factory, cv_processor, on_view_detail: Callable):
        self.page = page
        self.session_factory = session_factory
        self.cv_processor = cv_processor
        self.on_view_detail = on_view_detail

        # Pagination state
        self.current_page = 1
        self.items_per_page = 10
        self.total_applicants = 0
        self.total_pages = 0

        # Form fields
        self.first_name_field = ft.TextField(label="First Name", width=300)
        self.last_name_field = ft.TextField(label="Last Name", width=300)
        self.date_of_birth_field = ft.DatePicker(
            first_date=datetime(1900, 1, 1),
            last_date=datetime.now(),
            on_change=self._on_date_selected
        )
        self.date_display_field = ft.TextField(
            label="Date of Birth",
            width=300,
            read_only=True,
            suffix=ft.IconButton(
                icon=ft.Icons.CALENDAR_MONTH,
                on_click=self._open_date_picker
            )
        )
        self.address_field = ft.TextField(
            label="Address",
            width=300,
            multiline=True,
            min_lines=2,
            max_lines=4
        )
        self.phone_number_field = ft.TextField(label="Phone Number", width=300)
        self.on_applicant_created_callback = None

        # UI component references for dynamic updates
        self.applicants_list_container = None
        self.pagination_info = None
        self.prev_button = None
        self.next_button = None
        self.page_input = None

    def set_applicant_created_callback(self, callback: Callable):
        """Set callback for when applicant is created"""
        self.on_applicant_created_callback = callback

    def build(self) -> ft.Control:
        """Build the applicants management page"""
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

        # Create the applicants list container
        self.applicants_list_container = ft.Container(
            content=self._build_applicants_list(),
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
                    ft.Text("Applicant Management", size=24,
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
                    # Create applicant form
                    ft.Container(
                        content=ft.Column([
                            self._build_create_applicant_form()
                        ], scroll=ft.ScrollMode.AUTO),
                        width=400,
                        padding=20,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        height=600
                    ),

                    # Applicants list with pagination
                    ft.Column([
                        self.applicants_list_container,
                        self._build_pagination_controls()
                    ], expand=True)
                ], expand=True),
                padding=10,
                expand=True
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    def _build_create_applicant_form(self) -> ft.Control:
        """Build the create applicant form"""
        return ft.Column([
            ft.Text("Create New Applicant", size=18,
                    weight=ft.FontWeight.BOLD),
            ft.Divider(),            self.first_name_field,
            self.last_name_field,
            self.date_display_field,
            self.address_field,
            self.phone_number_field,

            ft.Container(height=20),  # Spacing

            ft.Row([
                ft.ElevatedButton(
                    "Create Applicant",
                    icon=ft.Icons.PERSON_ADD,
                    on_click=self._on_create_applicant,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_600,
                        color=ft.Colors.WHITE
                    )
                ),
                ft.TextButton(
                    "Clear Form",
                    on_click=self._on_clear_form
                )
            ], spacing=10),

        ], spacing=15)

    def _build_applicants_list(self) -> ft.Control:
        """Build the list of applicants with pagination"""
        try:
            db = self.session_factory()
            try:
                # Get total count for pagination
                self.total_applicants = db.query(ApplicantProfile).count()
                self.total_pages = max(
                    1, (self.total_applicants + self.items_per_page - 1) // self.items_per_page)

                # Ensure current page is within bounds
                self.current_page = max(
                    1, min(self.current_page, self.total_pages))

                # Calculate offset for pagination
                offset = (self.current_page - 1) * self.items_per_page

                # Get paginated applicants
                applicants = db.query(ApplicantProfile).order_by(
                    ApplicantProfile.first_name, ApplicantProfile.last_name).offset(offset).limit(self.items_per_page).all()

                # Update pagination info
                self._update_pagination_controls()

                if not applicants:
                    if self.total_applicants == 0:
                        return ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=64,
                                        color=ft.Colors.GREY_400),
                                ft.Text("No applicants found", size=16,
                                        color=ft.Colors.GREY_600),
                                ft.Text("Create a new applicant to get started",
                                        size=14, color=ft.Colors.GREY_500),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center,
                            expand=True
                        )
                    else:
                        return ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=64,
                                        color=ft.Colors.GREY_400),
                                ft.Text("No applicants on this page", size=16,
                                        color=ft.Colors.GREY_600),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            alignment=ft.alignment.center,
                            expand=True
                        )

                return ft.Column([
                    ft.Row([
                        ft.Text("Applicants", size=18,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Text(f"Total: {self.total_applicants}",
                                size=14, color=ft.Colors.GREY_600)
                    ]),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column([
                            self._create_applicant_card(applicant) for applicant in applicants
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
                    ft.Text("Error loading applicants",
                            size=16, color=ft.Colors.RED_600),
                    ft.Text(str(e), size=12, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )

    def _create_applicant_card(self, applicant: ApplicantProfile) -> ft.Control:
        """Create a card for an applicant"""
        # Get decrypted data for display
        display_applicant = applicant.get_display_data()

        full_name = f"{display_applicant.first_name or ''} {display_applicant.last_name or ''}".strip()
        if not full_name:
            full_name = f"Applicant #{display_applicant.applicant_id}"

        # Build address display
        address_display = []
        if display_applicant.address:
            address_display.append(
                ft.Text(display_applicant.address, size=12,
                        color=ft.Colors.GREY_600, max_lines=2)
            )

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(full_name, size=16,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(display_applicant.phone_number or "No phone",
                                    size=14, color=ft.Colors.GREY_600),
                        ], expand=True),
                        ft.Column([
                            ft.Text(f"ID: {display_applicant.applicant_id}",
                                    size=12, color=ft.Colors.GREY_500),
                            ft.Text(display_applicant.date_of_birth.strftime("%Y-%m-%d") if display_applicant.date_of_birth else "No DOB",
                                    size=12, color=ft.Colors.GREY_500),
                        ], horizontal_alignment=ft.CrossAxisAlignment.END),
                        # Address display (only if address exists)
                    ]),
                    *address_display
                ], spacing=10),
                padding=15
            ),
            elevation=2
        )

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
                           self.items_per_page, self.total_applicants)
            self.pagination_info.value = f"Page {self.current_page} of {self.total_pages} ({start_item}-{end_item} of {self.total_applicants})"

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
            self._refresh_applicants_list()

    def _on_next_page(self, e):
        """Handle next page button click"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._refresh_applicants_list()

    def _on_page_input_submit(self, e):
        """Handle page input submission"""
        try:
            page = int(self.page_input.value)
            if 1 <= page <= self.total_pages:
                self.current_page = page
                self._refresh_applicants_list()
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
        self._refresh_applicants_list()

    def _on_create_applicant(self, e):
        """Handle create applicant button click"""
        try:
            # Validate required fields
            if not self.first_name_field.value and not self.last_name_field.value:
                self._show_error(
                    "Please enter at least a first name or last name")
                return            # Parse date of birth
            date_of_birth = None
            if self.date_of_birth_field.value:
                date_of_birth = self.date_of_birth_field.value
            elif self.date_display_field.value:
                try:
                    date_of_birth = datetime.strptime(
                        self.date_display_field.value, "%Y-%m-%d").date()
                except ValueError:
                    self._show_error(
                        "Invalid date format. Please select a valid date")
                    return            # Create new applicant
            db = self.session_factory()
            try:
                # Create applicant with plain data first
                new_applicant = ApplicantProfile(
                    first_name=self.first_name_field.value.strip(
                    ) if self.first_name_field.value else None,
                    last_name=self.last_name_field.value.strip(
                    ) if self.last_name_field.value else None,
                    date_of_birth=date_of_birth,
                    address=self.address_field.value.strip() if self.address_field.value else None,
                    phone_number=self.phone_number_field.value.strip(
                    ) if self.phone_number_field.value else None,
                )                # Encrypt the sensitive data before saving to database
                encrypted_applicant = new_applicant.encrypt_data()
                db.add(encrypted_applicant)
                db.commit()
                db.refresh(encrypted_applicant)

                # Use the original (non-encrypted) data for display purposes
                full_name = f"{new_applicant.first_name or ''} {new_applicant.last_name or ''}".strip(
                )
                self._show_success(
                    f"Applicant '{full_name}' created successfully! (Data encrypted)")

                # Clear form
                self._clear_form()

                # Refresh the applicants list
                self._refresh_applicants_list()

                if self.on_applicant_created_callback:
                    self.on_applicant_created_callback(
                        True, f"Applicant created with ID: {encrypted_applicant.applicant_id}")

            finally:
                db.close()

        except Exception as ex:
            self._show_error(f"Error creating applicant: {str(ex)}")
            if self.on_applicant_created_callback:
                self.on_applicant_created_callback(False, str(ex))

    def _on_clear_form(self, e):
        """Handle clear form button click"""
        self._clear_form()

    def _clear_form(self):
        """Clear all form fields"""
        self.first_name_field.value = ""
        self.last_name_field.value = ""
        self.date_display_field.value = ""
        self.date_of_birth_field.value = None
        self.address_field.value = ""
        self.phone_number_field.value = ""

        self.page.update()

    def _refresh_applicants_list(self):
        """Refresh the applicants list"""
        try:
            if self.applicants_list_container:
                # Update the content of the applicants list container
                self.applicants_list_container.content = self._build_applicants_list()
                self.page.update()
        except Exception as e:
            print(f"Error refreshing applicants list: {e}")
            # Fallback to simple page update
            self.page.update()

    def _show_success(self, message: str):
        """Show success message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.GREEN_100
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _show_error(self, message: str):
        """Show error message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_100
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _open_date_picker(self, e):
        """Open the date picker"""
        self.page.overlay.append(self.date_of_birth_field)
        self.date_of_birth_field.open = True
        self.page.update()

    def _on_date_selected(self, e):
        """Handle date selection from date picker"""
        if self.date_of_birth_field.value:
            self.date_display_field.value = self.date_of_birth_field.value.strftime(
                "%Y-%m-%d")
            self.page.update()
