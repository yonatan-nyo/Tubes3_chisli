import flet as ft
from typing import Callable

class SearchSection:
    """Search section component"""
    
    def __init__(self, page: ft.Page, search_engine, on_search_callback: Callable):
        self.page = page
        self.search_engine = search_engine
        self.on_search_callback = on_search_callback
        
        # UI components
        self.keywords_field = ft.TextField(
            label="Search Keywords",
            hint_text="Enter keywords separated by commas (e.g., Python, Java, Machine Learning)",
            multiline=True,
            max_lines=3,
            width=400
        )
        
        self.algorithm_dropdown = ft.Dropdown(
            label="Search Algorithm",
            width=200,
            options=[
                ft.dropdown.Option("KMP", "Knuth-Morris-Pratt (KMP)"),
                ft.dropdown.Option("BM", "Boyer-Moore (BM)"),
                ft.dropdown.Option("AC", "Aho-Corasick (AC)")
            ],
            value="KMP"
        )
        
        self.max_results_field = ft.TextField(
            label="Max Results",
            width=120,
            value="10",
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.fuzzy_threshold_slider = ft.Slider(
            min=0.1,
            max=1.0,
            value=0.7,
            divisions=9,
            label="Fuzzy Threshold: {value}",
            width=300
        )
        
        self.search_button = ft.ElevatedButton(
            "Search CVs",
            on_click=self.perform_search,
            width=150
        )
        
        self.clear_button = ft.TextButton(
            "Clear",
            on_click=self.clear_search
        )
    
    def build(self) -> ft.Control:
        """Build search section UI"""
        return ft.Column([
            ft.Text("Search CVs", size=18, weight=ft.FontWeight.BOLD),
            ft.Divider(height=10),
            
            # Keywords input
            self.keywords_field,
            
            ft.Container(height=15),
            
            # Search options
            ft.Row([
                self.algorithm_dropdown,
                ft.Container(width=20),
                self.max_results_field
            ]),
            
            ft.Container(height=15),
            
            # Fuzzy matching threshold
            ft.Column([
                ft.Text("Fuzzy Matching Threshold", size=14, weight=ft.FontWeight.W_500),
                self.fuzzy_threshold_slider,
                ft.Text(
                    "Higher values = more strict matching",
                    size=12,
                    color=ft.Colors.GREY_600
                )
            ]),
            
            ft.Container(height=20),
            
            # Action buttons
            ft.Row([
                self.search_button,
                self.clear_button
            ]),
            
            ft.Container(height=15),
            
            # Algorithm info
            ft.Container(
                content=ft.Column([
                    ft.Text("Algorithm Information:", weight=ft.FontWeight.BOLD, size=14),
                    ft.Text("• KMP: Good for single pattern matching", size=12),
                    ft.Text("• Boyer-Moore: Efficient for longer patterns", size=12),
                    ft.Text("• Aho-Corasick: Best for multiple patterns (Bonus)", size=12),
                ]),
                padding=15,
                bgcolor=ft.Colors.AMBER_50,
                border_radius=8
            )
        ])
    
    def perform_search(self, e):
        """Perform CV search"""
        # Get search parameters
        keywords_text = self.keywords_field.value
        if not keywords_text or not keywords_text.strip():
            self.show_error("Please enter search keywords")
            return
        
        # Parse keywords
        keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
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
