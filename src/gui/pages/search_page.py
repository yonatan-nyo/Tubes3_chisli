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
        return ft.Column([
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Text("Search Applicants", size=24,
                            weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.START),
                padding=30,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.only(
                    bottom=ft.BorderSide(1, ft.Colors.GREY_300))
            ),

            # Content
            ft.Container(
                content=ft.Column([
                    self.search_section.build(),
                    ft.Divider(height=20),
                    self.results_section.build()
                ], scroll=ft.ScrollMode.AUTO),
                padding=30,
                expand=True
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO)

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

    def get_search_results(self) -> Dict:
        """Get current search results"""
        return self.search_results
