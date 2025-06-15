import flet as ft
import threading
import time
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
            prefix_icon=ft.Icons.FILTER_LIST
        )

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

        # Multiprocessing toggle (placeholder for now)
        self.multiprocessing_toggle = ft.Switch(
            label="Use Multiprocessing",
            value=True,  # Default enabled
            on_change=self.on_multiprocessing_toggle
        )

        # Progress tracking components
        self.progress_bar = ft.ProgressBar(
            width=400,
            visible=False,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.BLUE_100
        )

        self.progress_text = ft.Text(
            value="",
            size=12,
            color=ft.Colors.GREY_600,
            visible=False
        )

    def on_threshold_change(self, e):
        """Handle threshold slider value change"""
        value = e.control.value
        self.threshold_label.value = f"Fuzzy Threshold: {value:.1f}"
        self.page.update()

    def on_multiprocessing_toggle(self, e):
        """Handle multiprocessing toggle change"""
        use_multiprocessing = e.control.value
        print(f"🔄 Multiprocessing toggle changed: {use_multiprocessing}")

        # Show feedback to user
        status = "enabled" if use_multiprocessing else "disabled"
        feedback_message = f"Multiprocessing {status} - will be used for searches with many applicants"
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(feedback_message),
            bgcolor=ft.Colors.GREEN_100 if use_multiprocessing else ft.Colors.GREY_100
        )
        self.page.snack_bar.open = True
        self.page.update()

    def update_progress(self, progress: float, message: str = ""):
        """Update progress bar and message"""
        self.progress_bar.value = progress / 100.0  # Convert percentage to decimal
        self.progress_text.value = f"{message} ({progress:.0f}%)"
        self.progress_bar.visible = True
        self.progress_text.visible = True
        self.page.update()

    def hide_progress(self):
        """Hide progress bar and message"""
        self.progress_bar.visible = False
        self.progress_text.visible = False
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
                        ]),
                        ft.Container(height=10),  # Spacing
                        ft.Row([
                            ft.Icon(ft.Icons.SPEED,
                                    color=ft.Colors.GREEN_600, size=20),
                            ft.Container(width=8),
                            ft.Container(
                                content=self.multiprocessing_toggle, expand=1),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Text(
                            "💡 Enable for faster search on multi-core systems",
                            size=11,
                            color=ft.Colors.GREY_600
                        )
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

                # Progress section
                ft.Container(
                    content=ft.Column([
                        self.progress_text,
                        self.progress_bar,
                    ], spacing=8),
                    margin=ft.Margin(0, 10, 0, 0),
                    alignment=ft.alignment.center
                ),

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
            border_radius=12,            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=6,
                color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_500),
                offset=ft.Offset(0, 2)
            )
        )

    def perform_search(self, e):
        """Perform CV search with progress tracking"""
        # Get search parameters
        keywords_text = self.keywords_field.value
        if not keywords_text or not keywords_text.strip():
            print("❌ Search Error: No keywords entered")
            self.show_error("Please enter search keywords")
            return

        # Parse keywords
        keywords = [kw.strip()
                    for kw in keywords_text.split(',') if kw.strip()]
        if not keywords:
            print("❌ Search Error: No valid keywords found")
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

        # Print search parameters to terminal
        fuzzy_threshold = self.fuzzy_threshold_slider.value
        print(f"\n🔍 Starting CV Search:")
        print(f"   Keywords: {', '.join(keywords)}")
        print(f"   Algorithm: {algorithm}")
        print(f"   Max Results: {max_results}")
        print(f"   Fuzzy Threshold: {fuzzy_threshold:.2f}")
        print(
            f"   Multiprocessing: {'Enabled' if self.multiprocessing_toggle.value else 'Disabled'}")

        # Disable search button during search
        self.search_button.disabled = True
        self.search_button.text = "Searching..."
        self.update_progress(0, "Initializing search...")
        self.page.update()

        # Run search in a separate thread to prevent UI blocking
        def run_search():
            try:
                print("🚀 Search thread started")

                # Perform search with real progress callback from search engine
                print("⚙️  Calling search engine with real progress tracking...")
                search_start_time = time.time()

                results = self.search_engine.search(
                    keywords=keywords,
                    algorithm=algorithm,
                    max_results=max_results,
                    fuzzy_threshold=fuzzy_threshold,
                    progress_callback=self.update_progress,  # Real progress from search engine
                    # Pass multiprocessing setting
                    use_multiprocessing=self.multiprocessing_toggle.value
                )

                search_duration = time.time() - search_start_time
                print(f"Search completed in {search_duration:.2f} seconds")
                print(f"Found {len(results.get('results', []))} results")

                # Final progress update (already done by search engine, but ensure 100%)
                self.update_progress(100, "Search completed!")

                # Call callback with results
                self.on_search_callback(results)

            except Exception as ex:
                print(f"[ERROR] Search error occurred: {str(ex)}")
                self.show_error(f"Search error: {str(ex)}")

            finally:
                # Re-enable search button and hide progress
                self.search_button.disabled = False
                self.search_button.text = "Search CVs"
                # Schedule hiding progress after a short delay to show completion

                def hide_progress_delayed():
                    time.sleep(1)
                    self.hide_progress()

                threading.Thread(target=hide_progress_delayed,
                                 daemon=True).start()
                self.page.update()

        # Start search thread
        search_thread = threading.Thread(target=run_search, daemon=True)
        search_thread.start()

    def clear_search(self, e):
        """Clear search form"""

        self.keywords_field.value = ""
        self.algorithm_dropdown.value = "KMP"
        self.max_results_field.value = "10"
        self.fuzzy_threshold_slider.value = 0.7
        self.multiprocessing_toggle.value = True  # Reset to default enabled

        # Update the threshold label when clearing
        self.threshold_label.value = f"Fuzzy Threshold: {0.7:.1f}"

        print("📝 Search form reset to defaults")
        # Clear results by calling callback with empty results
        print("🗑️  Clearing search results...")
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
        print("✨ Search form cleared successfully")

    def show_error(self, message: str):
        """Show error message"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error: {message}"),
            bgcolor=ft.Colors.RED_100
        )
        self.page.snack_bar.open = True
        self.page.update()

    def _start_progress_simulation(self):
        """Start simulated progress updates"""
        print("⏳ Starting progress simulation...")
        self._progress_stop_flag = False
        self._progress_thread = threading.Thread(
            target=self._simulate_progress, daemon=True)
        self._progress_thread.start()

    def _stop_progress_simulation(self):
        """Stop simulated progress updates"""
        print("⏹️  Stopping progress simulation...")
        self._progress_stop_flag = True

    def _simulate_progress(self):
        """Simulate search progress with realistic stages"""
        stages = [
            (10, "Loading applicant data..."),
            (25, "Processing CV fields..."),
            (40, "Computing search fields..."),
            (60, "Running search algorithm..."),
            (80, "Processing results..."),
            (95, "Ranking and filtering...")
        ]

        print("📈 Progress simulation running...")
        for progress, message in stages:
            if self._progress_stop_flag:
                print("🛑 Progress simulation stopped by flag")
                break
            print(f"   📊 {progress}%: {message}")
            self.update_progress(progress, message)
            time.sleep(0.5)  # Simulate processing time

        # Wait a bit more for actual search completion
        while not self._progress_stop_flag:
            time.sleep(0.1)
        print("✅ Progress simulation completed")
