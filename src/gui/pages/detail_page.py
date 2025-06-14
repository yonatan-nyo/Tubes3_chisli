import flet as ft
from typing import Callable
from database import Applicant
from gui.components.detail_view import DetailView


class DetailPage:
    """Applicant detail page"""

    def __init__(self, page: ft.Page, session_factory, on_back: Callable):
        self.page = page
        self.session_factory = session_factory
        self.on_back = on_back

        # Initialize detail view component
        self.detail_view = DetailView(self.page, self.on_back)

        # Current applicant
        self.current_applicant_id = None

    def build(self, applicant_id: int) -> ft.Control:
        """Build the detail page for a specific applicant"""
        self.current_applicant_id = applicant_id

        try:
            db = self.session_factory()
            try:
                applicant = db.query(Applicant).filter(
                    Applicant.id == applicant_id).first()
                if applicant:
                    applicant_data = applicant.to_dict()
                    return self.detail_view.build(applicant_data)
                else:
                    return self._build_not_found()
            finally:
                db.close()
        except Exception as e:
            return self._build_error(str(e))

    def _build_not_found(self) -> ft.Control:
        """Build not found view"""
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PERSON_OFF, size=60,
                            color=ft.Colors.GREY_400),
                    ft.Text("Applicant Not Found", size=24,
                            weight=ft.FontWeight.BOLD),
                    ft.Text("The requested applicant could not be found.",
                            size=16, color=ft.Colors.GREY_600),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Go Back",
                        on_click=lambda e: self.on_back(),
                        bgcolor=ft.Colors.BLUE_600,
                        color=ft.Colors.WHITE
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=50,
                alignment=ft.alignment.center
            )
        ], expand=True)

    def _build_error(self, error_message: str) -> ft.Control:
        """Build error view"""
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ERROR, size=60, color=ft.Colors.RED_400),
                    ft.Text("Error Loading Applicant", size=24,
                            weight=ft.FontWeight.BOLD),
                    ft.Text(f"Error: {error_message}",
                            size=16, color=ft.Colors.RED_600),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Go Back",
                        on_click=lambda e: self.on_back(),
                        bgcolor=ft.Colors.BLUE_600,
                        color=ft.Colors.WHITE
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=50,
                alignment=ft.alignment.center
            )
        ], expand=True)
