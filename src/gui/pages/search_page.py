import flet as ft
from typing import Dict, Callable
from gui.components.search_section import SearchSection
from gui.components.results_section import ResultsSection


class SearchPage:
    """Search applicants page"""

    def __init__(self, page: ft.Page, search_engine, on_result_selected: Callable):
        self.page = page
        self.search_engine = search_engine
        self.on_result_selected = on_result_selected

        # Initialize search components
        self.search_section = SearchSection(
            self.page, self.search_engine, self.on_search_performed
        )
        self.results_section = ResultsSection(
            self.page, self.on_result_selected
        )

        # Search results
        self.search_results = []

    def build(self) -> ft.Control:
        """Build the search page"""
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.Text("Search Applicants", size=24,
                                weight=ft.FontWeight.BOLD),
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=30,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.only(
                        bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
                    width=None  # Take full width
                ),

                # Content
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=self.search_section.build(),
                            width=None,  # Take full width
                            expand=False
                        ),
                        ft.Divider(height=20),
                        ft.Container(
                            content=self.results_section.build(),
                            width=None,  # Take full width
                            expand=True,  # Expand to fill remaining space
                            alignment=ft.alignment.top_left  # Ensure proper alignment
                        )
                    ], scroll=ft.ScrollMode.AUTO, expand=True),
                    padding=30,
                    expand=True,
                    width=None  # Take full width of parent
                )
            ], expand=True, scroll=ft.ScrollMode.AUTO, width=None),
            expand=True,
            width=None  # Container takes full width
        )

    def on_search_performed(self, results: Dict):
        """Handle search completion"""
        self.search_results = results
        self.results_section.update_results(results)

    def get_search_results(self) -> Dict:
        """Get current search results"""
        return self.search_results
