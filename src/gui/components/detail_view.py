import flet as ft
import os
import subprocess
import platform
from typing import Callable, Dict, List


class DetailView:
    """Detailed view for selected applicant"""

    def __init__(self, page: ft.Page, on_back_callback: Callable):
        self.page = page
        self.on_back_callback = on_back_callback

    def build(self, applicant_data: Dict) -> ft.Control:
        """Build detailed view for applicant"""
        return ft.Column([
            # Header with back button
            ft.Container(
                content=ft.Row([
                    ft.ElevatedButton(
                        "← Back to Results",
                        on_click=lambda e: self.on_back_callback()
                    ),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.ElevatedButton(
                            "View Full CV",
                            on_click=lambda e: self._open_cv_file(
                                applicant_data.get('cv_file_path', ''))
                        ),
                        ft.ElevatedButton(
                            "View Extracted Text",
                            on_click=lambda e: self._open_txt_file(
                                applicant_data.get('txt_file_path', ''))
                        )
                    ], spacing=10)
                ]),
                padding=20,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=10,
                margin=ft.Margin(0, 0, 0, 20)
            ),            # Main content - Vertical layout with scrolling
            ft.Container(
                content=ft.Column([
                    # Personal info and summary section
                    ft.Container(
                        content=self._build_personal_section(applicant_data),
                        padding=20,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        margin=ft.Margin(0, 0, 0, 20)
                    ),

                    # Skills, experience, education section
                    ft.Container(
                        content=self._build_details_section(applicant_data),
                        padding=20,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10
                    )
                ], scroll=ft.ScrollMode.AUTO, expand=True),
                expand=True
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    def _build_personal_section(self, applicant_data: Dict) -> ft.Control:
        """Build personal information section"""
        return ft.Column([
            # Profile header
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        applicant_data.get('name', 'Unknown'),
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        f"ID: {applicant_data.get('id', 'N/A')}",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=8,
                margin=ft.Margin(0, 0, 0, 20)
            ),

            # Contact information with file paths
            self._build_info_card("Contact Information", [
                ("Email", applicant_data.get('email', 'Not provided')),
                ("Phone", applicant_data.get('phone', 'Not provided')),
                ("CV Uploaded", applicant_data.get('created_at', 'Unknown')),
                ("PDF File", os.path.basename(
                    applicant_data.get('cv_file_path', 'N/A'))),
                ("TXT File", os.path.basename(
                    applicant_data.get('txt_file_path', 'N/A')))
            ]),

            ft.Container(height=20),

            # Summary section
            self._build_summary_card(applicant_data.get('summary', ''))
        ], spacing=0)

    def _build_details_section(self, applicant_data: Dict) -> ft.Control:
        """Build details section with skills, highlights, accomplishments, experience, education"""
        return ft.Column([
            # Skills section
            self._build_skills_section(applicant_data.get('skills', [])),

            ft.Container(height=20),

            # Highlights section
            self._build_highlights_section(
                applicant_data.get('highlights', [])),

            ft.Container(height=20),

            # Accomplishments section
            self._build_accomplishments_section(
                applicant_data.get('accomplishments', [])),

            ft.Container(height=20),

            # Work experience section
            self._build_work_experience_section(
                applicant_data.get('work_experience', [])),

            ft.Container(height=20),            # Education section
            self._build_education_section(applicant_data.get('education', []))
        ], scroll=ft.ScrollMode.AUTO)

    def _build_info_card(self, title: str, info_items: List[tuple]) -> ft.Control:
        """Build information card"""
        content = [ft.Text(title, size=16, weight=ft.FontWeight.BOLD)]

        for label, value in info_items:
            content.extend([
                ft.Container(height=8),
                ft.Column([
                    ft.Text(f"{label}:", weight=ft.FontWeight.W_500, size=12),
                    ft.Text(
                        str(value),
                        size=12,
                        no_wrap=False,  # Allow text wrapping
                        overflow=ft.TextOverflow.VISIBLE
                    )
                ], spacing=2)
            ])

        return ft.Container(
            content=ft.Column(content, spacing=5),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE
        )

    def _build_summary_card(self, summary: str) -> ft.Control:
        """Build summary card"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Summary", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Text(
                    summary if summary else "No summary available",
                    size=14,
                    color=ft.Colors.GREY_700 if summary else ft.Colors.GREY_500,
                    no_wrap=False,  # Allow text wrapping
                    overflow=ft.TextOverflow.VISIBLE
                )
            ], spacing=5),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE
        )

    def _build_skills_section(self, skills: List[str]) -> ft.Control:
        """Build skills section"""
        if not skills:
            content = ft.Text("No skills information available",
                              color=ft.Colors.GREY_500)
        else:
            # Create skill containers with blue background and white text
            skill_chips = [
                ft.Container(
                    content=ft.Text(
                        skill,
                        size=14,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_500
                    ),
                    padding=ft.Padding(12, 8, 12, 8),
                    bgcolor=ft.Colors.BLUE_800,
                    border_radius=20,
                    margin=ft.Margin(2, 2, 2, 2)
                )
                for skill in skills
            ]

            # Use a single Row with wrap=True for responsive layout
            content = ft.Row(
                controls=skill_chips,
                wrap=True,
                spacing=8,
                run_spacing=8  # Vertical spacing between wrapped rows
            )

        return ft.Container(
            content=ft.Column([
                ft.Text("Skills", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                content
            ]),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE
        )

    def _build_work_experience_section(self, work_experience: List[Dict]) -> ft.Control:
        """Build work experience section"""
        if not work_experience:
            content = ft.Text(
                "No work experience information available", color=ft.Colors.GREY_500)
        else:
            exp_items = []
            for exp in work_experience:
                # Build the header with position and company
                position = exp.get('position', 'Unknown Position')
                company = exp.get('company', 'Unknown Company')
                start_date = exp.get('start_date', '')
                end_date = exp.get('end_date', '')

                # Create a more informative header
                header_text = f"{position}"
                if position != 'Not specified' and company:
                    header_text = f"{position} at {company}"
                elif company:
                    header_text = company

                exp_items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                header_text,
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                no_wrap=False,
                                overflow=ft.TextOverflow.VISIBLE
                            ),
                            ft.Text(
                                f"{start_date} - {end_date}" if start_date and end_date else
                                start_date if start_date else "Date not specified",
                                size=12,
                                color=ft.Colors.GREY_600
                            ),
                            ft.Container(height=5),
                            ft.Text(
                                exp.get('description', ''),
                                size=12,
                                color=ft.Colors.GREY_700,
                                no_wrap=False,
                                overflow=ft.TextOverflow.VISIBLE
                            ) if exp.get('description') else ft.Container()
                        ]),
                        padding=10,
                        margin=ft.Margin(0, 0, 0, 10),
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=6
                    )
                )

            content = ft.Column(exp_items)

        return ft.Container(
            content=ft.Column([
                ft.Text("Work Experience", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                content
            ]),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE
        )

    def _build_education_section(self, education: List[Dict]) -> ft.Control:
        """Build education section"""
        if not education:
            content = ft.Text(
                "No education information available", color=ft.Colors.GREY_500)
        else:
            edu_items = []
            for edu in education:
                edu_items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                edu.get('degree', 'Unknown Degree'),
                                size=14,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                edu.get('institution', 'Unknown Institution'),
                                size=12,
                                color=ft.Colors.BLUE_700
                            ),
                            ft.Row([
                                ft.Text(
                                    f"Graduated: {edu.get('graduation_year', 'Unknown')}",
                                    size=12,
                                    color=ft.Colors.GREY_600
                                ),
                                ft.Text(
                                    f"GPA: {edu.get('gpa', 'N/A')}",
                                    size=12,
                                    color=ft.Colors.GREY_600
                                ) if edu.get('gpa') else ft.Container()
                            ])
                        ]),
                        padding=10,
                        margin=ft.Margin(0, 0, 0, 10),
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=6
                    )
                )

            content = ft.Column(edu_items)

        return ft.Container(
            content=ft.Column([
                ft.Text("Education", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                content
            ]),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE
        )

    def _build_highlights_section(self, highlights: List[str]) -> ft.Control:
        """Build highlights section"""
        if not highlights:
            content = ft.Text(
                "No highlights information available", color=ft.Colors.GREY_500)
        else:
            highlight_items = []
            for highlight in highlights:
                highlight_items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.STAR,
                                    color=ft.Colors.AMBER, size=16),
                            ft.Container(width=8),
                            ft.Text(
                                highlight,
                                size=12,
                                color=ft.Colors.GREY_700,
                                no_wrap=False,
                                overflow=ft.TextOverflow.VISIBLE,
                                expand=True
                            )
                        ]),
                        padding=ft.Padding(5, 5, 5, 5),
                        margin=ft.Margin(0, 0, 0, 5),
                        bgcolor=ft.Colors.AMBER_50,
                        border_radius=4
                    )
                )
            content = ft.Column(highlight_items)

        return ft.Container(
            content=ft.Column([
                ft.Text("Highlights", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                content
            ]),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE
        )

    def _build_accomplishments_section(self, accomplishments: List[str]) -> ft.Control:
        """Build accomplishments section"""
        if not accomplishments:
            content = ft.Text(
                "No accomplishments information available", color=ft.Colors.GREY_500)
        else:
            accomplishment_items = []
            for accomplishment in accomplishments:
                accomplishment_items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.EMOJI_EVENTS,
                                    color=ft.Colors.GREEN, size=16),
                            ft.Container(width=8),
                            ft.Text(
                                accomplishment,
                                size=12,
                                color=ft.Colors.GREY_700,
                                no_wrap=False,
                                overflow=ft.TextOverflow.VISIBLE,
                                expand=True
                            )
                        ]),
                        padding=ft.Padding(5, 5, 5, 5),
                        margin=ft.Margin(0, 0, 0, 5),
                        bgcolor=ft.Colors.GREEN_50,
                        border_radius=4
                    )
                )
            content = ft.Column(accomplishment_items)

        return ft.Container(
            content=ft.Column([
                ft.Text("Accomplishments", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                content
            ]),
            padding=15,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE
        )

    def _open_cv_file(self, file_path: str):
        """Open CV file with default system application"""
        if not file_path or not os.path.exists(file_path):
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("CV file not found"),
                bgcolor=ft.Colors.RED_100
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error opening CV file: {str(e)}"),
                bgcolor=ft.Colors.RED_100
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _open_txt_file(self, file_path: str):
        """Open extracted text file with default system application"""
        if not file_path or not os.path.exists(file_path):
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Extracted text file not found"),
                bgcolor=ft.Colors.RED_100
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error opening text file: {str(e)}"),
                bgcolor=ft.Colors.RED_100
            )
            self.page.snack_bar.open = True
            self.page.update()
