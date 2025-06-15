import flet as ft
import os
from typing import Callable, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models.applicant import ApplicantProfile, ApplicantDetail
from gui.components.detail_view import DetailView
from core.search_engine import SearchEngine
from utils.type_safety import (
    validate_applicant_data,
    safe_get_str,
    safe_get_list,
    format_datetime_safe,
    TypeSafetyError
)


class DetailPage:
    """Application detail page"""

    def __init__(self, page: ft.Page, session_factory: Callable[[], Session], on_back: Callable[[], None]):
        self.page: ft.Page = page
        self.session_factory: Callable[[], Session] = session_factory
        # Initialize detail view component
        self.on_back: Callable[[], None] = on_back
        self.detail_view: DetailView = DetailView(self.page, self.on_back)
        self.current_detail_id: Optional[int] = None
        # Initialize search engine for computing CV fields
        self.search_engine: SearchEngine = SearchEngine()

    def build(self, detail_id: int) -> ft.Control:
        """Build the detail page for a specific application"""
        self.current_detail_id = detail_id

        try:
            db: Session = self.session_factory()
            try:
                applicant_detail: Optional[ApplicantDetail] = db.query(ApplicantDetail).filter(
                    ApplicantDetail.detail_id == detail_id).first()

                if applicant_detail and applicant_detail.profile:
                    # Combine detail and profile data in the expected format
                    profile: ApplicantProfile = applicant_detail.profile

                    # Get decrypted profile data for display
                    display_profile = profile.get_display_data()

                    full_name: str = f"{display_profile.first_name or ''} {display_profile.last_name or ''}".strip(
                    )
                    if not full_name:
                        full_name = f"Applicant #{display_profile.applicant_id}"

                    # Parse JSON fields safely using the decrypted data                    # Create combined data dict using type-safe functions
                    applicant_data: Dict[str, Any] = {
                        'detail_id': applicant_detail.detail_id,
                        'applicant_id': applicant_detail.applicant_id,
                        'name': full_name,
                        'email': 'Not provided',  # Email removed from new schema
                        'phone': safe_get_str({'phone': display_profile.phone_number}, 'phone', 'Not provided'),                        'cv_path': safe_get_str({'path': applicant_detail.cv_path}, 'path', ''),
                        'application_role': safe_get_str({'role': applicant_detail.application_role}, 'role', 'Not specified'),                        'address': safe_get_str({'address': display_profile.address}, 'address', 'Not provided'),
                        'date_of_birth': format_datetime_safe(display_profile.date_of_birth, "%Y-%m-%d", 'Not provided')}

                    # Compute CV fields on demand using search engine
                    detail_with_computed = self.search_engine.get_applicant_details(
                        detail_id)
                    if detail_with_computed:
                        computed_fields = {
                            'extracted_text': safe_get_str(detail_with_computed, 'extracted_text', ''),
                            'summary': safe_get_str(detail_with_computed, 'summary', ''),
                            'skills': safe_get_list(detail_with_computed, 'skills', []),
                            'work_experience': safe_get_list(detail_with_computed, 'work_experience', []),
                            'education': safe_get_list(detail_with_computed, 'education', []),
                            'highlights': safe_get_list(detail_with_computed, 'highlights', []),
                            'accomplishments': safe_get_list(detail_with_computed, 'accomplishments', [])
                        }

                        # Merge computed fields
                        applicant_data.update(computed_fields)
                    else:
                        # Provide empty defaults
                        applicant_data.update({
                            'extracted_text': '',
                            'summary': '',
                            'skills': [],
                            'work_experience': [],
                            'education': [],
                            'highlights': [],
                            'accomplishments': []
                        })                    # Validate the data before passing to detail view
                    try:
                        validated_data = validate_applicant_data(
                            applicant_data)
                        return self.detail_view.build(validated_data.to_dict())
                    except TypeSafetyError as e:
                        print(f"Type safety error in applicant data: {e}")
                        return self._build_error(f"Data validation error: {str(e)}")
                else:
                    return self._build_not_found()
            finally:
                db.close()
        except Exception as e:
            print(f"Error in DetailPage.build: {e}")
            return self._build_error(str(e))

    def _build_not_found(self) -> ft.Control:
        """Build not found view"""
        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=60,
                            color=ft.Colors.GREY_400),
                    ft.Text("Application Not Found", size=24,
                            weight=ft.FontWeight.BOLD),
                    ft.Text("The requested application could not be found.",
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
