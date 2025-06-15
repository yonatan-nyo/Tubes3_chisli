import flet as ft
from typing import Callable, Dict, Any
from utils.type_safety import (
    safe_get_str,
    safe_get_list,
    safe_get_dict,
    safe_get_int,
    safe_get_float,
    is_dict,
    ensure_string,
    TypeSafetyError
)


class ResultsSection:
    """Search results section component with type safety"""

    def __init__(self, page: ft.Page, on_result_selected: Callable[[int], None]):
        self.page: ft.Page = page
        self.on_result_selected: Callable[[int], None] = on_result_selected

        # UI components
        self.results_container = ft.Column([
            ft.Container(
                content=ft.Text("No search results yet",
                                color=ft.Colors.GREY_600, size=14),
                alignment=ft.alignment.center,
                width=None,  # Take full width
                expand=True,
                padding=20
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True, width=None)

        self.results_info = ft.Text("", size=12, color=ft.Colors.GREY_600)

    def build(self) -> ft.Control:
        """Build results section UI with improved styling"""
        return ft.Column([
            # Modern header with icon
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.SEARCH_ROUNDED,
                            color=ft.Colors.BLUE_600, size=24),
                    ft.Text("Search Results", size=20,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                    ft.Container(expand=True),
                    self.results_info
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding(0, 0, 0, 10),
                expand=True
            ),
            ft.Container(
                content=self.results_container,
                height=400,
                width=None,
                expand=True,
                border=ft.border.all(1, ft.Colors.BLUE_200),
                border_radius=12,
                padding=15,
                bgcolor=ft.Colors.GREY_50,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_500),
                    offset=ft.Offset(0, 2)
                ),
            )], expand=True)  # Make the main column expand to full width

    def update_results(self, search_results: Dict[str, Any]):
        """Update results display with type safety"""
        try:
            if not is_dict(search_results):
                raise TypeSafetyError(
                    f"Expected dictionary, got {type(search_results)}")

            results = safe_get_list(search_results, 'results', [])

           # Update info text
            if results:
                algorithm = safe_get_str(
                    search_results, 'algorithm_used', 'Unknown')
                total_time = safe_get_float(search_results, 'total_time', 0.0)
                exact_time = safe_get_float(
                    search_results, 'exact_match_time', 0.0)
                fuzzy_time = safe_get_float(
                    search_results, 'fuzzy_match_time', 0.0)
                self.results_info.value = (
                    f"{len(results)} results • {algorithm} • "
                    f"Total: {total_time:.3f}s "
                    f"(Exact: {exact_time:.3f}s, Fuzzy: {fuzzy_time:.3f}s)"
                )
            else:
                self.results_info.value = "No results found"

            # Clear existing results
            self.results_container.controls.clear()

            if not results:
                self.results_container.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SEARCH_OFF, size=48,
                                    color=ft.Colors.GREY_400),
                            ft.Text("No matching CVs found", size=16,
                                    color=ft.Colors.GREY_600),                            ft.Text("Try different keywords or broaden your search criteria",
                                                                                                  size=12, color=ft.Colors.GREY_500)
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

        except Exception as e:
            print(f"Error updating results: {e}")
            self.results_info.value = "Error loading results"
            self.results_container.controls.clear()
            self.results_container.controls.append(
                ft.Text(f"Error: {str(e)}", color=ft.Colors.RED_600)
            )
            self.page.update()

    def _create_result_card(self, rank: int, result: Dict[str, Any]) -> ft.Control:
        """Create a result card for an applicant with type safety"""
        try:
            if not is_dict(result):
                raise TypeSafetyError(
                    f"Expected dictionary, got {type(result)}")

            applicant = safe_get_dict(result, 'applicant', {})
            exact_matches = safe_get_dict(result, 'exact_matches', {})
            fuzzy_matches = safe_get_dict(result, 'fuzzy_matches', {})
            # Create match indicators with improved styling
            total_score = safe_get_float(result, 'overall_score', 0.0)
            match_chips = []

            # Exact matches with green theme
            for keyword, count in exact_matches.items():
                match_chips.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE,
                                    color=ft.Colors.GREEN_700, size=14),
                            ft.Text(f"{keyword} ({count})", size=11,
                                    weight=ft.FontWeight.W_500)
                        ], spacing=4),
                        bgcolor=ft.Colors.GREEN_50,
                        border=ft.border.all(1, ft.Colors.GREEN_200),
                        border_radius=20,
                        padding=ft.Padding(8, 4, 8, 4),
                        height=28
                    )
                )

            # Fuzzy matches with orange theme
            for keyword, match_info in fuzzy_matches.items():
                similarity = safe_get_float(match_info, 'similarity', 0.0)
                matched_word = safe_get_str(match_info, 'matched_word', '')
                match_chips.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.TRENDING_UP,
                                    color=ft.Colors.ORANGE_700, size=14),
                            ft.Text(f"{keyword}→{matched_word} ({similarity:.1f})",
                                    size=11, weight=ft.FontWeight.W_500)
                        ], spacing=4),
                        bgcolor=ft.Colors.ORANGE_50,
                        border=ft.border.all(1, ft.Colors.ORANGE_200),
                        border_radius=20,
                        padding=ft.Padding(8, 4, 8, 4),
                        height=28
                    )
                )            # Create modern card content
            card_content = ft.Column([
                # Header with rank badge, name, and score
                ft.Row([
                    # Rank badge
                    ft.Container(
                        content=ft.Text(
                            f"{rank}", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.WHITE),
                        width=40,
                        height=40,
                        bgcolor=ft.Colors.BLUE_600,
                        border_radius=20,
                        alignment=ft.alignment.center,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=4,
                            color=ft.Colors.with_opacity(
                                0.3, ft.Colors.BLUE_600),
                            offset=ft.Offset(0, 2)
                        )
                    ),

                    # Name and role column
                    ft.Column([
                        ft.Text(
                            safe_get_str(applicant, 'name', 'Unknown'),
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_800,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        ft.Text(
                            safe_get_str(applicant, 'application_role',
                                         'No role specified'),
                            size=13,
                            color=ft.Colors.GREY_600,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS
                        )
                    ], spacing=2, expand=True),

                    # Score badge
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.STAR,
                                    color=ft.Colors.AMBER_600, size=16),
                            ft.Text(f"{total_score:.1f}", size=12,
                                    weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_700)
                        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=8,
                        bgcolor=ft.Colors.AMBER_50,
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.AMBER_200)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                # Match indicators with scrollable container
                ft.Container(
                    content=ft.Row(
                        match_chips[:6],  # Show up to 6 chips
                        wrap=True,
                        spacing=6,
                        run_spacing=4
                    ),
                    margin=ft.Margin(0, 12, 0, 0)
                ) if match_chips else ft.Container(),

                # Summary preview with better styling
                ft.Container(
                    content=ft.Text(
                        self._get_summary_preview(applicant),
                        size=12,
                        color=ft.Colors.GREY_700,
                        max_lines=3,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                    margin=ft.Margin(0, 8, 0, 0),
                    padding=ft.Padding(10, 8, 10, 8),
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=6,
                    border=ft.border.all(1, ft.Colors.GREY_200)
                )
            ], spacing=8)            # Create modern clickable card with enhanced hover effects
            return ft.Container(
                content=card_content,
                padding=16,
                margin=ft.Margin(0, 0, 0, 12),
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.BLUE_100),
                border_radius=12,
                ink=True,
                on_click=lambda e, aid=safe_get_int(
                    applicant, 'detail_id', 0): self.on_result_selected(aid),
                animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
                on_hover=self._on_card_hover,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=6,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.GREY_500),
                    offset=ft.Offset(0, 2)
                )
            )

        except Exception as e:
            print(f"Error creating result card: {e}")
            return ft.Container(
                content=ft.Text(
                    f"Error loading result: {str(e)}", color=ft.Colors.RED_600),
                padding=12,
                margin=ft.Margin(0, 0, 0, 8),
                bgcolor=ft.Colors.RED_50,                border_radius=8
            )

    def _on_card_hover(self, e):
        """Handle card hover effect with error handling"""
        try:
            if e.control and hasattr(e.control, 'page') and e.control.page:
                if e.data == "true":
                    e.control.bgcolor = ft.Colors.BLUE_50
                    e.control.border = ft.border.all(2, ft.Colors.BLUE_300)
                else:
                    e.control.bgcolor = ft.Colors.WHITE
                    e.control.border = ft.border.all(1, ft.Colors.GREY_300)
                e.control.update()
        except Exception as ex:
            print(f"Warning: Error in card hover effect: {ex}")
            # Ignore hover errors to prevent app crashes

    def _get_summary_preview(self, applicant: Dict[str, Any]) -> str:
        """Get a preview of the applicant's summary with type safety"""
        try:
            summary = safe_get_str(applicant, 'summary', '')
            if summary:
                return summary[:150] + "..." if len(summary) > 150 else summary

            # Fallback to skills or first few words of extracted text
            skills = safe_get_list(applicant, 'skills', [])
            if skills:
                skill_strs = [ensure_string(skill) for skill in skills[:3]]
                return f"Skills: {', '.join(skill_strs)}" + ("..." if len(skills) > 3 else "")

            extracted_text = safe_get_str(applicant, 'extracted_text', '')
            if extracted_text:
                words = extracted_text.split()[:20]
                return ' '.join(words) + "..." if len(words) == 20 else ' '.join(words)

            return "No summary available"
        except Exception as e:
            print(f"Error getting summary preview: {e}")
            return "Error loading summary"
