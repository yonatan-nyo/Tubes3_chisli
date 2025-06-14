import flet as ft
from typing import Callable


class SearchSection:
    """Search section component"""

    def __init__(self, page: ft.Page, search_engine, on_search_callback: Callable):
        self.page = page
        self.search_engine = search_engine
        self.on_search_callback = on_search_callback
        # UI components with improved styling
        self.keywords_field = ft.TextField(
            label="Search Keywords",
            hint_text="Enter keywords separated by commas (e.g., Python, Java, Machine Learning)",
            multiline=True,
            max_lines=3,
            border_color=ft.Colors.BLUE_200,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
            prefix_icon=ft.Icons.SEARCH
        )

        self.algorithm_dropdown = ft.Dropdown(
            label="Search Algorithm",
            border_color=ft.Colors.BLUE_200,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
            options=[
                ft.dropdown.Option("KMP", "Knuth-Morris-Pratt (KMP)"),
                ft.dropdown.Option("BM", "Boyer-Moore (BM)"),
                ft.dropdown.Option("AC", "Aho-Corasick (AC)")
            ],
            value="KMP"
        )

        self.max_results_field = ft.TextField(
            label="Max Results",
            width=150,
            value="10",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=ft.Colors.BLUE_200,
            focused_border_color=ft.Colors.BLUE_600,
            border_radius=10,
            prefix_icon=ft.Icons.FILTER_LIST)

        # Create threshold label text component
        self.threshold_label = ft.Text(f"Fuzzy Threshold: {0.7:.1f}", size=14)

        self.fuzzy_threshold_slider = ft.Slider(
            min=0.1,
            max=1.0,
            value=0.7,
            divisions=9,
            width=300,
            on_change=self.on_threshold_change
        )

        self.search_button = ft.ElevatedButton(
            "Search CVs",
            on_click=self.perform_search,
            width=160,
            height=40,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                elevation={"default": 2, "hovered": 4}
            ),
            icon=ft.Icons.SEARCH
        )

        self.clear_button = ft.TextButton(
            "Clear",
            on_click=self.clear_search,
            width=100,
            height=40,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                color=ft.Colors.GREY_600
            ),
            icon=ft.Icons.CLEAR
        )

    def on_threshold_change(self, e):
        """Handle threshold slider value change"""
        value = e.control.value
        self.threshold_label.value = f"Fuzzy Threshold: {value:.1f}"
        self.page.update()

    def build(self) -> ft.Control:
        """Build search section UI with improved modern design"""
        return ft.Container(
            content=ft.Column([
                # Modern header with icon
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.MANAGE_SEARCH,
                                color=ft.Colors.BLUE_600, size=24),
                        ft.Text(
                            "Search CVs", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(0, 0, 0, 15)
                ),

                # Keywords input section
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Keywords", size=14, weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                        self.keywords_field,
                    ], spacing=8),
                    margin=ft.Margin(0, 0, 0, 20)
                ),

                # Search options in a card
                ft.Container(
                    content=ft.Column([
                        ft.Text("Search Options", size=14,
                                weight=ft.FontWeight.W_500, color=ft.Colors.GREY_700),
                        ft.Row([
                            ft.Container(
                                content=self.algorithm_dropdown, expand=2),
                            ft.Container(width=15),
                            ft.Container(
                                content=self.max_results_field, expand=1)
                        ])
                    ], spacing=10),
                    padding=15,
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    margin=ft.Margin(0, 0, 0, 20)
                ),

                # Fuzzy matching section
                ft.Container(
                    content=ft.Column([
                        self.threshold_label,
                        self.fuzzy_threshold_slider,
                        ft.Text(
                            "💡 Higher values = more strict matching",
                            size=12,
                            color=ft.Colors.GREY_600
                        )
                    ], spacing=8),
                    padding=15,
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.BLUE_200),
                    margin=ft.Margin(0, 0, 0, 20)
                ),

                # Action buttons
                ft.Row([
                    self.search_button,
                    ft.Container(width=10),
                    self.clear_button
                ], alignment=ft.MainAxisAlignment.CENTER),

                # Algorithm info card
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE,
                                    color=ft.Colors.AMBER_700, size=20),
                            ft.Text("Algorithm Information", weight=ft.FontWeight.BOLD,
                                    size=14, color=ft.Colors.AMBER_800),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Divider(height=10, color=ft.Colors.AMBER_200),
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.CIRCLE,
                                        color=ft.Colors.GREEN_600, size=8),
                                ft.Text("KMP: Good for single pattern matching",
                                        size=12, color=ft.Colors.GREY_700),
                            ], spacing=8),
                            ft.Row([
                                ft.Icon(ft.Icons.CIRCLE,
                                        color=ft.Colors.BLUE_600, size=8),
                                ft.Text(
                                    "Boyer-Moore: Efficient for longer patterns", size=12, color=ft.Colors.GREY_700),
                            ], spacing=8),
                            ft.Row([
                                ft.Icon(ft.Icons.CIRCLE,
                                        color=ft.Colors.PURPLE_600, size=8),
                                ft.Text(
                                    "Aho-Corasick: Best for multiple patterns (Bonus)", size=12, color=ft.Colors.GREY_700),
                            ], spacing=8),
                        ], spacing=6)
                    ], spacing=10),
                    padding=15,
                    bgcolor=ft.Colors.AMBER_50,
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.AMBER_200),
                    margin=ft.Margin(0, 20, 0, 0)
                )
            ], spacing=0),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=6,
                color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_500),
                offset=ft.Offset(0, 2)
            )
        )

    def perform_search(self, e):
        """Perform CV search"""
        # Get search parameters
        keywords_text = self.keywords_field.value
        if not keywords_text or not keywords_text.strip():
            self.show_error("Please enter search keywords")
            return

        # Parse keywords
        keywords = [kw.strip()
                    for kw in keywords_text.split(',') if kw.strip()]
        if not keywords:
            self.show_error("Please enter valid keywords")
            return

        # Get other parameters
        algorithm = self.algorithm_dropdown.value or "KMP"

        try:
            max_results = int(self.max_results_field.value or "10")
            if max_results <= 0:
                max_results = 10
        except ValueError:
            max_results = 10

        fuzzy_threshold = self.fuzzy_threshold_slider.value

        # Disable search button during search
        self.search_button.disabled = True
        self.search_button.text = "Searching..."
        self.page.update()

        try:
            # Perform search
            results = self.search_engine.search(
                keywords=keywords,
                algorithm=algorithm,
                max_results=max_results,
                fuzzy_threshold=fuzzy_threshold
            )

            # Call callback with results
            self.on_search_callback(results)

        except Exception as ex:
            self.show_error(f"Search error: {str(ex)}")

        finally:
            # Re-enable search button
            self.search_button.disabled = False
            self.search_button.text = "Search CVs"
            self.page.update()

    def clear_search(self, e):
        """Clear search form"""
        self.keywords_field.value = ""
        self.algorithm_dropdown.value = "KMP"
        self.max_results_field.value = "10"
        self.fuzzy_threshold_slider.value = 0.7

        # Update the threshold label when clearing
        self.threshold_label.value = f"Fuzzy Threshold: {0.7:.1f}"

        # Clear results by calling callback with empty results
        empty_results = {
            'results': [],
            'exact_match_time': 0,
            'fuzzy_match_time': 0,
            'total_time': 0,
            'algorithm_used': 'KMP',
            'keywords_searched': []
        }
        self.on_search_callback(empty_results)

        self.page.update()

    def show_error(self, message: str):
        """Show error message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error: {message}"),
            bgcolor=ft.Colors.RED_100
        )
        self.page.snack_bar.open = True
        self.page.update()
