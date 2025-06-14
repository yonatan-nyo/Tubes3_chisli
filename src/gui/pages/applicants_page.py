import flet as ft
from typing import Callable
from database import Applicant
from gui.components.upload_section import UploadSection


class ApplicantsPage:
    """Applicants management page"""

    def __init__(self, page: ft.Page, session_factory, cv_processor, on_view_detail: Callable):
        self.page = page
        self.session_factory = session_factory
        self.cv_processor = cv_processor
        self.on_view_detail = on_view_detail

        # Initialize upload section
        self.upload_section = UploadSection(
            self.page, self.cv_processor, self.on_cv_uploaded
        )

        # Callback for when upload completes
        self.on_upload_callback = None

    def set_upload_callback(self, callback: Callable):
        """Set callback for upload completion"""
        self.on_upload_callback = callback

    def build(self) -> ft.Control:
        """Build the applicants management page"""
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
                    # Upload section
                    ft.Container(
                        content=ft.Column([
                            self.upload_section.build()
                        ], scroll=ft.ScrollMode.AUTO),
                        width=400,
                        padding=20,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        height=600
                    ),

                    # Applicants list
                    ft.Container(
                        content=self._build_applicants_list(),
                        expand=True,
                        padding=20,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        margin=ft.Margin(20, 0, 0, 0),
                        height=600
                    )
                ], expand=True),
                padding=30,
                expand=True
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    def _build_applicants_list(self) -> ft.Control:
        """Build the list of applicants"""
        try:
            db = self.session_factory()
            try:
                applicants = db.query(Applicant).order_by(
                    Applicant.created_at.desc()).all()

                if not applicants:
                    return ft.Column([
                        ft.Text("All Applicants", size=18,
                                weight=ft.FontWeight.BOLD),
                        ft.Divider(height=20),
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.Icons.PEOPLE_OUTLINE,
                                        size=60, color=ft.Colors.GREY_400),
                                ft.Text("No applicants found", size=16,
                                        color=ft.Colors.GREY_600),
                                ft.Text("Upload CV files to add applicants",
                                        size=14, color=ft.Colors.GREY_500),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                            padding=50,
                            alignment=ft.alignment.center
                        )
                    ], scroll=ft.ScrollMode.AUTO)

                applicant_cards = []
                for applicant in applicants:
                    card = self._create_applicant_card(applicant)
                    applicant_cards.append(card)

                return ft.Column([
                    ft.Row([
                        ft.Text("All Applicants", size=18,
                                weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        ft.Text(f"{len(applicants)} applicants",
                                size=14, color=ft.Colors.GREY_600)
                    ]),
                    ft.Divider(height=20),
                    ft.Column(applicant_cards,
                              scroll=ft.ScrollMode.AUTO, spacing=10)
                ], scroll=ft.ScrollMode.AUTO)

            finally:
                db.close()
        except Exception as e:
            print(f"Error loading applicants: {e}")
            return ft.Column([
                ft.Text("Error loading applicants",
                        size=16, color=ft.Colors.RED),
                ft.Text(f"Details: {str(e)}", size=12,
                        color=ft.Colors.GREY_600)
            ])

    def _create_applicant_card(self, applicant: Applicant) -> ft.Control:
        """Create a card for an applicant"""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE_600),
                    ft.Column([
                        ft.Text(applicant.name or "Unknown",
                                size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(applicant.email or "No email",
                                size=12, color=ft.Colors.GREY_600),
                    ], spacing=2, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.ARROW_FORWARD_IOS,
                        icon_size=16,
                        on_click=lambda e, aid=applicant.id: self.on_view_detail(
                            aid)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text(f"Phone: {applicant.phone or 'N/A'}",
                            size=12, color=ft.Colors.GREY_600),
                    ft.Container(expand=True),
                    ft.Text(f"Added: {applicant.created_at.strftime('%Y-%m-%d') if applicant.created_at else 'Unknown'}",
                            size=10, color=ft.Colors.GREY_500)
                ])
            ], spacing=8),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE,
            on_click=lambda e, aid=applicant.id: self.on_view_detail(aid),
            ink=True
        )

    def on_cv_uploaded(self, success: bool, message: str):
        """Handle CV upload completion"""
        if success and self.on_upload_callback:
            self.on_upload_callback(success, message)

    def refresh(self):
        """Refresh the applicants list"""
        # This would be called to refresh the page content
        pass
