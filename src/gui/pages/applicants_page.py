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
        self.on_view_detail = on_view_detail        # Form fields
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

    def set_applicant_created_callback(self, callback: Callable):
        """Set callback for when applicant is created"""
        self.on_applicant_created_callback = callback

    def build(self) -> ft.Control:
        """Build the applicants management page"""
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
                padding=30,
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

                    # Applicants list
                    self.applicants_list_container
                ], expand=True),
                padding=30,
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
        """Build the list of applicants"""
        try:
            db = self.session_factory()
            try:
                applicants = db.query(ApplicantProfile).order_by(
                    ApplicantProfile.first_name, ApplicantProfile.last_name).all()

                if not applicants:
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

                return ft.Column([
                    ft.Text("Applicants", size=18, weight=ft.FontWeight.BOLD),
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
        full_name = f"{applicant.first_name or ''} {applicant.last_name or ''}".strip()
        if not full_name:
            full_name = f"Applicant #{applicant.applicant_id}"

        # Build address display
        address_display = []
        if applicant.address:
            address_display.append(
                ft.Text(applicant.address, size=12,
                        color=ft.Colors.GREY_600, max_lines=2)
            )

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Column([
                            ft.Text(full_name, size=16,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(applicant.phone_number or "No phone",
                                    size=14, color=ft.Colors.GREY_600),
                        ], expand=True),
                        ft.Column([
                            ft.Text(f"ID: {applicant.applicant_id}",
                                    size=12, color=ft.Colors.GREY_500),
                            ft.Text(applicant.date_of_birth.strftime("%Y-%m-%d") if applicant.date_of_birth else "No DOB",
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
                    return

            # Create new applicant
            db = self.session_factory()
            try:
                new_applicant = ApplicantProfile(
                    first_name=self.first_name_field.value.strip(
                    ) if self.first_name_field.value else None,
                    last_name=self.last_name_field.value.strip(
                    ) if self.last_name_field.value else None,
                    date_of_birth=date_of_birth,
                    address=self.address_field.value.strip() if self.address_field.value else None,
                    phone_number=self.phone_number_field.value.strip(
                    ) if self.phone_number_field.value else None,
                )

                db.add(new_applicant)
                db.commit()

                full_name = f"{new_applicant.first_name or ''} {new_applicant.last_name or ''}".strip(
                )
                self._show_success(
                    f"Applicant '{full_name}' created successfully!")

                # Clear form
                self._clear_form()

                # Refresh the applicants list
                self._refresh_applicants_list()

                if self.on_applicant_created_callback:
                    self.on_applicant_created_callback(
                        True, f"Applicant created with ID: {new_applicant.applicant_id}")

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
