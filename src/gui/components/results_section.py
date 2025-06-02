import flet as ft
from typing import Callable, Dict

class ResultsSection:
    """Search results section component"""
    
    def __init__(self, page: ft.Page, on_result_selected: Callable):
        self.page = page
        self.on_result_selected = on_result_selected
        
        # UI components
        self.results_container = ft.Column([
            ft.Text("No search results yet", color=ft.Colors.GREY_600, size=14)
        ], scroll=ft.ScrollMode.AUTO)
        
        self.results_info = ft.Text("", size=12, color=ft.Colors.GREY_600)
    
    def build(self) -> ft.Control:
        """Build results section UI"""
        return ft.Column([
            ft.Row([
                ft.Text("Search Results", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.results_info
            ]),
            ft.Divider(height=10),
            
            ft.Container(
                content=self.results_container,
                height=350,  # Fixed height for better scrolling
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=8,
                padding=10
            )
        ])
    
    def update_results(self, search_results: Dict):
        """Update results display"""
        results = search_results.get('results', [])
        
        # Update info text
        if results:
            algorithm = search_results.get('algorithm_used', 'Unknown')
            total_time = search_results.get('total_time', 0)
            self.results_info.value = f"{len(results)} results • {algorithm} • {total_time:.3f}s"
        else:
            self.results_info.value = "No results found"
        
        # Clear existing results
        self.results_container.controls.clear()
        
        if not results:
            self.results_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=ft.Colors.GREY_400),
                        ft.Text("No matching CVs found", size=16, color=ft.Colors.GREY_600),
                        ft.Text("Try different keywords or lower the fuzzy threshold", size=12, color=ft.Colors.GREY_500)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40
                )
            )
        else:
            # Add result cards
            for i, result in enumerate(results, 1):
                self.results_container.controls.append(
                    self._create_result_card(i, result)
                )
        
        self.page.update()
    
    def _create_result_card(self, rank: int, result: Dict) -> ft.Control:
        """Create a result card for an applicant"""
        applicant = result['applicant']
        exact_matches = result.get('exact_matches', {})
        fuzzy_matches = result.get('fuzzy_matches', {})
        total_score = result.get('overall_score', 0)
        
        # Create match indicators
        match_chips = []
        
        # Exact matches
        for keyword, count in exact_matches.items():
            match_chips.append(
                ft.Chip(
                    label=ft.Text(f"{keyword} ({count})", size=10),
                    bgcolor=ft.Colors.GREEN_100,
                    color=ft.Colors.GREEN_800,
                    height=30
                )
            )
        
        # Fuzzy matches
        for keyword, match_info in fuzzy_matches.items():
            similarity = match_info.get('similarity', 0)
            matched_word = match_info.get('matched_word', '')
            match_chips.append(
                ft.Chip(
                    label=ft.Text(f"{keyword}→{matched_word} ({similarity:.2f})", size=10),
                    bgcolor=ft.Colors.ORANGE_100,
                    color=ft.Colors.ORANGE_800,
                    height=30
                )
            )
        
        # Create card content with better spacing
        card_content = ft.Column([
            # Header row with rank and name
            ft.Row([
                ft.Container(
                    content=ft.Text(f"#{rank}", weight=ft.FontWeight.BOLD, size=12),
                    width=35,
                    height=35,
                    bgcolor=ft.Colors.BLUE_100,
                    border_radius=17,
                    alignment=ft.alignment.center
                ),
                ft.Column([
                    ft.Text(
                        applicant.get('name', 'Unknown'),
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    ft.Text(
                        applicant.get('email', ''),
                        size=11,
                        color=ft.Colors.GREY_600,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS
                    )
                ], spacing=2, expand=True),
                ft.Text(
                    f"Score: {total_score:.1f}",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Match indicators with scrollable container
            ft.Container(
                content=ft.Row(
                    match_chips[:5],  # Limit to 5 chips to avoid overflow
                    wrap=True,
                    spacing=3
                ),
                height=30 if match_chips else 0,
                margin=ft.Margin(0, 5, 0, 0)
            ),
            
            # Summary preview
            ft.Container(
                content=ft.Text(
                    self._get_summary_preview(applicant),
                    size=11,
                    color=ft.Colors.GREY_700,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS
                ),
                margin=ft.Margin(0, 5, 0, 0)
            )
        ], spacing=5)
        
        # Create clickable card with hover effect
        return ft.Container(
            content=card_content,
            padding=12,
            margin=ft.Margin(0, 0, 0, 8),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            ink=True,
            on_click=lambda e, aid=applicant['id']: self.on_result_selected(aid),
            animate=ft.Animation(100, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=self._on_card_hover
        )
    
    def _on_card_hover(self, e):
        """Handle card hover effect"""
        if e.data == "true":
            e.control.bgcolor = ft.Colors.BLUE_50
            e.control.border = ft.border.all(2, ft.Colors.BLUE_300)
        else:
            e.control.bgcolor = ft.Colors.WHITE
            e.control.border = ft.border.all(1, ft.Colors.GREY_300)
        e.control.update()
    
    def _get_summary_preview(self, applicant: Dict) -> str:
        """Get a preview of the applicant's summary"""
        summary = applicant.get('summary', '')
        if summary:
            return summary[:150] + "..." if len(summary) > 150 else summary
        
        # Fallback to skills or first few words of extracted text
        skills = applicant.get('skills', [])
        if skills:
            return f"Skills: {', '.join(skills[:3])}" + ("..." if len(skills) > 3 else "")
        
        extracted_text = applicant.get('extracted_text', '')
        if extracted_text:
            words = extracted_text.split()[:20]
            return ' '.join(words) + "..." if len(words) == 20 else ' '.join(words)
        
        return "No summary available"
